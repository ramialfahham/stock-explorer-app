"""Fetch raw yfinance market data and write parquet snapshots."""

from __future__ import annotations

import os
import time
from datetime import date, datetime, timezone
from pathlib import Path

import pandas as pd
import yfinance as yf

from ingestion.constituents.seeds import load_constituents
from ingestion.paths import raw_dir
from ingestion.registry import Market
from ingestion.yfinance.balance_sheet import land_balance_sheet_fields
from ingestion.yfinance.quarterly import (
    OPERATING_EXPENSE_ROW,
    OPERATING_INCOME_FALLBACK_ROWS,
    OPERATING_REVENUE_ROW,
    land_quarterly_ttm_fields,
)
from ingestion.yfinance.rate_limit import call_with_retry, is_rate_limited
from ingestion.yfinance.symbols import to_yfinance_download_ticker, to_yfinance_ticker

LOOKBACK_DAYS = 30
BATCH_SIZE = 50

INFO_FIELDS = {
    "info_forward_pe": "forwardPE",
    "info_operating_margins": "operatingMargins",
    "info_revenue_growth": "revenueGrowth",
    "info_net_debt": "netDebt",
    "info_total_debt": "totalDebt",
    "info_total_cash": "totalCash",
    "info_ebitda": "ebitda",
    "info_return_on_equity": "returnOnEquity",
    "info_current_ratio": "currentRatio",
    "info_price_to_book": "priceToBook",
    "info_price_to_sales": "priceToSalesTrailing12Months",
    "info_ev_to_ebitda": "enterpriseToEbitda",
    "info_free_cashflow": "freeCashflow",
    "info_market_cap": "marketCap",
    "info_dividend_yield": "dividendYield",
    "info_payout_ratio": "payoutRatio",
    "info_sector": "sector",
    "info_currency": "currency",
    "info_long_name": "longName",
    "info_business_summary": "longBusinessSummary",
    "info_founded_year": "founded",
}

INCOME_ROW = "Total Revenue"
CASHFLOW_ROW = "Free Cash Flow"
OPERATING_CASH_FLOW_ROW = "Operating Cash Flow"
CAPITAL_EXPENDITURE_ROW = "Capital Expenditure"
INTEREST_EXPENSE_ROW = "Interest Expense"
NET_INCOME_ROW = "Net Income"
# Net income attributable to common shareholders (after minority interest + preferred
# dividends) — the correctly-attributed numerator for a common ROE against common equity.
NET_INCOME_COMMON_ROW = "Net Income Common Stockholders"


def _write_constituents_snapshot(market: Market, constituents: pd.DataFrame) -> None:
    output_dir = raw_dir(market.market_code)
    output_dir.mkdir(parents=True, exist_ok=True)

    snapshot = constituents.copy()
    snapshot["ingested_at"] = datetime.now(timezone.utc).isoformat()
    snapshot.to_parquet(output_dir / "yf_constituents.parquet", index=False)


def _checkpoint_marker_path(output_path: Path) -> Path:
    return output_path.with_name(f"{output_path.name}.checkpoint")


def _is_fresh_today(output_path: Path) -> bool:
    """True when `output_path` has a checkpoint marker last touched today (UTC) --
    the freshness boundary for skip-if-already-fetched. The marker's own mtime is the
    signal, not the parquet file's -- deliberately decoupled, since other scripts write
    these exact paths for unrelated reasons with no coordination with this checkpoint
    (`scripts/seed_ci_raw_fixtures.py` writes fake fixture rows into real market_codes for
    CI dbt builds; `scripts/backfill_fundamentals_parquet_schema.py` rewrites the schema
    across every market). Only `_atomic_write_parquet` ever touches the marker, so only a
    completed write from this module can ever satisfy the check -- a same-day write from
    one of those other scripts leaves no marker, so the next real ingestion run correctly
    treats the file as not-fresh and fully refetches, self-healing rather than trusting
    stale-looking-but-wrong content. (Narrower residual case, not fully closed: if one of
    those scripts overwrites the parquet file itself AFTER a real ingestion run already
    wrote both the file and the marker the same day, the marker still reads fresh even
    though the parquet content is no longer what ingestion wrote -- an unusual, deliberate
    action sequence, not a normal workflow; use `--force-refetch` if this is ever suspected.)
    """
    marker = _checkpoint_marker_path(output_path)
    if not output_path.exists() or not marker.exists():
        return False
    mtime = datetime.fromtimestamp(marker.stat().st_mtime, tz=timezone.utc)
    return mtime.date() == datetime.now(timezone.utc).date()


