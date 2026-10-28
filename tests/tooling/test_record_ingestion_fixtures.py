"""The recorder's `--ticker` mode must re-record only the named tickers and keep every other
recording, and a full recording must not touch a market's files before that market's network calls
have finished: a regression there would silently mix fresh and old data into the golden mart."""

from __future__ import annotations

import gzip
import json
from types import SimpleNamespace

import pandas as pd
import pytest

import record_ingestion_fixtures as recorder


def _prices(symbol: str, close: float) -> pd.DataFrame:
    return pd.DataFrame({
        "symbol": symbol,
        "Date": pd.to_datetime(["2026-10-01", "2026-10-02"]),
        "Close": [close, close],
    })


@pytest.fixture
def market(tmp_path, monkeypatch):
    monkeypatch.setattr(recorder, "FIXTURE_DIR", tmp_path)
    monkeypatch.setattr(recorder, "FIXTURE_TICKERS", {"us_sp500": ["AAPL", "KO"]})
    out = tmp_path / "yfinance" / "us_sp500"
    out.mkdir(parents=True)
    for name in ("AAPL", "KO", "OLD"):
        (out / f"{name}.json").write_text(json.dumps({"symbol": name, "v": "old"}), encoding="utf-8")
    pd.concat([_prices("AAPL", 1.0), _prices("KO", 2.0)]).to_parquet(out / "prices.parquet", index=False)
    monkeypatch.setattr(recorder, "_record_ticker", lambda symbol: {"symbol": symbol, "v": "new"})
    monkeypatch.setattr(
        recorder, "_record_prices", lambda batch: pd.concat([_prices(s, 9.0) for s in batch])
    )
    return out


def test_rerecord_replaces_only_the_named_ticker(market) -> None:
    entry = recorder.rerecord_tickers("us_sp500", ["KO"])
    assert json.loads((market / "KO.json").read_text(encoding="utf-8"))["v"] == "new"
    assert json.loads((market / "AAPL.json").read_text(encoding="utf-8"))["v"] == "old"
    prices = pd.read_parquet(market / "prices.parquet")
    assert prices.groupby("symbol")["Close"].first().to_dict() == {"AAPL": 1.0, "KO": 9.0}
    assert entry["info_symbols"] == {"AAPL": "AAPL", "KO": "KO"}
    assert entry["download_batch"] == ["AAPL", "KO"]


def test_rerecord_replaces_two_named_tickers_in_one_market(market) -> None:
    recorder.rerecord_tickers("us_sp500", ["AAPL", "KO"])
    for name in ("AAPL", "KO"):
        assert json.loads((market / f"{name}.json").read_text(encoding="utf-8"))["v"] == "new"
    prices = pd.read_parquet(market / "prices.parquet")
    assert prices.groupby("symbol")["Close"].first().to_dict() == {"AAPL": 9.0, "KO": 9.0}
    assert len(prices) == 4


def test_rerecord_removes_json_for_symbols_no_longer_listed(market) -> None:
    recorder.rerecord_tickers("us_sp500", ["KO"])
    assert sorted(p.stem for p in market.glob("*.json")) == ["AAPL", "KO"]


def test_rerecord_touches_nothing_when_the_network_fails(market, monkeypatch) -> None:
    def _offline(_batch):
        raise ConnectionError("no network")

    monkeypatch.setattr(recorder, "_record_prices", _offline)
    before = {p.name: p.read_bytes() for p in market.iterdir()}
    with pytest.raises(ConnectionError):
        recorder.rerecord_tickers("us_sp500", ["KO"])
    assert {p.name: p.read_bytes() for p in market.iterdir()} == before


def test_rerecord_refuses_a_ticker_not_in_the_fixture_list(market) -> None:
    with pytest.raises(SystemExit, match="not in FIXTURE_TICKERS"):
        recorder.rerecord_tickers("us_sp500", ["BRK.B"])


def test_record_prices_handles_a_single_symbol_frame_without_multiindex(monkeypatch) -> None:
    flat = pd.DataFrame(
        {"Open": [1.0], "Close": [2.0]}, index=pd.DatetimeIndex(["2026-10-01"], name="Date")
    )
    monkeypatch.setattr(recorder.yf, "download", lambda *a, **k: flat)
    frame = recorder._record_prices(["BT-A.L"])
    assert frame["symbol"].tolist() == ["BT-A.L"]
    assert frame["Close"].tolist() == [2.0]


def _utc_today() -> str:
    return recorder.datetime.now(recorder.timezone.utc).date().isoformat()


