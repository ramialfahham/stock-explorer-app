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


def test_fundamentals_failures_are_named_not_only_counted(monkeypatch, tmp_path):
    """A count says how many cards are stale; only the names say which. The names are what
    main() prints, so they must come out of the real fetch loop, not be inferred later."""
    _use_tmp_raw_dir(monkeypatch, tmp_path)

    def _fake_fetch_row(market, local_ticker, yf_symbol, snapshot_date):
        if local_ticker in ("BBB", "DDD"):
            raise RuntimeError("yfinance said no")
        return _fake_row(local_ticker)

    monkeypatch.setattr(ingest_module, "_fetch_fundamentals_row", _fake_fetch_row)

    frame, stats = ingest_module._fetch_fundamentals(
        MARKET, ["AAA", "BBB", "CCC", "DDD"], delay_seconds=0
    )

    assert stats["fundamentals_failed"] == 2
    assert stats["fundamentals_failed_tickers"] == ["BBB", "DDD"]
    assert sorted(frame["ticker"]) == ["AAA", "CCC"]


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
        _, _ = ingest_module._fetch_daily_prices(MARKET, ["AAA", "BBB", "CCC", "DDD"])

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
    _, _ = ingest_module._fetch_daily_prices(MARKET, ["AAA", "BBB", "CCC", "DDD"])
    assert sorted(calls) == ["AAA", "BBB", "CCC", "DDD"]

    calls.clear()

    def _fake_download_second_call(tickers, **kwargs):
        if set(tickers) & {"AAA", "BBB", "CCC", "DDD"}:
            raise AssertionError(f"{tickers} should have been skipped, already fresh today")
        calls.extend(tickers)
        return _fake_price_frame(tickers)

    monkeypatch.setattr(ingest_module.yf, "download", _fake_download_second_call)
    combined, _ = ingest_module._fetch_daily_prices(
        MARKET, ["AAA", "BBB", "CCC", "DDD", "EEE", "FFF"]
    )
    assert calls == ["EEE", "FFF"]
    assert sorted(combined["ticker"].unique()) == ["AAA", "BBB", "CCC", "DDD", "EEE", "FFF"]


def test_prices_no_duplicate_rows_when_batch_boundaries_shift(monkeypatch, tmp_path):
    """Regression: a batch that mixes already-fetched and pending tickers must never
    redownload the already-fetched ones -- filtering happens before batching, not per
    batch, so this can't produce a second row per (ticker, trading_date)."""
    _use_tmp_raw_dir(monkeypatch, tmp_path)
    monkeypatch.setattr(ingest_module, "BATCH_SIZE", 3)

    monkeypatch.setattr(ingest_module.yf, "download", lambda tickers, **kwargs: _fake_price_frame(tickers))
    _, _ = ingest_module._fetch_daily_prices(MARKET, ["AAA", "BBB"])

    calls: list[str] = []

    def _fake_download(tickers, **kwargs):
        calls.extend(tickers)
        return _fake_price_frame(tickers)

    # BATCH_SIZE=3 puts AAA/BBB (already fetched) in the same window as CCC (new) --
    # the exact partially-covered-batch scenario the fix targets.
    monkeypatch.setattr(ingest_module.yf, "download", _fake_download)
    combined, _ = ingest_module._fetch_daily_prices(MARKET, ["AAA", "BBB", "CCC", "DDD", "EEE"])

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
    _, _ = ingest_module._fetch_daily_prices(MARKET, ["AAA", "BBB"])

    _backdate_checkpoint(output_dir / "yf_daily_prices.parquet")

    calls: list[str] = []

    def _fake_download(tickers, **kwargs):
        calls.extend(tickers)
        return _fake_price_frame(tickers)

    monkeypatch.setattr(ingest_module.yf, "download", _fake_download)
    _, _ = ingest_module._fetch_daily_prices(MARKET, ["AAA", "BBB"])
    assert sorted(calls) == ["AAA", "BBB"]