def _atomic_write_parquet(frame: pd.DataFrame, output_path: Path) -> None:
    """Write to a same-directory temp file, then `os.replace()` onto `output_path` --
    atomic on both POSIX and Windows. A direct `.to_parquet(output_path, ...)` left the
    checkpoint file itself exposed to a process kill mid-write: a truncated file's mtime
    still reads as today, so the next run would trust it as fresh, then crash trying to
    read it back, wedging every same-day retry until someone deletes it by hand. This way
    `output_path` always holds either the last complete write or the new one, never a
    partial one. Touches the checkpoint marker last, only after the parquet write is fully
    complete and visible -- if the process dies between the two, the marker is missing or
    stale and the next run just refetches, which is always safe, never corrupting."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = output_path.with_name(f"{output_path.name}.tmp-{os.getpid()}")
    frame.to_parquet(tmp_path, index=False)
    os.replace(tmp_path, output_path)
    _checkpoint_marker_path(output_path).write_text(
        datetime.now(timezone.utc).isoformat(), encoding="utf-8"
    )


def _normalize_price_frame(frame: pd.DataFrame, market_code: str) -> pd.DataFrame:
    renamed = frame.rename(
        columns={
            "Date": "trading_date",
            "Open": "open",
            "High": "high",
            "Low": "low",
            "Close": "close",
            "Volume": "volume",
            "Dividends": "dividends",
            "Stock Splits": "stock_splits",
        }
    )
    renamed["market_code"] = market_code
    renamed["trading_date"] = pd.to_datetime(renamed["trading_date"]).dt.date

    for optional in ("dividends", "stock_splits"):
        if optional not in renamed.columns:
            renamed[optional] = None

    return renamed[
        [
            "market_code",
            "ticker",
            "trading_date",
            "open",
            "high",
            "low",
            "close",
            "volume",
            "dividends",
            "stock_splits",
        ]
    ]


def _fetch_daily_prices(
    market: Market,
    local_tickers: list[str],
    *,
    max_tickers: int | None = None,
    force: bool = False,
) -> pd.DataFrame:
    tickers = local_tickers[:max_tickers] if max_tickers else local_tickers

    output_path = raw_dir(market.market_code) / "yf_daily_prices.parquet"
    existing: pd.DataFrame | None = None
    already_fetched: set[str] = set()
    if not force and _is_fresh_today(output_path):
        existing = pd.read_parquet(output_path)
        already_fetched = set(existing["ticker"].unique())

    # Filtered BEFORE batching, not skipped per-batch -- a batch that mixes already-fetched
    # and pending tickers must never redownload the already-fetched ones (that would append
    # a second row per (ticker, trading_date) alongside `existing`, corrupting the file). This
    # also means batch composition/boundaries can legitimately differ between two same-day
    # runs (e.g. a different --max-tickers), which is fine -- only pending tickers are ever
    # batched at all.
    pending_tickers = [t for t in tickers if t not in already_fetched]
    yf_tickers = [
        to_yfinance_download_ticker(t, market.exchange_suffix) for t in pending_tickers
    ]

    # Raw (pre-normalize) batches fetched THIS call -- kept separate from `existing`
    # (already normalized, loaded from a prior same-day write) so a flush never runs
    # `_normalize_price_frame` twice over the same rows.
    frames: list[pd.DataFrame] = []

    def _current_combined() -> pd.DataFrame:
        parts = [p for p in (existing,) if p is not None and not p.empty]
        if frames:
            parts.append(
                _normalize_price_frame(pd.concat(frames, ignore_index=True), market.market_code)
            )
        return pd.concat(parts, ignore_index=True) if parts else pd.DataFrame()

    def _flush() -> None:
        combined = _current_combined()
        if combined.empty:
            return
        _atomic_write_parquet(combined, output_path)

    for start in range(0, len(yf_tickers), BATCH_SIZE):
        batch = yf_tickers[start : start + BATCH_SIZE]
        batch_local = pending_tickers[start : start + BATCH_SIZE]

        def _download_batch() -> pd.DataFrame:
            return yf.download(
                batch,
                period=f"{LOOKBACK_DAYS}d",
                group_by="ticker",
                auto_adjust=False,
                threads=True,
                progress=False,
            )

        try:
            downloaded = call_with_retry(_download_batch)
        except Exception as exc:  # noqa: BLE001
            print(
                f"  warning: price batch failed for {market.market_code} "
                f"(tickers {start}-{start + len(batch)}): {exc}"
            )
            continue

        if downloaded.empty:
            continue

        if len(batch) == 1:
            single = downloaded.copy()
            single["ticker"] = batch_local[0]
            single = single.reset_index()
            frames.append(single)
        else:
            for local_ticker, yf_ticker in zip(batch_local, batch):
                if yf_ticker not in downloaded.columns.get_level_values(0):
                    continue
                part = downloaded[yf_ticker].copy()
                part["ticker"] = local_ticker
                part = part.reset_index()
                frames.append(part)

        _flush()

    return _current_combined()


def _latest_annual_statement_value(
    statement: pd.DataFrame | None,
    row_label: str,
) -> tuple[object | None, date | None, str | None]:
    if statement is None or statement.empty or row_label not in statement.index:
        return None, None, None

    row = statement.loc[row_label]
    numeric_cols = []
    for col in row.index:
        try:
            val = row[col]
            if val is not None and not (isinstance(val, float) and pd.isna(val)):
                numeric_cols.append(col)
        except (TypeError, ValueError):
            continue

    if not numeric_cols:
        return None, None, None

    latest_col = max(numeric_cols, key=lambda c: pd.Timestamp(c))
    value = row[latest_col]
    if isinstance(value, float) and pd.isna(value):
        value = None

    fiscal_end: date | None = None
    try:
        fiscal_end = pd.Timestamp(latest_col).date()
    except (TypeError, ValueError):
        fiscal_end = None

    currency = None
    if hasattr(statement, "attrs") and statement.attrs.get("currency"):
        currency = statement.attrs.get("currency")

    return value, fiscal_end, currency


def _fetch_fundamentals_row(
    market: Market,
    local_ticker: str,
    yf_symbol: str,
    snapshot_date: date,
) -> dict[str, object]:
    def _load() -> dict[str, object]:
        ticker = yf.Ticker(yf_symbol)
        info = ticker.info or {}

        row: dict[str, object] = {
            "market_code": market.market_code,
            "ticker": local_ticker,
            "snapshot_date": snapshot_date,
        }

        for col, key in INFO_FIELDS.items():
            row[col] = info.get(key)

        income = ticker.income_stmt
        if income is None or income.empty:
            income = ticker.financials

        cashflow = ticker.cashflow

        revenue, fiscal_end, income_currency = _latest_annual_statement_value(
            income, INCOME_ROW
        )
        fcf, _, cashflow_currency = _latest_annual_statement_value(
            cashflow, CASHFLOW_ROW
        )

        row["stmt_total_revenue"] = revenue
        row["stmt_free_cash_flow"] = fcf
        row["stmt_fiscal_period_end"] = fiscal_end
        row["stmt_currency"] = income_currency or cashflow_currency

        stmt_op = None
        for label in OPERATING_INCOME_FALLBACK_ROWS:
            stmt_op, _, _ = _latest_annual_statement_value(income, label)
            if stmt_op is not None:
                break
        row["stmt_operating_income"] = stmt_op
        stmt_op_rev, _, _ = _latest_annual_statement_value(income, OPERATING_REVENUE_ROW)
        stmt_op_exp, _, _ = _latest_annual_statement_value(income, OPERATING_EXPENSE_ROW)
        row["stmt_operating_revenue"] = stmt_op_rev
        row["stmt_operating_expense"] = stmt_op_exp

        ocf, _, _ = _latest_annual_statement_value(cashflow, OPERATING_CASH_FLOW_ROW)
        capex, _, _ = _latest_annual_statement_value(cashflow, CAPITAL_EXPENDITURE_ROW)
        interest_expense, _, _ = _latest_annual_statement_value(income, INTEREST_EXPENSE_ROW)
        net_income, _, _ = _latest_annual_statement_value(income, NET_INCOME_ROW)
        net_income_common, _, _ = _latest_annual_statement_value(
            income, NET_INCOME_COMMON_ROW
        )
        row["stmt_operating_cash_flow"] = ocf
        row["stmt_capital_expenditure"] = capex
        row["stmt_interest_expense"] = interest_expense
        row["stmt_net_income"] = net_income
        row["stmt_net_income_common"] = net_income_common

        row.update(land_quarterly_ttm_fields(ticker))
        row.update(land_balance_sheet_fields(ticker))
        return row

    return call_with_retry(_load)


def _fetch_fundamentals(
    market: Market,
    local_tickers: list[str],
    *,
    max_tickers: int | None = None,
    delay_seconds: float = 0.0,
    force: bool = False,
) -> tuple[pd.DataFrame, dict[str, int]]:
    tickers = local_tickers[:max_tickers] if max_tickers else local_tickers
    snapshot_date = datetime.now(timezone.utc).date()

    output_path = raw_dir(market.market_code) / "yf_fundamentals.parquet"
    already_fetched: set[str] = set()
    rows: list[dict[str, object]] = []
    if not force and _is_fresh_today(output_path):
        existing = pd.read_parquet(output_path)
        rows = existing.to_dict(orient="records")
        already_fetched = set(existing["ticker"].unique())

    stats = {"fundamentals_ok": 0, "fundamentals_failed": 0, "fundamentals_skipped": 0}

    def _flush() -> None:
        _atomic_write_parquet(pd.DataFrame(rows), output_path)

    for local_ticker in tickers:
        if local_ticker in already_fetched:
            stats["fundamentals_skipped"] += 1
            continue

        yf_symbol = to_yfinance_ticker(local_ticker, market.exchange_suffix)
        try:
            row = _fetch_fundamentals_row(market, local_ticker, yf_symbol, snapshot_date)
            rows.append(row)
            stats["fundamentals_ok"] += 1
            # Flushed immediately, not batched -- each row is already one network call,
            # so one small parquet write alongside it is negligible overhead, and it
            # bounds a crash's loss to the ticker in flight, not up to a batch's worth.
            _flush()
        except Exception as exc:  # noqa: BLE001
            stats["fundamentals_failed"] += 1
            label = "rate-limited" if is_rate_limited(exc) else "error"
            print(
                f"  warning: fundamentals {label} for "
                f"{market.market_code}/{local_ticker}: {exc}"
            )
        if delay_seconds > 0:
            time.sleep(delay_seconds)

    if not rows:
        return pd.DataFrame(), stats

    return pd.DataFrame(rows), stats


def ingest_market(
    market: Market,
    *,
    max_tickers: int | None = None,
    delay_seconds: float = 0.0,
    force: bool = False,
) -> dict[str, int]:
    constituents = load_constituents(market.market_code)
    _write_constituents_snapshot(market, constituents)

    local_tickers = constituents["ticker"].tolist()
    prices = _fetch_daily_prices(
        market, local_tickers, max_tickers=max_tickers, force=force
    )
    fundamentals, fund_stats = _fetch_fundamentals(
        market,
        local_tickers,
        max_tickers=max_tickers,
        delay_seconds=delay_seconds,
        force=force,
    )

    return {
        "constituents": len(constituents),
        "tickers_requested": len(local_tickers[:max_tickers] if max_tickers else local_tickers),
        "price_rows": len(prices),
        "fundamentals_rows": len(fundamentals),
        **fund_stats,
    }
