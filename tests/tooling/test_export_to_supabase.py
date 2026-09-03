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


def test_export_columns_include_sector_min_max() -> None:
    """Regression guard: a new sector_median_* companion column (min/max) landing in the
    dbt mart but not in this static allowlist is silently never sent to Supabase -- the
    mart, the frontend, and every test can all be correct while production ships nothing.
    """
    for metric in (
        "forward_pe",
        "ebit_margin_pct",
        "revenue_growth_yoy_pct",
        "net_debt_to_ebitda",
        "fcf_margin_pct",
    ):
        assert f"sector_min_{metric}" in exp.EXPORT_COLUMNS
        assert f"sector_max_{metric}" in exp.EXPORT_COLUMNS


def test_export_columns_include_sector_quartiles() -> None:
    """Same regression guard as above, for the Q1/Q3 columns added for the outlier-aware
    range-mark display clamp (Gemini feedback point 5). forward_pe deliberately excluded --
    it already left the catalogue and carries no range mark, so it gets no quartile columns."""
    for metric in (
        "ebit_margin_pct",
        "revenue_growth_yoy_pct",
        "net_debt_to_ebitda",
        "fcf_margin_pct",
    ):
        assert f"sector_q1_{metric}" in exp.EXPORT_COLUMNS
        assert f"sector_q3_{metric}" in exp.EXPORT_COLUMNS
    assert "sector_q1_forward_pe" not in exp.EXPORT_COLUMNS
    assert "sector_q3_forward_pe" not in exp.EXPORT_COLUMNS


def test_export_columns_include_sector_financial_operating_expansion() -> None:
    """Same regression guard as above, for the 5-metric benchmark expansion (owner-approved
    follow-up to MR #22): debt_to_equity, current_ratio_stmt (operating) and
    statement_roe_pct, net_margin_pct, roa_pct (financial). All 5 statistics per metric,
    same as every other benchmarked metric."""
    for metric in (
        "debt_to_equity",
        "current_ratio_stmt",
        "statement_roe_pct",
        "net_margin_pct",
        "roa_pct",
    ):
        assert f"sector_median_{metric}" in exp.EXPORT_COLUMNS
        assert f"sector_min_{metric}" in exp.EXPORT_COLUMNS
        assert f"sector_max_{metric}" in exp.EXPORT_COLUMNS
        assert f"sector_q1_{metric}" in exp.EXPORT_COLUMNS
        assert f"sector_q3_{metric}" in exp.EXPORT_COLUMNS

    # Pre-revenue's 4 metrics stay deliberately unbenchmarked (only 3 pre-revenue companies
    # exist app-wide -- can never clear the 8-peer rendering threshold): this documents the
    # scope boundary as a test, not just prose.
    for metric in (
        "net_cash",
        "working_capital",
        "cash_runway_months",
        "burn_rate_monthly",
    ):
        assert f"sector_median_{metric}" not in exp.EXPORT_COLUMNS
        assert f"sector_min_{metric}" not in exp.EXPORT_COLUMNS
        assert f"sector_max_{metric}" not in exp.EXPORT_COLUMNS
        assert f"sector_q1_{metric}" not in exp.EXPORT_COLUMNS
        assert f"sector_q3_{metric}" not in exp.EXPORT_COLUMNS


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


def test_options_passed_to_create_client_is_the_sync_variant(tmp_path: Path, monkeypatch) -> None:
    """Regression guard: create_client's sync path reads options.storage internally
    (a confirmed supabase-py==2.30.0 bug — supabase/supabase-py#1306), which the base
    ClientOptions dataclass doesn't define, only SyncClientOptions/AsyncClientOptions do.
    A revert to plain ClientOptions crashes for real (verified live) but wouldn't be
    caught by the schema-only assertions elsewhere in this file, since both classes carry
    a .schema attribute — only .storage distinguishes them.
    """
    db = tmp_path / "mart.duckdb"
    _make_mart(db, [_ROW])
    monkeypatch.setenv("SUPABASE_URL", "https://fake.supabase.co")
    monkeypatch.setenv("SUPABASE_SERVICE_ROLE_KEY", "fake-key")

    seen_kwargs = {}

    def fake_create_client(url, key, options=None):
        seen_kwargs["options"] = options
        return _FakeClient([])

    monkeypatch.setattr(exp, "create_client", fake_create_client)

    assert exp.main(["--duckdb-path", str(db)]) == 0
    assert hasattr(seen_kwargs["options"], "storage")


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