def test_prices_ignores_a_fresh_today_file_with_an_old_schema(monkeypatch, tmp_path):
    """Regression: a fresh-today checkpoint can still predate a schema change (this task
    added `ingested_at` to prices) -- merging it with newly-fetched rows would silently
    NaN-fill the old rows' missing column instead of erroring. Must be treated the same as
    not-fresh: a full refetch, not a partial merge into a mismatched-schema file."""
    output_dir = _use_tmp_raw_dir(monkeypatch, tmp_path)
    output_path = output_dir / "yf_daily_prices.parquet"
    output_path.parent.mkdir(parents=True)

    old_schema_columns = [c for c in ingest_module.PRICE_COLUMNS if c != "ingested_at"]
    old_schema_row = {c: "ZZZ" if c == "ticker" else 1.0 for c in old_schema_columns}
    old_schema_row["market_code"] = MARKET.market_code
    old_schema_row["trading_date"] = pd.Timestamp("2026-01-01").date()
    pd.DataFrame([old_schema_row]).to_parquet(output_path, index=False)
    # Marker content is never read back, only its own mtime -- writing it now makes it
    # fresh-today, simulating a checkpoint that predates today's schema (the parquet has no
    # ingested_at column) but still passes the freshness check on its marker alone.
    ingest_module._checkpoint_marker_path(output_path).write_text("today", encoding="utf-8")

    calls: list[str] = []

    def _fake_download(tickers, **kwargs):
        calls.extend(tickers)
        return _fake_price_frame(tickers)

    monkeypatch.setattr(ingest_module, "BATCH_SIZE", 2)
    monkeypatch.setattr(ingest_module.yf, "download", _fake_download)
    combined, _ = ingest_module._fetch_daily_prices(MARKET, ["AAA", "BBB"])

    assert sorted(calls) == ["AAA", "BBB"]
    assert "ZZZ" not in combined["ticker"].values
    assert combined["ingested_at"].notna().all()


def test_prices_ingested_at_is_not_overwritten_by_a_later_batchs_flush(monkeypatch, tmp_path):
    """Regression: `ingested_at` is stamped once per fetch batch on the raw row data, not
    inside `_normalize_price_frame` -- which reruns on every flush over ALL of `frames`
    accumulated so far, not just the newest batch. If a future refactor moved the stamp
    into `_normalize_price_frame` instead (a natural-looking place for it), the second
    batch's flush would silently overwrite the first batch's already-flushed `ingested_at`
    values with the later flush's own timestamp. Nothing else would catch this: dbt build
    (schema/types unaffected), dbt source freshness (values would look fresher, not
    staler), and no other test here inspects ingested_at across batch boundaries."""
    _use_tmp_raw_dir(monkeypatch, tmp_path)
    monkeypatch.setattr(ingest_module, "BATCH_SIZE", 2)
    monkeypatch.setattr(
        ingest_module.yf, "download", lambda tickers, **kwargs: _fake_price_frame(tickers)
    )

    base = datetime(2026, 9, 1, 12, 0, 0, tzinfo=timezone.utc)
    call_count = {"n": 0}

    class _FakeDatetime:
        @staticmethod
        def now(tz=None):
            # Monotonically increasing, not a fixed count -- _atomic_write_parquet's
            # own marker write also calls datetime.now() once per flush, so the real
            # call count per batch is >1 and shouldn't be hardcoded here.
            call_count["n"] += 1
            return base + timedelta(minutes=call_count["n"])

    monkeypatch.setattr(ingest_module, "datetime", _FakeDatetime)

    combined, _ = ingest_module._fetch_daily_prices(MARKET, ["AAA", "BBB", "CCC", "DDD"])

    stamps = combined.set_index("ticker")["ingested_at"]
    assert stamps["AAA"] == stamps["BBB"], "same batch must share one fetch_time"
    assert stamps["CCC"] == stamps["DDD"], "same batch must share one fetch_time"
    assert stamps["AAA"] < stamps["CCC"], (
        "batch 1's stamp must predate batch 2's -- if the batch-2 flush had overwritten "
        "it, the two would be equal instead"
    )


def test_prices_force_bypasses_skip(monkeypatch, tmp_path):
    _use_tmp_raw_dir(monkeypatch, tmp_path)
    monkeypatch.setattr(ingest_module, "BATCH_SIZE", 2)

    monkeypatch.setattr(ingest_module.yf, "download", lambda tickers, **kwargs: _fake_price_frame(tickers))
    _, _ = ingest_module._fetch_daily_prices(MARKET, ["AAA", "BBB"])

    calls: list[str] = []

    def _fake_download(tickers, **kwargs):
        calls.extend(tickers)
        return _fake_price_frame(tickers)

    monkeypatch.setattr(ingest_module.yf, "download", _fake_download)
    _, _ = ingest_module._fetch_daily_prices(MARKET, ["AAA", "BBB"], force=True)
    assert sorted(calls) == ["AAA", "BBB"]