def test_main_ticker_mode_updates_the_manifest(market, tmp_path) -> None:
    (tmp_path / "manifest.json").write_text(
        json.dumps({"markets": {"us_sp500": {"tickers": ["AAPL", "OLD"], "recorded_at": "x"}}}),
        encoding="utf-8",
    )
    before = _utc_today()
    assert recorder.main(["--ticker", "us_sp500:KO"]) == 0
    entry = json.loads((tmp_path / "manifest.json").read_text(encoding="utf-8"))["markets"]["us_sp500"]
    assert entry["tickers"] == ["AAPL", "KO"]
    assert entry["recorded_at"] == "x"
    assert list(entry["rerecorded_at"]) == ["KO"]
    assert entry["rerecorded_at"]["KO"] in {before, _utc_today()}


def test_main_ticker_mode_keeps_earlier_dates_and_drops_unlisted_tickers(market, tmp_path) -> None:
    (tmp_path / "manifest.json").write_text(
        json.dumps({"markets": {"us_sp500": {
            "tickers": ["AAPL", "KO"],
            "recorded_at": "x",
            "rerecorded_at": {"AAPL": "2026-01-01", "OLD": "2026-01-01"},
        }}}),
        encoding="utf-8",
    )
    assert recorder.main(["--ticker", "us_sp500:KO"]) == 0
    manifest = json.loads((tmp_path / "manifest.json").read_text(encoding="utf-8"))
    entry = manifest["markets"]["us_sp500"]
    assert set(entry["rerecorded_at"]) == {"AAPL", "KO"}
    assert entry["rerecorded_at"]["AAPL"] == "2026-01-01"


def test_main_ticker_mode_saves_each_market_before_the_next(market, tmp_path, monkeypatch) -> None:
    (tmp_path / "manifest.json").write_text(
        json.dumps({"markets": {
            "us_sp500": {"tickers": ["AAPL", "OLD"], "recorded_at": "x"},
            "uk_ftse100": {"tickers": ["BT-A"], "recorded_at": "x"},
        }}),
        encoding="utf-8",
    )
    rerecord = recorder.rerecord_tickers

    def _fail_on_uk(code, tickers):
        if code == "uk_ftse100":
            raise ConnectionError("no network")
        return rerecord(code, tickers)

    monkeypatch.setattr(recorder, "rerecord_tickers", _fail_on_uk)
    with pytest.raises(ConnectionError):
        recorder.main(["--ticker", "us_sp500:KO", "--ticker", "uk_ftse100:BT-A"])
    markets = json.loads((tmp_path / "manifest.json").read_text(encoding="utf-8"))["markets"]
    assert markets["us_sp500"]["tickers"] == ["AAPL", "KO"]
    assert "KO" in markets["us_sp500"]["rerecorded_at"]


@pytest.mark.parametrize("argv", [
    ["--ticker", "us_sp500:KO", "--market", "us_sp500"],
    ["--ticker", "us_sp500"],
    ["--ticker", "us_sp500:"],
])
def test_main_rejects_ambiguous_ticker_arguments(argv) -> None:
    with pytest.raises(SystemExit) as exc:
        recorder.main(argv)
    assert exc.value.code == 2


def test_full_recording_clears_rerecorded_at(tmp_path, monkeypatch) -> None:
    active = [m.market_code for m in recorder.load_markets(active_only=True)]
    monkeypatch.setattr(recorder, "FIXTURE_DIR", tmp_path)
    monkeypatch.setattr(recorder, "FIXTURE_TICKERS", {code: [] for code in active})
    monkeypatch.setattr(recorder, "load_refresh_configs", lambda: {})
    monkeypatch.setattr(recorder, "record_market", lambda code: {"tickers": ["KO"]})
    (tmp_path / "manifest.json").write_text(
        json.dumps({"markets": {"us_sp500": {
            "tickers": ["KO"], "recorded_at": "x", "rerecorded_at": {"KO": "2026-01-01"},
        }}}),
        encoding="utf-8",
    )
    assert recorder.main(["--market", "us_sp500"]) == 0
    manifest = json.loads((tmp_path / "manifest.json").read_text(encoding="utf-8"))
    entry = manifest["markets"]["us_sp500"]
    assert "rerecorded_at" not in entry
    assert entry["recorded_at"] != "x"


