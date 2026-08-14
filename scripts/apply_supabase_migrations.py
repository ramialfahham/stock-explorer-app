"""Apply pending SQL migrations to Supabase Postgres (no Dashboard copy/paste).

Tracks applied files in public.schema_migrations. Safe to run locally and in CI.

Requires in .env (or GitLab CI/CD variables) — pick one approach:

  A) CI-friendly (recommended):
     SUPABASE_URL + SUPABASE_DB_PASSWORD + SUPABASE_DB_HOST
     (+ optional SUPABASE_DB_PORT, default 5432 Session pooler)

  B) Full URI:
     SUPABASE_DB_URL (Session pooler URI from Supabase Connect dialog)

  C) Local only:
     SUPABASE_URL + SUPABASE_DB_PASSWORD (direct db.*.supabase.co)

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
import json
from urllib.parse import quote_plus, urlparse
from urllib.request import Request, urlopen

from dotenv import load_dotenv

REPO_ROOT = Path(__file__).resolve().parents[1]
MIGRATIONS_DIR = REPO_ROOT / "supabase" / "migrations"

MIGRATION_TABLE = "public.schema_migrations"
MIGRATION_FILE_PATTERN = re.compile(r"^\d{3}_.+\.sql$")


def _strip_env(value: str | None) -> str | None:
    if value is None:
        return None
    value = value.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
        value = value[1:-1]
    return value.strip() or None


def _project_ref_from_supabase_url(supabase_url: str) -> str:
    host = supabase_url.replace("https://", "").replace("http://", "").split("/")[0]
    ref = host.split(".")[0]
    if not ref:
        raise ValueError(f"Could not parse project ref from SUPABASE_URL: {supabase_url}")
    return ref


def _build_pooler_url(project_ref: str, password: str, pooler_host: str, port: str) -> str:
    host = pooler_host.removeprefix("https://").removeprefix("http://").split("/")[0]
    return (
        f"postgresql://postgres.{project_ref}:{quote_plus(password)}"
        f"@{host}:{port}/postgres"
    )


def _fetch_pooler_host_port(project_ref: str, access_token: str) -> tuple[str, str]:
    """Resolve pooler host/port via Supabase Management API (no Connect UI needed)."""
    url = f"https://api.supabase.com/v1/projects/{project_ref}/config/database/pooler"
    request = Request(
        url,
        headers={
            "Authorization": f"Bearer {access_token}",
            "Accept": "application/json",
        },
    )
    with urlopen(request, timeout=30) as response:
        payload = json.loads(response.read().decode("utf-8"))

    # Prefer explicit session mode connection string when present.
    candidates: list[str] = []
    if isinstance(payload, dict):
        for key in ("session", "transaction"):
            section = payload.get(key)
            if isinstance(section, dict):
                for field in ("connection_string", "connectionString", "uri"):
                    value = section.get(field)
                    if isinstance(value, str):
                        candidates.append(value)

        for value in payload.values():
            if isinstance(value, str) and "pooler.supabase.com" in value:
                candidates.append(value)

    blob = json.dumps(payload)
    if "pooler.supabase.com" in blob:
        import re

        for match in re.findall(r"@[^:@/\"']+?pooler\\.supabase\\.com:(\\d+)", blob):
            host_match = re.search(
                rf"([a-z0-9.-]+pooler\\.supabase\\.com):{match}",
                blob,
            )
            if host_match:
                return host_match.group(1), match

    for conn in candidates:
        parsed = urlparse(conn.replace("postgres://", "postgresql://", 1))
        if parsed.hostname and parsed.port:
            return parsed.hostname, str(parsed.port)

    raise RuntimeError(
        "Could not parse pooler host from Supabase Management API response. "
        "Set SUPABASE_DB_HOST manually or paste SUPABASE_DB_URL."
    )


def resolve_database_url() -> str:
    supabase_url = _strip_env(os.getenv("SUPABASE_URL"))
    password = _strip_env(os.getenv("SUPABASE_DB_PASSWORD"))
    pooler_host = _strip_env(os.getenv("SUPABASE_DB_HOST"))
    pooler_port = _strip_env(os.getenv("SUPABASE_DB_PORT")) or "5432"
    access_token = _strip_env(os.getenv("SUPABASE_ACCESS_TOKEN"))

    if supabase_url and password and pooler_host:
        ref = _project_ref_from_supabase_url(supabase_url)
        return _ensure_sslmode(_build_pooler_url(ref, password, pooler_host, pooler_port))

    if supabase_url and password and access_token and os.getenv("GITHUB_ACTIONS"):
        ref = _project_ref_from_supabase_url(supabase_url)
        host, port = _fetch_pooler_host_port(ref, access_token)
        print(f"Resolved pooler via Management API: {host}:{port}")
        return _ensure_sslmode(_build_pooler_url(ref, password, host, port))

    for key in ("SUPABASE_DB_URL", "SUPABASE_DB_POOLER_URL"):
        value = _strip_env(os.getenv(key))
        if value:
            return _ensure_sslmode(value)

    if supabase_url and password:
        ref = _project_ref_from_supabase_url(supabase_url)
        return _ensure_sslmode(
            f"postgresql://postgres:{quote_plus(password)}@db.{ref}.supabase.co:5432/postgres"
        )

    raise RuntimeError(
        "CI: set SUPABASE_ACCESS_TOKEN (auto pooler lookup) or SUPABASE_DB_HOST. "
        "Local: SUPABASE_URL + SUPABASE_DB_PASSWORD."
    )


def _ensure_sslmode(db_url: str) -> str:
    if "sslmode=" in db_url:
        return db_url
    separator = "&" if "?" in db_url else "?"
    return f"{db_url}{separator}sslmode=require"


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
        if os.getenv("GITHUB_ACTIONS"):
            print(
                "CI hint: add GitHub secret SUPABASE_ACCESS_TOKEN "
                "(Supabase Dashboard → Account → Access Tokens) for automatic pooler lookup, "
                "or set SUPABASE_DB_HOST + SUPABASE_DB_PORT manually.",
                file=sys.stderr,
            )
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
