#!/usr/bin/env python3
"""Add nullable intl operating-margin columns to existing yf_fundamentals.parquet files."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[1]
RAW_ROOT = REPO_ROOT / "storage" / "raw"

NEW_COLUMNS = [
    *(f"qtr_operating_revenue_{idx}" for idx in range(4)),
    *(f"qtr_operating_expense_{idx}" for idx in range(4)),
    "stmt_operating_income",
    "stmt_operating_revenue",
    "stmt_operating_expense",
    "info_founded_year",
]


def main() -> int:
    paths = sorted(RAW_ROOT.glob("*/yf_fundamentals.parquet"))
    if not paths:
        print("backfill_fundamentals_parquet_schema: no parquet files found")
        return 0

    for path in paths:
        frame = pd.read_parquet(path)
        changed = False
        for column in NEW_COLUMNS:
            if column not in frame.columns:
                frame[column] = None
                changed = True
        if changed:
            frame.to_parquet(path, index=False)
            print(f"backfill_fundamentals_parquet_schema: updated {path.relative_to(REPO_ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
