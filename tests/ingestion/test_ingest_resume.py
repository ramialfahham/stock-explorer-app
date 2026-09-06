"""Checkpoint/resume behavior for the ingestion loop: skip-if-fresh-today, incremental
flush, and the `force` escape hatch. No real network -- `_fetch_fundamentals_row` and
`yf.download` are faked."""

from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone

import pandas as pd
import pytest

import ingestion.yfinance.ingest as ingest_module
from ingestion.registry import Market

MARKET = Market(
    market_code="test_market",
    index_name="^TEST",
    exchange_suffix="",
    source="yfinance",
    ingest_active=True,
)


def _use_tmp_raw_dir(monkeypatch, tmp_path):
    raw_root = tmp_path / "raw"
    monkeypatch.setattr(ingest_module, "raw_dir", lambda market_code: raw_root / market_code)
    return raw_root / MARKET.market_code


def _backdate_checkpoint(output_path) -> None:
    """Freshness is keyed on the checkpoint marker's mtime, not the parquet file's own --
    backdate the marker to simulate a stale (yesterday's) checkpoint."""
    marker = ingest_module._checkpoint_marker_path(output_path)
    yesterday = (datetime.now(timezone.utc) - timedelta(days=1)).timestamp()
    os.utime(marker, (yesterday, yesterday))


def _fake_row(ticker: str) -> dict:
    return {"market_code": MARKET.market_code, "ticker": ticker, "snapshot_date": "2026-09-06"}


# ---------------------------------------------------------------------------
# _atomic_write_parquet
# ---------------------------------------------------------------------------


def test_atomic_write_leaves_no_temp_file_behind(tmp_path):
    output_path = tmp_path / "some_market" / "yf_fundamentals.parquet"
    ingest_module._atomic_write_parquet(pd.DataFrame({"ticker": ["AAA"]}), output_path)

    assert output_path.exists()
    marker = ingest_module._checkpoint_marker_path(output_path)
    assert marker.exists()
    leftovers = [p for p in output_path.parent.iterdir() if p not in (output_path, marker)]
    assert leftovers == []
    assert pd.read_parquet(output_path)["ticker"].tolist() == ["AAA"]


# ---------------------------------------------------------------------------
# _fetch_fundamentals
# ---------------------------------------------------------------------------


def test_fundamentals_flush_survives_a_simulated_crash(monkeypatch, tmp_path):
    output_dir = _use_tmp_raw_dir(monkeypatch, tmp_path)

    def _fake_fetch_row(market, local_ticker, yf_symbol, snapshot_date):
        if local_ticker == "CCC":
            raise KeyboardInterrupt
        return _fake_row(local_ticker)

    monkeypatch.setattr(ingest_module, "_fetch_fundamentals_row", _fake_fetch_row)

    with pytest.raises(KeyboardInterrupt):
        ingest_module._fetch_fundamentals(MARKET, ["AAA", "BBB", "CCC", "DDD"], delay_seconds=0)

    on_disk = pd.read_parquet(output_dir / "yf_fundamentals.parquet")
    assert sorted(on_disk["ticker"]) == ["AAA", "BBB"]


def test_fundamentals_skip_if_fresh_today(monkeypatch, tmp_path):
    _use_tmp_raw_dir(monkeypatch, tmp_path)
    calls: list[str] = []

    def _fake_fetch_row(market, local_ticker, yf_symbol, snapshot_date):
        calls.append(local_ticker)
        return _fake_row(local_ticker)

    monkeypatch.setattr(ingest_module, "_fetch_fundamentals_row", _fake_fetch_row)
    _, stats = ingest_module._fetch_fundamentals(MARKET, ["AAA", "BBB", "CCC"], delay_seconds=0)
    assert stats["fundamentals_ok"] == 3
    assert calls == ["AAA", "BBB", "CCC"]

    calls.clear()

    def _fake_fetch_row_second_call(market, local_ticker, yf_symbol, snapshot_date):
        if local_ticker in {"AAA", "BBB", "CCC"}:
            raise AssertionError(f"{local_ticker} should have been skipped, already fresh today")
        calls.append(local_ticker)
        return _fake_row(local_ticker)

    monkeypatch.setattr(ingest_module, "_fetch_fundamentals_row", _fake_fetch_row_second_call)
    frame, stats = ingest_module._fetch_fundamentals(
        MARKET, ["AAA", "BBB", "CCC", "DDD"], delay_seconds=0
    )
    assert stats["fundamentals_skipped"] == 3
    assert calls == ["DDD"]
    assert sorted(frame["ticker"]) == ["AAA", "BBB", "CCC", "DDD"]


