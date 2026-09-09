"""Replace the mart_stock_cards snapshot in Supabase from DuckDB (service role).

--target selects which Postgres schema this writes to, inside the SAME Supabase project
(same credentials, no new secrets):

  prod (default) — public.mart_stock_cards. What Streamlit reads.
  dev            — dev.mart_stock_cards. A safe place to test an export change against a
                    real Postgres before it ships. Requires the "dev" schema to already
                    exist (run apply_supabase_migrations.py --target dev first) AND to be
                    added to the Supabase project's Settings -> API -> Exposed schemas list
                    once, manually. This script goes through PostgREST (client.rpc()),
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
    "net_cash",
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
    "sector_median_debt_to_equity",
    "sector_median_current_ratio_stmt",
    "sector_median_statement_roe_pct",
    "sector_median_net_margin_pct",
    "sector_median_roa_pct",
    "sector_min_forward_pe",
    "sector_max_forward_pe",
    "sector_min_ebit_margin_pct",
    "sector_max_ebit_margin_pct",
    "sector_min_revenue_growth_yoy_pct",
    "sector_max_revenue_growth_yoy_pct",
    "sector_min_net_debt_to_ebitda",
    "sector_max_net_debt_to_ebitda",
    "sector_min_fcf_margin_pct",
    "sector_max_fcf_margin_pct",
    "sector_min_debt_to_equity",
    "sector_max_debt_to_equity",
    "sector_min_current_ratio_stmt",
    "sector_max_current_ratio_stmt",
    "sector_min_statement_roe_pct",
    "sector_max_statement_roe_pct",
    "sector_min_net_margin_pct",
    "sector_max_net_margin_pct",
    "sector_min_roa_pct",
    "sector_max_roa_pct",
    "sector_q1_ebit_margin_pct",
    "sector_q3_ebit_margin_pct",
    "sector_q1_revenue_growth_yoy_pct",
    "sector_q3_revenue_growth_yoy_pct",
    "sector_q1_net_debt_to_ebitda",
    "sector_q3_net_debt_to_ebitda",
    "sector_q1_fcf_margin_pct",
    "sector_q3_fcf_margin_pct",
    "sector_q1_debt_to_equity",
    "sector_q3_debt_to_equity",
    "sector_q1_current_ratio_stmt",
    "sector_q3_current_ratio_stmt",
    "sector_q1_statement_roe_pct",
    "sector_q3_statement_roe_pct",
    "sector_q1_net_margin_pct",
    "sector_q3_net_margin_pct",
    "sector_q1_roa_pct",
    "sector_q3_roa_pct",
    "snapshot_date",
]


def _load_mart_rows(db_path: Path) -> list[dict]:
    conn = duckdb.connect(str(db_path), read_only=True)
    try:
        cols = ", ".join(EXPORT_COLUMNS)
        rows = conn.execute(
            f"select {cols} from marts.mart_stock_cards order by market_code, ticker, snapshot_date"
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


def inserted_count(data: object) -> int | None:
    """The row count replace_cards_snapshot returned, or None if the response is not one.

    PostgREST returns a scalar function's result as a bare value, but client versions differ
    on whether they hand it back wrapped in a single-element list. This accepts either rather
    than guessing, and returns None for anything else so the caller fails loudly instead of
    comparing against a shape it did not expect.
    """
    if isinstance(data, list):
        data = data[0] if len(data) == 1 else None
    if isinstance(data, bool) or not isinstance(data, int):
        return None
    return data


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

    # One transaction, server-side. The previous batched upsert committed each batch
    # separately, so a mid-run failure left production holding the new snapshot for some
    # tickers and the previous one for the rest, which the frontend then served as a mix.
    response = client.rpc("replace_cards_snapshot", {"payload": records}).execute()

    inserted = inserted_count(response.data)
    if inserted is None:
        # The call returned 2xx, so the transaction COMMITTED; only the response shape is
        # unrecognised. Saying anything about a rollback here would be a guess about
        # production state, and the wrong one.
        print(
            f"export_to_supabase: UNVERIFIED -- the write returned {response.data!r}, which is "
            f"not a row count. The snapshot was almost certainly written; check "
            f"mart_stock_cards in Supabase before re-running."
        )
        return 1
    if inserted != len(records):
        print(
            f"export_to_supabase: FAILED -- sent {len(records)} rows, database reported "
            f"{inserted} inserted. The transaction did not do what was asked."
        )
        return 1

    print(f"export_to_supabase: replaced snapshot with {inserted} rows in '{schema}'")
    return 0


if __name__ == "__main__":
    sys.exit(main())
