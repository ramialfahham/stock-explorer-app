"""Apply pending SQL migrations to Supabase Postgres (no Dashboard copy/paste).

Tracks applied files in public.schema_migrations. Safe to run locally and in CI.

Requires in .env (or GitHub Actions secrets):
  SUPABASE_URL + SUPABASE_DB_PASSWORD
  or SUPABASE_DB_URL (full postgresql:// URI)

Usage:
    python scripts/apply_supabase_migrations.py
    python scripts/apply_supabase_migrations.py --dry-run
"""

from __future__ import annotations

import argparse
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote_plus

from dotenv import load_dotenv

REPO_ROOT = Path(__file__).resolve().parents[1]
MIGRATIONS_DIR = REPO_ROOT / "supabase" / "migrations"

MIGRATION_TABLE = "public.schema_migrations"
MIGRATION_FILE_PATTERN = re.compile(r"^\d{3}_.+\.sql$")


def _project_ref_from_supabase_url(supabase_url: str) -> str:
    host = supabase_url.replace("https://", "").replace("http://", "").split("/")[0]
    ref = host.split(".")[0]
    if not ref:
        raise ValueError(f"Could not parse project ref from SUPABASE_URL: {supabase_url}")
    return ref


def resolve_database_url() -> str:
    direct = os.getenv("SUPABASE_DB_URL")
    if direct:
        return direct.strip()

    supabase_url = os.getenv("SUPABASE_URL")
    password = os.getenv("SUPABASE_DB_PASSWORD")
    if not supabase_url or not password:
        raise RuntimeError(
            "Set SUPABASE_DB_URL or both SUPABASE_URL and SUPABASE_DB_PASSWORD in .env"
        )

    ref = _project_ref_from_supabase_url(supabase_url)
    encoded_password = quote_plus(password)
    return f"postgresql://postgres:{encoded_password}@db.{ref}.supabase.co:5432/postgres"


def _connect(db_url: str):
    try:
        import psycopg2
    except ImportError as exc:
        raise RuntimeError(
            "psycopg2 is required for migrations. Run: pip install -r requirements.txt"
        ) from exc

    return psycopg2.connect(db_url)


def _list_migration_files() -> list[Path]:
    if not MIGRATIONS_DIR.is_dir():
        raise FileNotFoundError(f"Missing migrations directory: {MIGRATIONS_DIR}")

    files = sorted(
        path
        for path in MIGRATIONS_DIR.glob("*.sql")
        if MIGRATION_FILE_PATTERN.match(path.name)
    )
    if not files:
        raise RuntimeError(f"No migration files found in {MIGRATIONS_DIR}")
    return files


def _ensure_migration_table(conn) -> None:
    with conn.cursor() as cur:
        cur.execute(
            f"""
            create table if not exists {MIGRATION_TABLE} (
                filename text primary key,
                applied_at timestamptz not null default now()
            )
            """
        )
    conn.commit()


def _applied_migrations(conn) -> set[str]:
    with conn.cursor() as cur:
        cur.execute(f"select filename from {MIGRATION_TABLE}")
        return {row[0] for row in cur.fetchall()}


def _table_exists(conn, table_name: str) -> bool:
    with conn.cursor() as cur:
        cur.execute(
            """
            select exists (
                select 1
                from information_schema.tables
                where table_schema = 'public' and table_name = %s
            )
            """,
            (table_name,),
        )
        return bool(cur.fetchone()[0])


def _bootstrap_manual_initial_schema(conn, first_migration: str) -> None:
    """Record 001 as applied when project was set up before this script existed."""
    if first_migration != "001_initial_schema.sql":
        return
    if not (_table_exists(conn, "markets") and _table_exists(conn, "user_interactions")):
        return

    with conn.cursor() as cur:
        cur.execute(
            f"""
            insert into {MIGRATION_TABLE} (filename, applied_at)
            values (%s, %s)
            on conflict (filename) do nothing
            """,
            (first_migration, datetime.now(timezone.utc)),
        )
    conn.commit()
    print(f"Bootstrapped {first_migration} (existing schema detected)")


def _apply_file(conn, path: Path) -> None:
    sql = path.read_text(encoding="utf-8")
    with conn.cursor() as cur:
        cur.execute(sql)
        cur.execute(
            f"insert into {MIGRATION_TABLE} (filename) values (%s)",
            (path.name,),
        )
    conn.commit()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Apply Supabase SQL migrations")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="List pending migrations without applying",
    )
    args = parser.parse_args(argv)

    load_dotenv()

    try:
        db_url = resolve_database_url()
        migration_files = _list_migration_files()
    except Exception as exc:
        print(f"apply_supabase_migrations: {exc}", file=sys.stderr)
        return 1

    try:
        conn = _connect(db_url)
    except Exception as exc:
        print(f"apply_supabase_migrations: database connection failed — {exc}", file=sys.stderr)
        return 1

    try:
        _ensure_migration_table(conn)
        _bootstrap_manual_initial_schema(conn, migration_files[0].name)
        applied = _applied_migrations(conn)

        pending = [path for path in migration_files if path.name not in applied]
        if not pending:
            print("apply_supabase_migrations: all migrations already applied")
            return 0

        print(f"Pending migrations ({len(pending)}):")
        for path in pending:
            print(f"  - {path.name}")

        if args.dry_run:
            return 0

        for path in pending:
            print(f"Applying {path.name}...")
            try:
                _apply_file(conn, path)
            except Exception as exc:
                conn.rollback()
                print(f"apply_supabase_migrations: failed on {path.name} — {exc}", file=sys.stderr)
                return 1
            print(f"  ok")

        print("apply_supabase_migrations: done")
        return 0
    finally:
        conn.close()


if __name__ == "__main__":
    sys.exit(main())