def test_fundamentals_stale_file_is_fully_refetched(monkeypatch, tmp_path):
    output_dir = _use_tmp_raw_dir(monkeypatch, tmp_path)

    monkeypatch.setattr(
        ingest_module,
        "_fetch_fundamentals_row",
        lambda market, local_ticker, yf_symbol, snapshot_date: _fake_row(local_ticker),
    )
    ingest_module._fetch_fundamentals(MARKET, ["AAA", "BBB"], delay_seconds=0)

    _backdate_checkpoint(output_dir / "yf_fundamentals.parquet")

    calls: list[str] = []

    def _fake_fetch_row(market, local_ticker, yf_symbol, snapshot_date):
        calls.append(local_ticker)
        return _fake_row(local_ticker)

    monkeypatch.setattr(ingest_module, "_fetch_fundamentals_row", _fake_fetch_row)
    _, stats = ingest_module._fetch_fundamentals(MARKET, ["AAA", "BBB"], delay_seconds=0)
    assert stats["fundamentals_skipped"] == 0
    assert calls == ["AAA", "BBB"]


def test_fundamentals_ignores_a_same_day_write_from_another_script(monkeypatch, tmp_path):
    """Regression: scripts/seed_ci_raw_fixtures.py and
    scripts/backfill_fundamentals_parquet_schema.py write these exact raw parquet paths for
    unrelated reasons, with no checkpoint marker. A same-day write from one of them must not
    be mistaken for a completed ingestion run -- the marker, not the parquet file's own
    mtime, is the freshness signal, so ingestion should still fully (re)fetch."""
    output_dir = _use_tmp_raw_dir(monkeypatch, tmp_path)
    output_path = output_dir / "yf_fundamentals.parquet"
    output_path.parent.mkdir(parents=True)
    pd.DataFrame([_fake_row("ZZZ")]).to_parquet(output_path, index=False)  # no marker written

    calls: list[str] = []

    def _fake_fetch_row(market, local_ticker, yf_symbol, snapshot_date):
        calls.append(local_ticker)
        return _fake_row(local_ticker)

    monkeypatch.setattr(ingest_module, "_fetch_fundamentals_row", _fake_fetch_row)
    frame, stats = ingest_module._fetch_fundamentals(MARKET, ["AAA", "BBB"], delay_seconds=0)
    assert stats["fundamentals_skipped"] == 0
    assert calls == ["AAA", "BBB"]
    assert sorted(frame["ticker"]) == ["AAA", "BBB"]


def test_fundamentals_force_bypasses_skip(monkeypatch, tmp_path):
    _use_tmp_raw_dir(monkeypatch, tmp_path)

    monkeypatch.setattr(
        ingest_module,
        "_fetch_fundamentals_row",
        lambda market, local_ticker, yf_symbol, snapshot_date: _fake_row(local_ticker),
    )
    ingest_module._fetch_fundamentals(MARKET, ["AAA", "BBB"], delay_seconds=0)

    calls: list[str] = []

    def _fake_fetch_row(market, local_ticker, yf_symbol, snapshot_date):
        calls.append(local_ticker)
        return _fake_row(local_ticker)

    monkeypatch.setattr(ingest_module, "_fetch_fundamentals_row", _fake_fetch_row)
    _, stats = ingest_module._fetch_fundamentals(
        MARKET, ["AAA", "BBB"], delay_seconds=0, force=True
    )
    assert stats["fundamentals_skipped"] == 0
    assert calls == ["AAA", "BBB"]


# ---------------------------------------------------------------------------
# _fetch_daily_prices
# ---------------------------------------------------------------------------


def _fake_price_frame(tickers: list[str]) -> pd.DataFrame:
    idx = pd.to_datetime(["2026-09-01"])
    idx.name = "Date"
    fields = ["Open", "High", "Low", "Close", "Volume"]
    data = {(t, f): [1.0] for t in tickers for f in fields}
    return pd.DataFrame(data, index=idx)


def test_prices_flush_survives_a_simulated_crash(monkeypatch, tmp_path):
    output_dir = _use_tmp_raw_dir(monkeypatch, tmp_path)
    monkeypatch.setattr(ingest_module, "BATCH_SIZE", 2)

    def _fake_download(tickers, **kwargs):
        if "CCC" in tickers:
            raise KeyboardInterrupt
        return _fake_price_frame(tickers)

    monkeypatch.setattr(ingest_module.yf, "download", _fake_download)

    with pytest.raises(KeyboardInterrupt):
        ingest_module._fetch_daily_prices(MARKET, ["AAA", "BBB", "CCC", "DDD"])

    on_disk = pd.read_parquet(output_dir / "yf_daily_prices.parquet")
    assert sorted(on_disk["ticker"].unique()) == ["AAA", "BBB"]


