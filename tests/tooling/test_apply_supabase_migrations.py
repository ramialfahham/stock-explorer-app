"""Offline tests for --target dev's schema substitution — no real Postgres."""

from __future__ import annotations

from pathlib import Path

import apply_supabase_migrations as asm


class _FakeCursor:
    """Records every executed statement; answers the two SELECTs main()'s setup needs."""

    def __init__(self, log: list[tuple[str, tuple | None]]) -> None:
        self._log = log
        self._result: list[tuple] = []

    def __enter__(self) -> "_FakeCursor":
        return self

    def __exit__(self, *exc) -> bool:
        return False

    def execute(self, sql: str, params: tuple | None = None) -> None:
        self._log.append((sql, params))
        if "information_schema.tables" in sql:
            self._result = [(False,)]  # fresh schema: nothing exists yet
        elif sql.strip().startswith("select filename"):
            self._result = []  # nothing applied yet
        else:
            self._result = []

    def fetchone(self):
        return self._result[0] if self._result else None

    def fetchall(self):
        return self._result


class _FakeConn:
    def __init__(self) -> None:
        self.log: list[tuple[str, tuple | None]] = []
        self.commits = 0

    def cursor(self) -> _FakeCursor:
        return _FakeCursor(self.log)

    def commit(self) -> None:
        self.commits += 1

    def rollback(self) -> None:
        pass

    def close(self) -> None:
        pass


def _write_migration(tmp_path: Path, name: str, sql: str) -> Path:
    path = tmp_path / name
    path.write_text(sql, encoding="utf-8")
    return path


_SAMPLE_SQL = (
    "create table public.markets (market_code text primary key);\n"
    "alter table public.markets enable row level security;\n"
    'create policy "read" on public.markets for select using (true);\n'
)


def test_apply_file_substitutes_public_for_dev_schema(tmp_path: Path) -> None:
    path = _write_migration(tmp_path, "001_initial_schema.sql", _SAMPLE_SQL)
    conn = _FakeConn()

    asm._apply_file(conn, path, "dev", "dev.schema_migrations")

    executed_sql = conn.log[0][0]
    assert "dev.markets" in executed_sql
    assert "public.markets" not in executed_sql
    assert "insert into dev.schema_migrations" in conn.log[1][0]


def test_apply_file_leaves_prod_sql_untouched(tmp_path: Path) -> None:
    path = _write_migration(tmp_path, "001_initial_schema.sql", _SAMPLE_SQL)
    conn = _FakeConn()

    asm._apply_file(conn, path, "public", "public.schema_migrations")

    executed_sql = conn.log[0][0]
    assert executed_sql == _SAMPLE_SQL  # byte-identical — no substitution on the prod path
    assert "insert into public.schema_migrations" in conn.log[1][0]


def test_ensure_schema_creates_dev_but_skips_public() -> None:
    dev_conn = _FakeConn()
    asm._ensure_schema(dev_conn, "dev")
    assert dev_conn.log == [("create schema if not exists dev", None)]

    prod_conn = _FakeConn()
    asm._ensure_schema(prod_conn, "public")
    assert prod_conn.log == []  # no needless DDL against a schema that always exists


def test_main_target_dev_wires_schema_through(tmp_path: Path, monkeypatch) -> None:
    migration = _write_migration(tmp_path, "001_initial_schema.sql", _SAMPLE_SQL)
    fake_conn = _FakeConn()

    monkeypatch.setattr(asm, "resolve_database_url", lambda: "postgresql://fake")
    monkeypatch.setattr(asm, "_connect", lambda db_url: fake_conn)
    monkeypatch.setattr(asm, "_list_migration_files", lambda: [migration])

    assert asm.main(["--target", "dev"]) == 0

    executed = "\n".join(sql for sql, _ in fake_conn.log)
    assert "create schema if not exists dev" in executed
    assert "dev.schema_migrations" in executed
    assert "dev.markets" in executed
    assert "public." not in executed  # every public. reference was rewritten


def test_main_target_prod_is_the_default(tmp_path: Path, monkeypatch, capsys) -> None:
    migration = _write_migration(tmp_path, "001_initial_schema.sql", _SAMPLE_SQL)
    fake_conn = _FakeConn()

    monkeypatch.setattr(asm, "resolve_database_url", lambda: "postgresql://fake")
    monkeypatch.setattr(asm, "_connect", lambda db_url: fake_conn)
    monkeypatch.setattr(asm, "_list_migration_files", lambda: [migration])

    assert asm.main(["--dry-run"]) == 0  # no --target at all

    out = capsys.readouterr().out
    assert "Pending migrations for 'public'" in out
    assert "create schema if not exists dev" not in "\n".join(sql for sql, _ in fake_conn.log)


_RESOLVE_KEYS = (
    "SUPABASE_URL",
    "SUPABASE_DB_PASSWORD",
    "SUPABASE_DB_HOST",
    "SUPABASE_DB_PORT",
    "SUPABASE_DB_URL",
    "SUPABASE_DB_POOLER_URL",
)


def _env(monkeypatch, **values: str) -> None:
    for key in _RESOLVE_KEYS:
        monkeypatch.delenv(key, raising=False)
    for key, value in values.items():
        monkeypatch.setenv(key, value)


def test_resolve_database_url_prefers_the_pooler_host(monkeypatch) -> None:
    _env(
        monkeypatch,
        SUPABASE_URL="https://abcd.supabase.co",
        SUPABASE_DB_PASSWORD="pw",
        SUPABASE_DB_HOST="aws-1-eu.pooler.supabase.com",
        SUPABASE_DB_URL="postgresql://ignored",
    )
    url = asm.resolve_database_url()
    assert url.startswith("postgresql://postgres.abcd:pw@aws-1-eu.pooler.supabase.com:5432/postgres")


def test_resolve_database_url_falls_back_to_the_full_uri(monkeypatch) -> None:
    _env(monkeypatch, SUPABASE_DB_URL="postgresql://u:p@host:5432/postgres")
    assert asm.resolve_database_url().startswith("postgresql://u:p@host:5432/postgres")


def test_resolve_database_url_full_uri_beats_the_direct_host(monkeypatch) -> None:
    _env(
        monkeypatch,
        SUPABASE_URL="https://abcd.supabase.co",
        SUPABASE_DB_PASSWORD="pw",
        SUPABASE_DB_URL="postgresql://u:p@host:5432/postgres",
    )
    assert asm.resolve_database_url().startswith("postgresql://u:p@host:5432/postgres")


def test_resolve_database_url_local_direct_host(monkeypatch) -> None:
    _env(monkeypatch, SUPABASE_URL="https://abcd.supabase.co", SUPABASE_DB_PASSWORD="pw")
    assert "@db.abcd.supabase.co:5432/postgres" in asm.resolve_database_url()


def test_resolve_database_url_without_credentials_raises(monkeypatch) -> None:
    _env(monkeypatch)
    try:
        asm.resolve_database_url()
    except RuntimeError as exc:
        assert "SUPABASE_DB_HOST" in str(exc)
    else:
        raise AssertionError("expected RuntimeError")
