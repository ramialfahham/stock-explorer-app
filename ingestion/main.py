"""Orchestrate raw ingestion for all active markets."""

from __future__ import annotations

import argparse
import sys

from ingestion.registry import load_markets
from ingestion.yfinance.ingest import ingest_market


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Ingest raw yfinance data to storage/raw/")
    parser.add_argument(
        "--market",
        action="append",
        dest="markets",
        help="Limit to one or more market_code values (default: all ingest_active markets)",
    )
    parser.add_argument(
        "--max-tickers",
        type=int,
        default=None,
        help="Limit tickers per market (useful for local dev runs)",
    )
    args = parser.parse_args(argv)

    markets = load_markets(active_only=True)
    if args.markets:
        selected = set(args.markets)
        markets = [m for m in markets if m.market_code in selected]
        missing = selected - {m.market_code for m in markets}
        if missing:
            print(f"Unknown or inactive markets: {sorted(missing)}", file=sys.stderr)
            return 1

    if not markets:
        print("No active markets to ingest.", file=sys.stderr)
        return 1

    for market in markets:
        if market.source != "yfinance":
            print(f"Skipping {market.market_code}: unsupported source {market.source}")
            continue

        print(f"Ingesting {market.market_code}...")
        stats = ingest_market(market, max_tickers=args.max_tickers)
        print(
            f"  constituents={stats['constituents']} "
            f"tickers_requested={stats['tickers_requested']} "
            f"price_rows={stats['price_rows']}"
        )

    return 0


if __name__ == "__main__":
    sys.exit(main())