def test_prices_skip_if_fresh_today(monkeypatch, tmp_path):
    _use_tmp_raw_dir(monkeypatch, tmp_path)
    monkeypatch.setattr(ingest_module, "BATCH_SIZE", 2)
    calls: list[str] = []

    def _fake_download(tickers, **kwargs):
        calls.extend(tickers)
        return _fake_price_frame(tickers)

    monkeypatch.setattr(ingest_module.yf, "download", _fake_download)
    ingest_module._fetch_daily_prices(MARKET, ["AAA", "BBB", "CCC", "DDD"])
    assert sorted(calls) == ["AAA", "BBB", "CCC", "DDD"]

    calls.clear()

    def _fake_download_second_call(tickers, **kwargs):
        if set(tickers) & {"AAA", "BBB", "CCC", "DDD"}:
            raise AssertionError(f"{tickers} should have been skipped, already fresh today")
        calls.extend(tickers)
        return _fake_price_frame(tickers)

    monkeypatch.setattr(ingest_module.yf, "download", _fake_download_second_call)
    combined = ingest_module._fetch_daily_prices(MARKET, ["AAA", "BBB", "CCC", "DDD", "EEE", "FFF"])
    assert calls == ["EEE", "FFF"]
    assert sorted(combined["ticker"].unique()) == ["AAA", "BBB", "CCC", "DDD", "EEE", "FFF"]


def test_prices_no_duplicate_rows_when_batch_boundaries_shift(monkeypatch, tmp_path):
    """Regression: a batch that mixes already-fetched and pending tickers must never
    redownload the already-fetched ones -- filtering happens before batching, not per
    batch, so this can't produce a second row per (ticker, trading_date)."""
    _use_tmp_raw_dir(monkeypatch, tmp_path)
    monkeypatch.setattr(ingest_module, "BATCH_SIZE", 3)

    monkeypatch.setattr(ingest_module.yf, "download", lambda tickers, **kwargs: _fake_price_frame(tickers))
    ingest_module._fetch_daily_prices(MARKET, ["AAA", "BBB"])

    calls: list[str] = []

    def _fake_download(tickers, **kwargs):
        calls.extend(tickers)
        return _fake_price_frame(tickers)

    # BATCH_SIZE=3 puts AAA/BBB (already fetched) in the same window as CCC (new) --
    # the exact partially-covered-batch scenario the fix targets.
    monkeypatch.setattr(ingest_module.yf, "download", _fake_download)
    combined = ingest_module._fetch_daily_prices(MARKET, ["AAA", "BBB", "CCC", "DDD", "EEE"])

    assert "AAA" not in calls
    assert "BBB" not in calls
    assert sorted(set(calls)) == ["CCC", "DDD", "EEE"]
    assert combined["ticker"].value_counts().to_dict() == {
        t: 1 for t in ["AAA", "BBB", "CCC", "DDD", "EEE"]
    }


def test_prices_stale_file_is_fully_refetched(monkeypatch, tmp_path):
    output_dir = _use_tmp_raw_dir(monkeypatch, tmp_path)
    monkeypatch.setattr(ingest_module, "BATCH_SIZE", 2)

    monkeypatch.setattr(ingest_module.yf, "download", lambda tickers, **kwargs: _fake_price_frame(tickers))
    ingest_module._fetch_daily_prices(MARKET, ["AAA", "BBB"])

    _backdate_checkpoint(output_dir / "yf_daily_prices.parquet")

    calls: list[str] = []

    def _fake_download(tickers, **kwargs):
        calls.extend(tickers)
        return _fake_price_frame(tickers)

    monkeypatch.setattr(ingest_module.yf, "download", _fake_download)
    ingest_module._fetch_daily_prices(MARKET, ["AAA", "BBB"])
    assert sorted(calls) == ["AAA", "BBB"]


def test_prices_force_bypasses_skip(monkeypatch, tmp_path):
    _use_tmp_raw_dir(monkeypatch, tmp_path)
    monkeypatch.setattr(ingest_module, "BATCH_SIZE", 2)

    monkeypatch.setattr(ingest_module.yf, "download", lambda tickers, **kwargs: _fake_price_frame(tickers))
    ingest_module._fetch_daily_prices(MARKET, ["AAA", "BBB"])

    calls: list[str] = []

    def _fake_download(tickers, **kwargs):
        calls.extend(tickers)
        return _fake_price_frame(tickers)

    monkeypatch.setattr(ingest_module.yf, "download", _fake_download)
    ingest_module._fetch_daily_prices(MARKET, ["AAA", "BBB"], force=True)
    assert sorted(calls) == ["AAA", "BBB"]
