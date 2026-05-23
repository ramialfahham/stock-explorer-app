"""Refresh constituent seed CSVs from configured external sources."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ingestion.constituents.refresh import load_refresh_configs, refresh_market
from ingestion.registry import load_markets


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Refresh storage/seeds/{market_code}/constituents.csv from external sources"
    )
    parser.add_argument(
        "--market",
        action="append",
        dest="markets",
        help="Limit to one or more market_code values (default: all refresh-enabled markets)",
    )
    args = parser.parse_args(argv)

    configs = load_refresh_configs()
    active_codes = {m.market_code for m in load_markets(active_only=True)}
    targets = [
        cfg
        for cfg in configs.values()
        if cfg.market_code in active_codes and cfg.refresh_enabled
    ]

    if args.markets:
        selected = set(args.markets)
        targets = [cfg for cfg in targets if cfg.market_code in selected]

    if not targets:
        print("No refresh-enabled markets selected.", file=sys.stderr)
        return 1

    exit_code = 0
    for config in targets:
        try:
            count = refresh_market(config)
            print(f"{config.market_code}: refreshed {count} tickers from {config.provider}")
        except Exception as exc:
            print(f"{config.market_code}: failed — {exc}", file=sys.stderr)
            exit_code = 1

    skipped = [
        code
        for code in active_codes
        if code in configs and not configs[code].refresh_enabled
    ]
    for code in skipped:
        if not args.markets or code in args.markets:
            print(f"{code}: skipped (manual seed — update CSV or import_constituents.py)")

    return exit_code


if __name__ == "__main__":
    sys.exit(main())
