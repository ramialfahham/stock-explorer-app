"""Orchestrate raw ingestion for all active markets."""

from __future__ import annotations

import argparse
import sys
import time

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
    parser.add_argument(
        "--delay-seconds",
        type=float,
        default=0.25,
        help="Pause between fundamental ticker requests (default 0.25; use 0 for smoke tests)",
    )
    parser.add_argument(
        "--force-refetch",
        action="store_true",
        help="Ignore any same-day raw parquet already on disk and refetch every ticker",
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

    start = time.monotonic()
    markets_with_failed_prices: list[str] = []
    for market in markets:
        if market.source != "yfinance":
            print(f"Skipping {market.market_code}: unsupported source {market.source}")
            continue

        print(f"Ingesting {market.market_code}...")
        stats = ingest_market(
            market,
            max_tickers=args.max_tickers,
            delay_seconds=args.delay_seconds,
            force=args.force_refetch,
        )
        print(
            f"  constituents={stats['constituents']} "
            f"tickers_requested={stats['tickers_requested']} "
            f"price_rows={stats['price_rows']} "
            f"price_batches={stats['price_batches']} "
            f"price_batches_failed={stats['price_batches_failed']} "
            f"price_batches_empty={stats['price_batches_empty']} "
            f"price_tickers_missing={stats['price_tickers_missing']} "
            f"fundamentals_rows={stats['fundamentals_rows']} "
            f"fundamentals_ok={stats['fundamentals_ok']} "
            f"fundamentals_failed={stats['fundamentals_failed']} "
            f"fundamentals_skipped={stats['fundamentals_skipped']}"
        )
        if stats["price_batches_failed"]:
            markets_with_failed_prices.append(market.market_code)
        # Observability only -- not a gate. Ingestion is ~37% of the scheduled job's
        # total runtime (measured: ~24 of ~65 min against a 2h timeout), so stopping
        # early here would not meaningfully protect the job's actual timeout risk; this
        # just makes the trend visible in CI job logs across runs as more markets are
        # added, which today nobody tracks.
        elapsed_minutes = (time.monotonic() - start) / 60
        print(f"  elapsed so far: {elapsed_minutes:.1f}m")

    # Reported, not a gate, and deliberately so. Nothing downstream reads prices today:
    # stg_yf__daily_prices is defined and never selected from, and no price column reaches the
    # mart, the export or a card. Aborting here would cost the cycle's dbt build, Supabase
    # export and assessment refresh over data nobody consumes. call_with_retry also retries
    # rate limits ONLY, so an ordinary connection error arrives here unretried and would fire
    # this on noise. Owner-decided (issue #9, finding A3): report loudly, do not fail.
    # If a price column ever gains a consumer, revisit -- that is what makes this safe.
    if markets_with_failed_prices:
        print(
            "run_ingestion: price batches failed for "
            f"{', '.join(markets_with_failed_prices)}. Rows those markets DID retrieve were "
            "written with a fresh timestamp, so `dbt source freshness` cannot see the gap. A "
            "market whose every batch failed kept its previous file, untouched. Nothing "
            "downstream reads prices, so the run continues.",
            file=sys.stderr,
        )

    return 0


if __name__ == "__main__":
    sys.exit(main())
