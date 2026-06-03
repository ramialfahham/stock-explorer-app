"""Fetch raw yfinance market data and write parquet snapshots."""

from __future__ import annotations

from datetime import date, datetime, timezone

import pandas as pd
import yfinance as yf

from ingestion.constituents.seeds import load_constituents
from ingestion.paths import raw_dir
from ingestion.registry import Market

LOOKBACK_DAYS = 30
BATCH_SIZE = 50

INFO_FIELDS = {
    "info_forward_pe": "forwardPE",
    "info_operating_margins": "operatingMargins",
    "info_revenue_growth": "revenueGrowth",
    "info_net_debt": "netDebt",
    "info_ebitda": "ebitda",
    "info_sector": "sector",
    "info_currency": "currency",
    "info_long_name": "longName",
}

INCOME_ROW_LABELS = ("Total Revenue",)
CASHFLOW_ROW_LABELS = ("Free Cash Flow",)


def _to_yfinance_ticker(local_ticker: str, exchange_suffix: str) -> str:
    # Some indices list full provider symbols (e.g. AIR.PA on DAX); do not double-suffix.
    if "." in local_ticker:
        return local_ticker
    return f"{local_ticker}{exchange_suffix}"


def _write_constituents_snapshot(market: Market, constituents: pd.DataFrame) -> None:
    output_dir = raw_dir(market.market_code)
    output_dir.mkdir(parents=True, exist_ok=True)

    snapshot = constituents.copy()
    snapshot["ingested_at"] = datetime.now(timezone.utc).isoformat()
    snapshot.to_parquet(output_dir / "yf_constituents.parquet", index=False)


def _fetch_daily_prices(
    market: Market,
    local_tickers: list[str],
    *,
    max_tickers: int | None = None,
) -> pd.DataFrame:
    tickers = local_tickers[:max_tickers] if max_tickers else local_tickers
    yf_tickers = [_to_yfinance_ticker(t, market.exchange_suffix) for t in tickers]

    frames: list[pd.DataFrame] = []
    for start in range(0, len(yf_tickers), BATCH_SIZE):
        batch = yf_tickers[start : start + BATCH_SIZE]
        batch_local = tickers[start : start + BATCH_SIZE]
        downloaded = yf.download(
            batch,
            period=f"{LOOKBACK_DAYS}d",
            group_by="ticker",
            auto_adjust=False,
            threads=True,
            progress=False,
        )

        if downloaded.empty:
            continue

        if len(batch) == 1:
            single = downloaded.copy()
            single["ticker"] = batch_local[0]
            single = single.reset_index()
            frames.append(single)
            continue

        for local_ticker, yf_ticker in zip(batch_local, batch):
            if yf_ticker not in downloaded.columns.get_level_values(0):
                continue
            part = downloaded[yf_ticker].copy()
            part["ticker"] = local_ticker
            part = part.reset_index()
            frames.append(part)

    if not frames:
        return pd.DataFrame()

    combined = pd.concat(frames, ignore_index=True)
    combined = combined.rename(
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
    combined["market_code"] = market.market_code
    combined["trading_date"] = pd.to_datetime(combined["trading_date"]).dt.date

    for optional in ("dividends", "stock_splits"):
        if optional not in combined.columns:
            combined[optional] = None

    return combined[
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
        income, "Total Revenue"
    )
    fcf, _, cashflow_currency = _latest_annual_statement_value(cashflow, "Free Cash Flow")

    row["stmt_total_revenue"] = revenue
    row["stmt_free_cash_flow"] = fcf
    row["stmt_fiscal_period_end"] = fiscal_end
    row["stmt_currency"] = income_currency or cashflow_currency

    return row


def _fetch_fundamentals(
    market: Market,
    local_tickers: list[str],
    *,
    max_tickers: int | None = None,
) -> pd.DataFrame:
    tickers = local_tickers[:max_tickers] if max_tickers else local_tickers
    snapshot_date = datetime.now(timezone.utc).date()
    rows: list[dict[str, object]] = []

    for local_ticker in tickers:
        yf_symbol = _to_yfinance_ticker(local_ticker, market.exchange_suffix)
        try:
            rows.append(
                _fetch_fundamentals_row(market, local_ticker, yf_symbol, snapshot_date)
            )
        except Exception as exc:  # noqa: BLE001 — log and continue per ticker
            print(
                f"  warning: fundamentals failed for {market.market_code}/{local_ticker}: {exc}"
            )

    if not rows:
        return pd.DataFrame()

    return pd.DataFrame(rows)


def ingest_market(market: Market, *, max_tickers: int | None = None) -> dict[str, int]:
    constituents = load_constituents(market.market_code)
    _write_constituents_snapshot(market, constituents)

    local_tickers = constituents["ticker"].tolist()
    prices = _fetch_daily_prices(market, local_tickers, max_tickers=max_tickers)
    fundamentals = _fetch_fundamentals(market, local_tickers, max_tickers=max_tickers)

    output_dir = raw_dir(market.market_code)
    output_dir.mkdir(parents=True, exist_ok=True)
    prices.to_parquet(output_dir / "yf_daily_prices.parquet", index=False)
    fundamentals.to_parquet(output_dir / "yf_fundamentals.parquet", index=False)

    return {
        "constituents": len(constituents),
        "tickers_requested": len(local_tickers[:max_tickers] if max_tickers else local_tickers),
        "price_rows": len(prices),
        "fundamentals_rows": len(fundamentals),
    }
