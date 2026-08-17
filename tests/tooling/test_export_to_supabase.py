"""Offline test for --target's schema wiring — no real Supabase, no network."""

from __future__ import annotations

from pathlib import Path

import duckdb

import export_to_supabase as exp


def _make_mart(path: Path, rows: list[dict]) -> None:
    con = duckdb.connect(str(path))
    con.execute("create schema if not exists marts")
    cols = ", ".join(f"{c} VARCHAR" for c in exp.EXPORT_COLUMNS)
    con.execute(f"create table marts.mart_stock_cards ({cols})")
    for row in rows:
        keys = list(row.keys())
        placeholders = ", ".join("?" for _ in keys)
        con.execute(
            f"insert into marts.mart_stock_cards ({', '.join(keys)}) values ({placeholders})",
            [row[k] for k in keys],
        )
    con.close()


_ROW = {"market_code": "us_sp500", "ticker": "T1", "snapshot_date": "2026-06-01"}


class _FakeQuery:
    def __init__(self, calls: list[dict]) -> None:
        self._calls = calls

    def upsert(self, batch, on_conflict=None):
        self._calls.append({"batch": batch, "on_conflict": on_conflict})
        return self

    def execute(self):
        return None


class _FakeClient:
    def __init__(self, calls: list[dict]) -> None:
        self._calls = calls

    def table(self, _name: str) -> _FakeQuery:
        return _FakeQuery(self._calls)


def test_target_dev_passes_dev_schema_to_create_client(tmp_path: Path, monkeypatch) -> None:
    db = tmp_path / "mart.duckdb"
    _make_mart(db, [_ROW])
    monkeypatch.setenv("SUPABASE_URL", "https://fake.supabase.co")
    monkeypatch.setenv("SUPABASE_SERVICE_ROLE_KEY", "fake-key")

    seen_kwargs = {}

    def fake_create_client(url, key, options=None):
        seen_kwargs["options"] = options
        return _FakeClient([])

    monkeypatch.setattr(exp, "create_client", fake_create_client)

    assert exp.main(["--duckdb-path", str(db), "--target", "dev"]) == 0
    assert seen_kwargs["options"].schema == "dev"


def test_target_prod_is_the_default_schema(tmp_path: Path, monkeypatch) -> None:
    db = tmp_path / "mart.duckdb"
    _make_mart(db, [_ROW])
    monkeypatch.setenv("SUPABASE_URL", "https://fake.supabase.co")
    monkeypatch.setenv("SUPABASE_SERVICE_ROLE_KEY", "fake-key")

    seen_kwargs = {}

    def fake_create_client(url, key, options=None):
        seen_kwargs["options"] = options
        return _FakeClient([])

    monkeypatch.setattr(exp, "create_client", fake_create_client)

    assert exp.main(["--duckdb-path", str(db)]) == 0  # no --target at all
    assert seen_kwargs["options"].schema == "public"


def test_dry_run_needs_no_credentials_regardless_of_target(tmp_path: Path, monkeypatch) -> None:
    db = tmp_path / "mart.duckdb"
    _make_mart(db, [_ROW])
    # main() calls load_dotenv() itself, which would re-read a real local .env and defeat
    # delenv below — stub it out so this test doesn't depend on whether one exists on disk.
    monkeypatch.setattr(exp, "load_dotenv", lambda *a, **k: None)
    monkeypatch.delenv("SUPABASE_URL", raising=False)
    monkeypatch.delenv("SUPABASE_SERVICE_ROLE_KEY", raising=False)

    assert exp.main(["--duckdb-path", str(db), "--target", "dev", "--dry-run"]) == 1
    # --dry-run still requires SUPABASE_URL/KEY to be present today (unchanged behavior);
    # this pins that --target doesn't accidentally bypass the existing credential check.
