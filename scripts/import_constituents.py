"""Import a constituent CSV into storage/seeds/{market_code}/constituents.csv."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import pandas as pd

from ingestion.constituents.seeds import write_constituents
from ingestion.registry import get_market


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Import constituents from a local CSV file")
    parser.add_argument("--market", required=True, help="market_code from docs/market_registry.yml")
    parser.add_argument("--file", required=True, type=Path, help="CSV with ticker and company_name columns")
    parser.add_argument("--ticker-column", default="ticker")
    parser.add_argument("--name-column", default="company_name")
    args = parser.parse_args(argv)

    get_market(args.market)
    frame = pd.read_csv(args.file)
    if args.ticker_column not in frame.columns:
        print(f"Missing ticker column: {args.ticker_column}", file=sys.stderr)
        return 1
    if args.name_column not in frame.columns:
        print(f"Missing name column: {args.name_column}", file=sys.stderr)
        return 1

    path = write_constituents(
        args.market,
        frame[args.ticker_column],
        frame[args.name_column],
        source="import",
    )
    print(f"Wrote {path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