def test_price_batch_failure_is_counted_not_swallowed(monkeypatch, tmp_path):
    """Issue #9 A3. A failed batch used to print a warning and `continue`, returning only a
    frame, so no caller could tell a complete fetch from a partial one. The parquet is still
    written and still carries a fresh timestamp, so `dbt source freshness` cannot see the loss
    and no `check_*` script looks at prices at all."""
    output_dir = _use_tmp_raw_dir(monkeypatch, tmp_path)
    monkeypatch.setattr(ingest_module, "BATCH_SIZE", 2)

    def _fake_download(tickers, **kwargs):
        if "CCC" in tickers:
            raise RuntimeError("yfinance said no")
        return _fake_price_frame(tickers)

    monkeypatch.setattr(ingest_module.yf, "download", _fake_download)
    monkeypatch.setattr(ingest_module, "call_with_retry", lambda fn: fn())

    combined, stats = ingest_module._fetch_daily_prices(MARKET, ["AAA", "BBB", "CCC", "DDD"])

    assert stats["price_batches"] == 2
    assert stats["price_batches_failed"] == 1

    # The partial write still happens, on purpose: it is the resume checkpoint. What changes is
    # that the caller can now tell it is partial.
    assert sorted(combined["ticker"].unique()) == ["AAA", "BBB"]
    assert (output_dir / "yf_daily_prices.parquet").exists()


def test_empty_and_missing_are_counted_from_the_real_fetch(monkeypatch, tmp_path):
    """The empty-batch and missing-ticker paths are the two the stderr warning does not fire
    on, so nothing else would notice their counters regressing. Exercised against the real
    _fetch_daily_prices, not a faked summary."""
    _use_tmp_raw_dir(monkeypatch, tmp_path)
    monkeypatch.setattr(ingest_module, "BATCH_SIZE", 2)

    def _fake_download(tickers, **kwargs):
        if "CCC" in tickers:
            return pd.DataFrame()
        # Return AAA only, so BBB is absent from the response columns.
        return _fake_price_frame([tickers[0]])

    monkeypatch.setattr(ingest_module.yf, "download", _fake_download)
    monkeypatch.setattr(ingest_module, "call_with_retry", lambda fn: fn())

    _, stats = ingest_module._fetch_daily_prices(MARKET, ["AAA", "BBB", "CCC", "DDD"])

    assert stats["price_batches_empty"] == 1
    assert stats["price_tickers_missing"] == 1
    assert stats["price_batches_failed"] == 0


def test_price_stats_reach_the_market_summary(monkeypatch, tmp_path):
    """The counts are useless unless they leave `_fetch_daily_prices`. `ingest_market` is what
    `ingestion/main.py` reads, and its fundamentals counts already arrive this way."""
    _use_tmp_raw_dir(monkeypatch, tmp_path)
    monkeypatch.setattr(ingest_module, "BATCH_SIZE", 2)
    monkeypatch.setattr(
        ingest_module,
        "load_constituents",
        lambda market_code: pd.DataFrame({"ticker": ["AAA", "BBB", "CCC", "DDD"]}),
    )
    monkeypatch.setattr(ingest_module, "_write_constituents_snapshot", lambda market, frame: None)
    monkeypatch.setattr(
        ingest_module,
        "_fetch_fundamentals_row",
        lambda market, local_ticker, yf_symbol, snapshot_date: _fake_row(local_ticker),
    )

    def _fake_download(tickers, **kwargs):
        if "CCC" in tickers:
            raise RuntimeError("yfinance said no")
        return _fake_price_frame(tickers)

    monkeypatch.setattr(ingest_module.yf, "download", _fake_download)
    monkeypatch.setattr(ingest_module, "call_with_retry", lambda fn: fn())

    summary = ingest_module.ingest_market(MARKET, delay_seconds=0)

    assert summary["price_batches_failed"] == 1
    assert summary["price_batches"] == 2

    # Pin the whole key set, not just the two this test reads. `ingestion/main.py` indexes every
    # one of these by name, so renaming a counter here alone would pass every test and then
    # raise KeyError on the real run, after the ~24-minute ingest has already happened.
    assert set(summary) == {
        "constituents",
        "tickers_requested",
        "price_rows",
        "price_batches",
        "price_batches_failed",
        "price_batches_empty",
        "price_tickers_missing",
        "fundamentals_rows",
        "fundamentals_ok",
        "fundamentals_failed",
        "fundamentals_skipped",
        "fundamentals_failed_tickers",
    }
