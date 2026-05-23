"""Fetch raw yfinance market data and write parquet snapshots."""

from __future__ import annotations

from datetime import datetime, timezone

import pandas as pd
import yfinance as yf

from ingestion.constituents.seeds import load_constituents
from ingestion.paths import raw_dir
from ingestion.registry import Market

LOOKBACK_DAYS = 30
BATCH_SIZE = 50


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


def ingest_market(market: Market, *, max_tickers: int | None = None) -> dict[str, int]:
    constituents = load_constituents(market.market_code)
    _write_constituents_snapshot(market, constituents)

    local_tickers = constituents["ticker"].tolist()
    prices = _fetch_daily_prices(market, local_tickers, max_tickers=max_tickers)

    output_dir = raw_dir(market.market_code)
    output_dir.mkdir(parents=True, exist_ok=True)
    prices.to_parquet(output_dir / "yf_daily_prices.parquet", index=False)

    return {
        "constituents": len(constituents),
        "tickers_requested": len(local_tickers[:max_tickers] if max_tickers else local_tickers),
        "price_rows": len(prices),
    }