def test_full_recording_touches_nothing_when_a_later_ticker_fails(market, monkeypatch) -> None:
    def _offline_on_ko(symbol):
        if symbol == "KO":
            raise ConnectionError("no network")
        return {"symbol": symbol, "v": "new"}

    monkeypatch.setattr(recorder, "_record_ticker", _offline_on_ko)
    before = {p.name: p.read_bytes() for p in market.iterdir()}
    with pytest.raises(ConnectionError):
        recorder.record_market("us_sp500")
    assert {p.name: p.read_bytes() for p in market.iterdir()} == before


def test_full_recording_touches_nothing_when_the_price_download_fails(market, monkeypatch) -> None:
    def _offline(_batch):
        raise ConnectionError("no network")

    monkeypatch.setattr(recorder, "_record_prices", _offline)
    before = {p.name: p.read_bytes() for p in market.iterdir()}
    with pytest.raises(ConnectionError):
        recorder.record_market("us_sp500")
    assert {p.name: p.read_bytes() for p in market.iterdir()} == before


def test_full_recording_writes_every_ticker_and_the_price_batch(market) -> None:
    entry = recorder.record_market("us_sp500")
    for name in ("AAPL", "KO"):
        assert json.loads((market / f"{name}.json").read_text(encoding="utf-8"))["v"] == "new"
    prices = pd.read_parquet(market / "prices.parquet")
    assert prices.groupby("symbol")["Close"].first().to_dict() == {"AAPL": 9.0, "KO": 9.0}
    assert entry["download_batch"] == ["AAPL", "KO"]


def test_main_full_mode_saves_each_market_before_the_next(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(recorder, "FIXTURE_DIR", tmp_path)
    active = [m.market_code for m in recorder.load_markets(active_only=True)]
    monkeypatch.setattr(recorder, "FIXTURE_TICKERS", {code: [] for code in active})
    monkeypatch.setattr(recorder, "load_refresh_configs", lambda: {})

    def _fail_on_uk(code):
        if code == "uk_ftse100":
            raise ConnectionError("no network")
        return {"tickers": ["KO"]}

    monkeypatch.setattr(recorder, "record_market", _fail_on_uk)
    with pytest.raises(ConnectionError):
        recorder.main(["--market", "us_sp500", "--market", "uk_ftse100"])
    markets = json.loads((tmp_path / "manifest.json").read_text(encoding="utf-8"))["markets"]
    assert list(markets) == ["us_sp500"]
    assert markets["us_sp500"]["recorded_at"] == _utc_today()


def test_main_full_mode_fetches_the_wikipedia_page_before_recording_the_market(
    tmp_path, monkeypatch
) -> None:
    monkeypatch.setattr(recorder, "FIXTURE_DIR", tmp_path)
    active = [m.market_code for m in recorder.load_markets(active_only=True)]
    monkeypatch.setattr(recorder, "FIXTURE_TICKERS", {code: [] for code in active})
    wiki = SimpleNamespace(provider="wikipedia", url="https://example.invalid/page")
    monkeypatch.setattr(recorder, "load_refresh_configs", lambda: {"us_sp500": wiki})
    recorded = []
    monkeypatch.setattr(recorder, "record_market", lambda code: recorded.append(code) or {})

    def _offline(_url):
        raise ConnectionError("no network")

    monkeypatch.setattr(recorder, "fetch_wikipedia", _offline)
    with pytest.raises(ConnectionError):
        recorder.main(["--market", "us_sp500"])
    assert recorded == []
    assert list(tmp_path.iterdir()) == []


def test_main_full_mode_writes_the_wikipedia_page_and_flags_the_manifest(
    tmp_path, monkeypatch
) -> None:
    monkeypatch.setattr(recorder, "FIXTURE_DIR", tmp_path)
    active = [m.market_code for m in recorder.load_markets(active_only=True)]
    monkeypatch.setattr(recorder, "FIXTURE_TICKERS", {code: [] for code in active})
    wiki = SimpleNamespace(provider="wikipedia", url="https://example.invalid/page")
    monkeypatch.setattr(recorder, "load_refresh_configs", lambda: {"us_sp500": wiki})
    monkeypatch.setattr(recorder, "record_market", lambda code: {"tickers": []})
    monkeypatch.setattr(recorder, "fetch_wikipedia", lambda url: "<html>page</html>")

    assert recorder.main(["--market", "us_sp500"]) == 0
    with gzip.open(tmp_path / "wikipedia" / "us_sp500.html.gz", "rt", encoding="utf-8") as handle:
        assert handle.read() == "<html>page</html>"
    manifest = json.loads((tmp_path / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["markets"]["us_sp500"]["wikipedia"] is True
