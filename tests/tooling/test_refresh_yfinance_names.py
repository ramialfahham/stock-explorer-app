"""Tests for the yfinance name snapshot refresh (issue #34)."""

from __future__ import annotations

import csv
from pathlib import Path

import pytest

import refresh_yfinance_names

_EXISTING = (
    "market_code,ticker,yfinance_long_name,refreshed_at\n"
    "ch_smi,NESN,Nestlé S.A.,2026-09-17T10:00:00+00:00\n"
    "ch_smi,ROG,Roche Holding AG,2026-09-17T10:00:00+00:00\n"
    "it_ftsemib,ENI,Eni S.p.A.,2026-09-17T10:00:00+00:00\n"
    'us_sp500,BRK.B,"Berkshire Hathaway, Inc.",2026-09-17T10:00:00+00:00\n'
    "xx_retired,OLD,Retired Market Co,2026-09-17T10:00:00+00:00\n"
)


def _fake_refresh(market_codes: list[str], *, delay_seconds: float) -> list[dict[str, str]]:
    return [
        {
            "market_code": code,
            "ticker": "NEW",
            "yfinance_long_name": f"Fresh {code}",
            "refreshed_at": "2026-10-06T00:00:00+00:00",
        }
        for code in market_codes
    ]


@pytest.fixture
def snapshot(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    path = tmp_path / "yfinance_name_snapshot.csv"
    path.write_text(_EXISTING, encoding="utf-8", newline="")
    monkeypatch.setattr(refresh_yfinance_names, "NAME_SNAPSHOT_PATH", path)
    monkeypatch.setattr(refresh_yfinance_names, "refresh_snapshot", _fake_refresh)
    return path


def _lines_for(path: Path, market_code: str) -> list[str]:
    return [
        line
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.startswith(f"{market_code},")
    ]


def _markets(path: Path) -> set[str]:
    with open(path, encoding="utf-8", newline="") as f:
        return {r["market_code"] for r in csv.DictReader(f)}


def test_market_refresh_leaves_other_markets_rows_unchanged(snapshot: Path) -> None:
    before = {m: _lines_for(snapshot, m) for m in ("it_ftsemib", "us_sp500", "xx_retired")}

    assert refresh_yfinance_names.main(["--market", "ch_smi"]) == 0

    for market_code, lines in before.items():
        assert _lines_for(snapshot, market_code) == lines
    assert _lines_for(snapshot, "ch_smi") == [
        "ch_smi,NEW,Fresh ch_smi,2026-10-06T00:00:00+00:00"
    ]


def test_full_refresh_rewrites_the_whole_snapshot(snapshot: Path) -> None:
    assert refresh_yfinance_names.main([]) == 0

    with open(snapshot, encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))
    assert {r["ticker"] for r in rows} == {"NEW"}
    assert "ch_smi" in _markets(snapshot)
    assert "xx_retired" not in _markets(snapshot)


@pytest.fixture
def live_refresh(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    """The real refresh_snapshot with the network, the registry and the constituents faked."""
    import pandas as pd

    from ingestion.registry import Market

    path = tmp_path / "yfinance_name_snapshot.csv"
    path.write_text(_EXISTING, encoding="utf-8", newline="")
    monkeypatch.setattr(refresh_yfinance_names, "NAME_SNAPSHOT_PATH", path)
    market = Market(market_code="ch_smi", index_name="^SSMI", exchange_suffix=".SW", source="yfinance", ingest_active=True)
    monkeypatch.setattr(refresh_yfinance_names, "load_markets", lambda *a, **k: [market])
    monkeypatch.setattr(
        refresh_yfinance_names, "load_constituents", lambda code: pd.DataFrame({"ticker": ["NESN", "ROG", "NEWCO"]})
    )
    monkeypatch.setattr(refresh_yfinance_names.time, "sleep", lambda seconds: None)

    def run(fetch) -> list[dict[str, str]]:
        monkeypatch.setattr(refresh_yfinance_names, "_fetch_long_name", fetch)
        return refresh_yfinance_names.refresh_snapshot(["ch_smi"], delay_seconds=0)

    return run


@pytest.mark.parametrize("nameless", ["", None])
def test_a_failed_or_nameless_ticker_keeps_its_previous_row_and_the_counts_are_printed(
    live_refresh, capsys, nameless
) -> None:
    def fetch(symbol: str):
        if symbol == "NESN.SW":
            raise RuntimeError("429")
        return nameless

    rows = live_refresh(fetch)

    by_ticker = {r["ticker"]: r for r in rows}
    assert sorted(by_ticker) == ["NESN", "ROG"]
    assert by_ticker["NESN"]["yfinance_long_name"] == "Nestlé S.A."
    assert by_ticker["NESN"]["refreshed_at"] == "2026-09-17T10:00:00+00:00"
    assert by_ticker["ROG"]["yfinance_long_name"] == "Roche Holding AG"
    captured = capsys.readouterr()
    assert "ch_smi: refreshed 0 names, failed 1, no name 2, kept previous 2" in captured.out
    assert "NESN.SW" in captured.err


def test_a_fresh_name_replaces_the_previous_row(live_refresh) -> None:
    rows = live_refresh(lambda symbol: f"Fresh {symbol}")

    by_ticker = {r["ticker"]: r for r in rows}
    assert by_ticker["NESN"]["yfinance_long_name"] == "Fresh NESN.SW"
    assert by_ticker["NESN"]["refreshed_at"] != "2026-09-17T10:00:00+00:00"
    assert sorted(by_ticker) == ["NESN", "NEWCO", "ROG"]


def test_a_write_that_fails_keeps_the_previous_snapshot(snapshot: Path) -> None:
    before = snapshot.read_text(encoding="utf-8")
    bad_row = {"market_code": "ch_smi", "ticker": "X", "yfinance_long_name": "X", "refreshed_at": "t", "unexpected": "field"}

    with pytest.raises(ValueError):
        refresh_yfinance_names.write_snapshot([bad_row])

    assert snapshot.read_text(encoding="utf-8") == before
    assert list(snapshot.parent.iterdir()) == [snapshot]
