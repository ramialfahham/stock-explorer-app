"""Try common Supabase Postgres endpoints and print the one that works.

Usage (from repo root, with .env configured):
    python scripts/discover_supabase_db_host.py

Prints GitHub secret values to set — never prints your password.
"""

from __future__ import annotations

import os
import sys
from urllib.parse import quote_plus

from dotenv import load_dotenv

# Common Supabase pooler regions (aws-0 and aws-1 variants)
POOLER_REGIONS = [
    "eu-central-1",
    "eu-central-2",
    "eu-west-1",
    "eu-west-2",
    "eu-west-3",
    "eu-north-1",
    "us-east-1",
    "us-east-2",
    "us-west-1",
    "ap-southeast-1",
]


def _strip(value: str | None) -> str | None:
    if not value:
        return None
    value = value.strip().strip('"').strip("'")
    return value or None


def _ref(url: str) -> str:
    host = url.replace("https://", "").replace("http://", "").split("/")[0]
    return host.split(".")[0]


def _try(url: str) -> tuple[bool, str]:
    try:
        import psycopg2
    except ImportError:
        return False, "install psycopg2-binary (pip install -r requirements.txt)"

    try:
        conn = psycopg2.connect(url + ("&sslmode=require" if "sslmode=" not in url else ""))
        conn.close()
        return True, "ok"
    except Exception as exc:
        return False, str(exc).split("\n")[0]


def main() -> int:
    load_dotenv()
    url = _strip(os.getenv("SUPABASE_URL"))
    password = _strip(os.getenv("SUPABASE_DB_PASSWORD"))
    if not url or not password:
        print("Set SUPABASE_URL and SUPABASE_DB_PASSWORD in .env first.", file=sys.stderr)
        return 1

    ref = _ref(url)
    enc = quote_plus(password)
    candidates: list[tuple[str, str, str, str]] = []

    # Direct (local / IPv6)
    candidates.append(
        ("direct", f"db.{ref}.supabase.co", "5432", f"postgresql://postgres:{enc}@db.{ref}.supabase.co:5432/postgres")
    )
    # Transaction on db host
    candidates.append(
        ("db-transaction", f"db.{ref}.supabase.co", "6543", f"postgresql://postgres:{enc}@db.{ref}.supabase.co:6543/postgres")
    )
    candidates.append(
        (
            "db-transaction-ref-user",
            f"db.{ref}.supabase.co",
            "6543",
            f"postgresql://postgres.{ref}:{enc}@db.{ref}.supabase.co:6543/postgres",
        )
    )

    for region in POOLER_REGIONS:
        for aws in ("aws-0", "aws-1"):
            host = f"{aws}-{region}.pooler.supabase.com"
            candidates.append(
                (
                    f"pooler-session-{aws}-{region}",
                    host,
                    "5432",
                    f"postgresql://postgres.{ref}:{enc}@{host}:5432/postgres",
                )
            )
            candidates.append(
                (
                    f"pooler-transaction-{aws}-{region}",
                    host,
                    "6543",
                    f"postgresql://postgres.{ref}:{enc}@{host}:6543/postgres",
                )
            )

    print(f"Probing connections for project ref {ref}...\n")
    working: list[tuple[str, str, str]] = []
    for label, host, port, conn_url in candidates:
        ok, msg = _try(conn_url)
        status = "OK" if ok else "fail"
        print(f"  [{status}] {label} ({host}:{port})")
        if ok:
            working.append((host, port, label))

    if not working:
        print("\nNo working endpoint found from this machine.", file=sys.stderr)
        print("Reset database password in Supabase and update .env, then retry.", file=sys.stderr)
        return 1

    host, port, label = working[0]
    print("\n--- Set these GitLab CI/CD variables (Protected) ---")
    print(f"SUPABASE_DB_HOST={host}")
    print(f"SUPABASE_DB_PORT={port}")
    print("SUPABASE_URL=https://{ref}.supabase.co".format(ref=ref))
    print("SUPABASE_DB_PASSWORD=(same as your .env)")
    print(f"\n(first working endpoint: {label})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
