"""Write minimal raw parquet fixtures for CI dbt builds (no network)."""

from __future__ import annotations

from datetime import date, datetime, timezone
from pathlib import Path

import pandas as pd
import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
REGISTRY_PATH = REPO_ROOT / "docs" / "market_registry.yml"
SNAPSHOT = date.today()
TICKERS = [f"CI{i:02d}" for i in range(1, 6)]


def _load_active_markets() -> list[str]:
    data = yaml.safe_load(REGISTRY_PATH.read_text(encoding="utf-8"))
    return sorted(
        m["market_code"]
        for m in data["markets"]
        if m.get("ingest_active")
    )


def _write_market_fixtures(market_code: str) -> None:
    out = REPO_ROOT / "storage" / "raw" / market_code
    out.mkdir(parents=True, exist_ok=True)
    now = datetime.now(timezone.utc).isoformat()

    constituents = pd.DataFrame(
        [
            {
                "market_code": market_code,
                "ticker": ticker,
                "company_name": f"CI Fixture {ticker}",
                "refreshed_at": now,
                "source": "ci_fixture",
                "ingested_at": now,
            }
            for ticker in TICKERS
        ]
    )
    constituents.to_parquet(out / "yf_constituents.parquet", index=False)

    prices = pd.DataFrame(
        [
            {
                "market_code": market_code,
                "ticker": ticker,
                "trading_date": SNAPSHOT,
                "open": 100.0,
                "high": 101.0,
                "low": 99.0,
                "close": 100.5,
                "volume": 1_000_000,
                "dividends": 0.0,
                "stock_splits": 0.0,
            }
            for ticker in TICKERS
        ]
    )
    prices.to_parquet(out / "yf_daily_prices.parquet", index=False)

    fundamentals = pd.DataFrame(
        [
            {
                "market_code": market_code,
                "ticker": ticker,
                "snapshot_date": SNAPSHOT,
                "info_forward_pe": 20.0 + i,
                "info_operating_margins": 0.25,
                "info_revenue_growth": 0.08,
                "info_net_debt": 10_000_000_000.0,
                "info_ebitda": 20_000_000_000.0,
                "info_sector": "Technology",
                "info_currency": "USD",
                "info_long_name": f"CI Fixture {ticker}",
                "stmt_total_revenue": 50_000_000_000.0,
                "stmt_free_cash_flow": 5_000_000_000.0,
                "stmt_fiscal_period_end": SNAPSHOT,
                "stmt_currency": "USD",
            }
            for i, ticker in enumerate(TICKERS, start=1)
        ]
    )
    fundamentals.to_parquet(out / "yf_fundamentals.parquet", index=False)


def main() -> int:
    markets = _load_active_markets()
    for market_code in markets:
        _write_market_fixtures(market_code)
        print(f"seed_ci_raw_fixtures: wrote fixtures for {market_code}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
