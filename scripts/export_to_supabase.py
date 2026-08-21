"""Upsert mart_stock_cards from DuckDB into Supabase (service role).

--target selects which Postgres schema this writes to, inside the SAME Supabase project
(same credentials, no new secrets):

  prod (default) — public.mart_stock_cards. What Streamlit reads.
  dev            — dev.mart_stock_cards. A safe place to test an export change against a
                    real Postgres before it ships. Requires the "dev" schema to already
                    exist (run apply_supabase_migrations.py --target dev first) AND to be
                    added to the Supabase project's Settings -> API -> Exposed schemas list
                    once, manually — this script goes through PostgREST (client.table()),
                    which only serves schemas on that list. apply_supabase_migrations.py is
                    unaffected (raw Postgres connection, not PostgREST).
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
from supabase.lib.client_options import SyncClientOptions

REPO_ROOT = Path(__file__).resolve().parents[1]

EXPORT_COLUMNS = [
    "market_code",
    "ticker",
    "company_name",
    "sector",
    "currency",
    "business_summary",
    "company_founded_year",
    "forward_pe",
    "ebit_margin_pct",
    "ebit_margin_basis",
    "revenue_growth_yoy_pct",
    "net_debt_to_ebitda",
    "fcf_margin_pct",
    "debt_to_equity",
    "current_ratio_stmt",
    "statement_roe_pct",
    "price_to_tangible_book",
    "net_margin_pct",
    "roa_pct",
    "dividend_yield_pct",
    "net_cash_to_market_cap",
    "working_capital",
    "cash_runway_months",
    "burn_rate_monthly",
    "is_card_eligible",
    "company_type",
    "sector_peer_count",
    "sector_median_forward_pe",
    "sector_median_ebit_margin_pct",
    "sector_median_revenue_growth_yoy_pct",
    "sector_median_net_debt_to_ebitda",
    "sector_median_fcf_margin_pct",
    "snapshot_date",
]


def _load_mart_rows(db_path: Path) -> list[dict]:
    conn = duckdb.connect(str(db_path), read_only=True)
    try:
        cols = ", ".join(EXPORT_COLUMNS)
        rows = conn.execute(
            f"select {cols} from marts.mart_stock_cards"
        ).fetchdf()
    finally:
        conn.close()

    if rows.empty:
        return []

    exported_at = datetime.now(timezone.utc).isoformat()
    records: list[dict] = []
    for _, row in rows.iterrows():
        record = {col: row[col] for col in EXPORT_COLUMNS}
        for key, value in record.items():
            if value is None or pd.isna(value):
                record[key] = None
            elif isinstance(value, float) and value != value:
                record[key] = None
            elif hasattr(value, "isoformat"):
                record[key] = value.isoformat()
            elif hasattr(value, "item"):
                record[key] = value.item()
            else:
                record[key] = value
        record["exported_at"] = exported_at
        records.append(record)
    return records


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Export mart_stock_cards to Supabase")
    parser.add_argument(
        "--duckdb-path",
        default=str(REPO_ROOT / "storage" / "stock_data.db"),
        help="Path to DuckDB file after dbt build",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Load rows but do not write to Supabase",
    )
    parser.add_argument(
        "--target",
        choices=["prod", "dev"],
        default="prod",
        help="prod (default) writes to public.*; dev writes to dev.* in the same project",
    )
    args = parser.parse_args(argv)

    load_dotenv()
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
    if not url or not key:
        print("Missing SUPABASE_URL or SUPABASE_SERVICE_ROLE_KEY in .env")
        return 1

    schema = "public" if args.target == "prod" else args.target

    db_path = Path(args.duckdb_path)
    if not db_path.exists():
        print(f"DuckDB not found: {db_path}")
        return 1

    records = _load_mart_rows(db_path)
    print(f"Loaded {len(records)} rows from marts.mart_stock_cards")

    if args.dry_run:
        return 0

    if not records:
        print("Nothing to export; keeping existing Supabase snapshot.")
        return 0

    client = create_client(url, key, options=SyncClientOptions(schema=schema))
    batch_size = 500
    for start in range(0, len(records), batch_size):
        batch = records[start : start + batch_size]
        client.table("mart_stock_cards").upsert(
            batch,
            on_conflict="market_code,ticker,snapshot_date",
        ).execute()

    print(f"export_to_supabase: upserted {len(records)} rows to '{schema}'")
    return 0


if __name__ == "__main__":
    sys.exit(main())
