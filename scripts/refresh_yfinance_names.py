"""Refresh the cached yfinance company-name snapshot check_company_names_vs_yfinance.py
compares seed names against (issue #19).

Manual, human-run, exactly like scripts/refresh_constituents.py -- not a CI job. This repo
has no mechanism for CI to commit back to the repo, and building one is its own
new-mechanism decision (a CI push credential), declined in favor of this simpler,
already-precedented pattern: run occasionally, commit the result.

Fetches only `info.longName` per ticker (not the full fundamentals payload
`ingestion.yfinance.ingest._fetch_fundamentals_row` pulls for a real ingestion run) --
this is a name-only snapshot, far lighter than a real fetch.
"""

from __future__ import annotations

import argparse
import csv
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import yfinance as yf

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ingestion.constituents.refresh import load_refresh_configs
from ingestion.constituents.seeds import load_constituents
from ingestion.paths import NAME_SNAPSHOT_PATH
from ingestion.registry import load_markets
from ingestion.yfinance.rate_limit import call_with_retry
from ingestion.yfinance.symbols import to_yfinance_ticker


def _fetch_long_name(yf_symbol: str) -> str | None:
    def _load() -> str | None:
        info = yf.Ticker(yf_symbol).info or {}
        return info.get("longName")

    return call_with_retry(_load)


def refresh_snapshot(
    market_codes: list[str], *, delay_seconds: float = 0.25
) -> list[dict[str, str]]:
    markets_by_code = {m.market_code: m for m in load_markets()}
    rows: list[dict[str, str]] = []
    now = datetime.now(timezone.utc).isoformat()

    for market_code in market_codes:
        market = markets_by_code.get(market_code)
        if market is None:
            print(f"{market_code}: not in market registry, skipped", file=sys.stderr)
            continue
        frame = load_constituents(market_code)
        for _, row in frame.iterrows():
            ticker = str(row["ticker"])
            symbol = to_yfinance_ticker(ticker, market.exchange_suffix)
            try:
                long_name = _fetch_long_name(symbol)
            except Exception as exc:  # noqa: BLE001
                print(f"{market_code}:{ticker} ({symbol}): failed: {exc}", file=sys.stderr)
                long_name = None
            if long_name:
                rows.append(
                    {
                        "market_code": market_code,
                        "ticker": ticker,
                        "yfinance_long_name": long_name,
                        "refreshed_at": now,
                    }
                )
            time.sleep(delay_seconds)
        print(f"{market_code}: refreshed {sum(1 for r in rows if r['market_code'] == market_code)} names")

    return rows


def write_snapshot(rows: list[dict[str, str]]) -> Path:
    NAME_SNAPSHOT_PATH.parent.mkdir(parents=True, exist_ok=True)
    rows_sorted = sorted(rows, key=lambda r: (r["market_code"], r["ticker"]))
    with open(NAME_SNAPSHOT_PATH, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(
            f, fieldnames=["market_code", "ticker", "yfinance_long_name", "refreshed_at"]
        )
        writer.writeheader()
        writer.writerows(rows_sorted)
    return NAME_SNAPSHOT_PATH


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Refresh ingestion/constituents/yfinance_name_snapshot.csv from live "
            "yfinance data, for provider:wikipedia markets"
        )
    )
    parser.add_argument(
        "--market",
        action="append",
        dest="markets",
        help="Limit to one or more market_code values (default: all provider:wikipedia active markets)",
    )
    parser.add_argument(
        "--delay-seconds",
        type=float,
        default=0.25,
        help="Pause between tickers, to reduce Yahoo 429 rate limits (default: 0.25)",
    )
    args = parser.parse_args(argv)

    configs = load_refresh_configs()
    active_codes = {m.market_code for m in load_markets(active_only=True)}
    targets = sorted(
        code
        for code, cfg in configs.items()
        if code in active_codes and cfg.provider == "wikipedia"
    )
    if args.markets:
        selected = set(args.markets)
        targets = [code for code in targets if code in selected]

    if not targets:
        print("No provider:wikipedia markets selected.", file=sys.stderr)
        return 1

    rows = refresh_snapshot(targets, delay_seconds=args.delay_seconds)
    path = write_snapshot(rows)
    print(f"Wrote {len(rows)} names to {path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
