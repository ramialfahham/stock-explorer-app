"""Generate per-card health assessments from the DuckDB mart into Supabase (Slice 5a).

Deterministic verdict only — NO LLM. Mirrors scripts/export_to_supabase.py: reads
marts.mart_stock_cards (already filtered to eligible cards), computes a per-type health
verdict + an input_hash per card, and upserts into public.card_assessments.

The prose read (ai_read) is written later by Slice 5b and is deliberately NOT part of the
upsert payload here, so re-running 5a never clobbers a 5b read (PostgREST upsert only sets
the columns provided).
"""

from __future__ import annotations

import argparse
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

import duckdb
import pandas as pd
from dotenv import load_dotenv
from supabase import create_client

from assessment_rules import (
    INPUT_FIELDS_BY_TYPE,
    compute_input_hash,
    compute_verdict,
)

REPO_ROOT = Path(__file__).resolve().parents[1]

# Union of every per-type card metric (derived from the rules module so it can't drift),
# plus the keys the verdict/hash and dedupe need.
_METRIC_COLUMNS = sorted({m for fields in INPUT_FIELDS_BY_TYPE.values() for m in fields})
ASSESSMENT_INPUT_COLUMNS = [
    "market_code",
    "ticker",
    "company_type",
    "snapshot_date",
    *_METRIC_COLUMNS,
]


def _coerce(value):
    """Match export_to_supabase coercion: NaN/NA -> None, dates -> iso, numpy -> python."""
    if value is None or pd.isna(value):
        return None
    if isinstance(value, float) and value != value:  # defensive NaN
        return None
    if hasattr(value, "isoformat"):
        return value.isoformat()
    if hasattr(value, "item"):
        return value.item()
    return value


def _load_mart_rows(db_path: Path) -> list[dict]:
    conn = duckdb.connect(str(db_path), read_only=True)
    try:
        cols = ", ".join(ASSESSMENT_INPUT_COLUMNS)
        frame = conn.execute(f"select {cols} from marts.mart_stock_cards").fetchdf()
    finally:
        conn.close()
    if frame.empty:
        return []
    return [
        {col: _coerce(row[col]) for col in ASSESSMENT_INPUT_COLUMNS}
        for _, row in frame.iterrows()
    ]


def _latest_per_ticker(rows: list[dict]) -> list[dict]:
    """Keep the row with the max snapshot_date per (market_code, ticker)."""
    latest: dict[tuple, dict] = {}
    for row in rows:
        key = (row["market_code"], row["ticker"])
        current = latest.get(key)
        if current is None or str(row["snapshot_date"]) > str(current["snapshot_date"]):
            latest[key] = row
    return list(latest.values())


def build_assessment_records(rows: list[dict]) -> list[dict]:
    """Pure: dedupe to latest snapshot, then verdict + input_hash per card.

    ai_read / read_model are intentionally omitted (not None) so a 5a upsert never nulls a
    Slice-5b prose read.
    """
    generated_at = datetime.now(timezone.utc).isoformat()
    records: list[dict] = []
    for row in _latest_per_ticker(rows):
        verdict = compute_verdict(row)
        records.append(
            {
                "market_code": row["market_code"],
                "ticker": row["ticker"],
                "company_type": row["company_type"],
                "health_verdict": verdict,
                "input_hash": compute_input_hash(row, verdict),
                "snapshot_date": row["snapshot_date"],
                "generated_at": generated_at,
            }
        )
    return records


def _verdict_distribution(records: list[dict]) -> dict[str, int]:
    dist: dict[str, int] = {}
    for rec in records:
        dist[rec["health_verdict"]] = dist.get(rec["health_verdict"], 0) + 1
    return dist


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Generate card_assessments verdicts from the DuckDB mart (Slice 5a)"
    )
    parser.add_argument(
        "--duckdb-path",
        default=str(REPO_ROOT / "storage" / "stock_data.db"),
        help="Path to DuckDB file after dbt build",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Compute verdicts but do not write to Supabase (no credentials required)",
    )
    args = parser.parse_args(argv)

    load_dotenv()

    db_path = Path(args.duckdb_path)
    if not db_path.exists():
        print(f"DuckDB not found: {db_path}", file=sys.stderr)
        return 1

    records = build_assessment_records(_load_mart_rows(db_path))
    print(
        f"generate_assessments: {len(records)} cards -> verdicts {_verdict_distribution(records)}"
    )

    # Dry-run returns before touching credentials so CI can smoke it secret-free.
    if args.dry_run:
        return 0

    if not records:
        print("Nothing to generate; keeping existing card_assessments snapshot.")
        return 0

    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
    if not url or not key:
        print("Missing SUPABASE_URL or SUPABASE_SERVICE_ROLE_KEY in .env", file=sys.stderr)
        return 1

    client = create_client(url, key)
    batch_size = 500
    for start in range(0, len(records), batch_size):
        batch = records[start : start + batch_size]
        client.table("card_assessments").upsert(
            batch, on_conflict="market_code,ticker"
        ).execute()

    print(f"generate_assessments: upserted {len(records)} rows")
    return 0


if __name__ == "__main__":
    sys.exit(main())
