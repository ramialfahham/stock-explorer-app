"""Verify Supabase credentials and that the initial schema exists."""

from __future__ import annotations

import os
import sys

from dotenv import load_dotenv
from supabase import Client, create_client

REQUIRED_TABLES = ("markets", "mart_stock_cards", "user_interactions")


def main() -> int:
    load_dotenv()

    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_ANON_KEY")

    if not url or not key:
        print("Missing SUPABASE_URL or key in .env")
        print("Copy .env.example to .env and add your project values.")
        return 1

    client: Client = create_client(url, key)
    key_type = "service_role" if os.getenv("SUPABASE_SERVICE_ROLE_KEY") else "anon"

    print(f"Connected to {url} ({key_type} key)")

    for table in REQUIRED_TABLES:
        response = client.table(table).select("*", count="exact").limit(1).execute()
        count = response.count if response.count is not None else "?"
        print(f"  {table}: ok ({count} rows)")

    markets = client.table("markets").select("market_code, ingest_active").execute()
    active = [row["market_code"] for row in markets.data if row["ingest_active"]]
    print(f"Active markets: {', '.join(active) if active else '(none)'}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
