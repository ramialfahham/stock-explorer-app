"""The recorder's `--ticker` mode must re-record only the named tickers and keep every other
recording: a regression there would silently mix fresh and old data into the golden mart."""

from __future__ import annotations

import json

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
    monkeypatch.setattr(recorder, "_record_prices", lambda batch: _prices(batch[0], 9.0))
    return out


def test_rerecord_replaces_only_the_named_ticker(market) -> None:
    entry = recorder.rerecord_tickers("us_sp500", ["KO"])
    assert json.loads((market / "KO.json").read_text(encoding="utf-8"))["v"] == "new"
    assert json.loads((market / "AAPL.json").read_text(encoding="utf-8"))["v"] == "old"
    prices = pd.read_parquet(market / "prices.parquet")
    assert prices.groupby("symbol")["Close"].first().to_dict() == {"AAPL": 1.0, "KO": 9.0}
    assert entry["info_symbols"] == {"AAPL": "AAPL", "KO": "KO"}
    assert entry["download_batch"] == ["AAPL", "KO"]


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


def test_main_ticker_mode_updates_the_manifest(market, tmp_path) -> None:
    (tmp_path / "manifest.json").write_text(
        json.dumps({"markets": {"us_sp500": {"tickers": ["AAPL", "OLD"], "recorded_at": "x"}}}),
        encoding="utf-8",
    )
    assert recorder.main(["--ticker", "us_sp500:KO"]) == 0
    entry = json.loads((tmp_path / "manifest.json").read_text(encoding="utf-8"))["markets"]["us_sp500"]
    assert entry["tickers"] == ["AAPL", "KO"]
    assert entry["recorded_at"] == "x"


@pytest.mark.parametrize("argv", [
    ["--ticker", "us_sp500:KO", "--market", "us_sp500"],
    ["--ticker", "us_sp500"],
    ["--ticker", "us_sp500:"],
])
def test_main_rejects_ambiguous_ticker_arguments(argv) -> None:
    with pytest.raises(SystemExit) as exc:
        recorder.main(argv)
    assert exc.value.code == 2
