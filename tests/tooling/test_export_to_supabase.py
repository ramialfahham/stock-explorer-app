"""Offline test for --target's schema wiring — no real Supabase, no network."""

from __future__ import annotations

import itertools
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


class _FakeResponse:
    def __init__(self, data) -> None:
        self.data = data


class _FakeQuery:
    def __init__(self, calls: list[dict], response=None) -> None:
        self._calls = calls
        self._response = response

    def upsert(self, batch, on_conflict=None):
        self._calls.append({"batch": batch, "on_conflict": on_conflict})
        return self

    def execute(self):
        return self._response


class _FakeClient:
    """Records every rpc/table call so a test can assert HOW the export wrote, not just that
    it returned 0. The whole point of this change is that the write is one transaction."""

    def __init__(self, calls: list[dict], rpc_result=None) -> None:
        self._calls = calls
        self._rpc_result = rpc_result

    def table(self, _name: str) -> _FakeQuery:
        return _FakeQuery(self._calls)

    def rpc(self, name: str, params: dict) -> _FakeQuery:
        self._calls.append({"rpc": name, "params": params})
        return _FakeQuery(self._calls, _FakeResponse(self._rpc_result))


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
        return _FakeClient([], rpc_result=1)

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
        return _FakeClient([], rpc_result=1)

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
        return _FakeClient([], rpc_result=1)

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


# --- Atomic export (issue #9 finding A1) ---
# The export used to write in batches of 500 with no transaction, so a failure partway left
# production holding the new snapshot for some tickers and the previous one for the rest.
# These pin the shape of the fix: one call, one transaction, and a loud failure if the
# database does not confirm every row.


_EXPORT_RUN = itertools.count()


def _run_export(monkeypatch, tmp_path, rows, rpc_result):
    db = tmp_path / f"mart_{next(_EXPORT_RUN)}.duckdb"
    _make_mart(db, rows)
    calls: list[dict] = []
    monkeypatch.setattr(exp, "load_dotenv", lambda *a, **k: None)
    monkeypatch.setenv("SUPABASE_URL", "https://fixture.supabase.co")
    monkeypatch.setenv("SUPABASE_SERVICE_ROLE_KEY", "fixture-key")
    monkeypatch.setattr(exp, "create_client", lambda *a, **k: _FakeClient(calls, rpc_result))
    code = exp.main(["--duckdb-path", str(db)])
    return code, calls


def test_export_writes_in_a_single_transaction(tmp_path: Path, monkeypatch) -> None:
    """One rpc call, never a per-batch loop. A second write call would mean a partial failure
    is still reachable."""
    rows = [dict(_ROW, ticker=f"T{i}") for i in range(3)]
    code, calls = _run_export(monkeypatch, tmp_path, rows, len(rows))

    assert code == 0
    assert len(calls) == 1
    assert calls[0]["rpc"] == "replace_cards_snapshot"
    assert len(calls[0]["params"]["payload"]) == len(rows)
    assert not [c for c in calls if "batch" in c]


def test_export_fails_when_the_database_confirms_a_different_count(
    tmp_path: Path, monkeypatch
) -> None:
    """A short count means the transaction did not do what was asked. Exiting 0 there would
    report a good export over a snapshot nobody verified."""
    rows = [dict(_ROW, ticker=f"T{i}") for i in range(3)]
    code, _ = _run_export(monkeypatch, tmp_path, rows, 2)
    assert code == 1


def test_export_fails_on_an_unreadable_response(tmp_path: Path, monkeypatch) -> None:
    rows = [dict(_ROW, ticker=f"T{i}") for i in range(3)]
    assert _run_export(monkeypatch, tmp_path, rows, None)[0] == 1
    assert _run_export(monkeypatch, tmp_path, rows, "3")[0] == 1


def test_unreadable_response_does_not_claim_a_rollback(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    """postgrest raises on a non-2xx, so reaching this branch means the write COMMITTED.
    An earlier version printed "the transaction rolled back ... the previous snapshot is
    intact" here, which is false in the only case that reaches it and would send an operator
    hunting for a rollback that never happened."""
    rows = [dict(_ROW, ticker=f"T{i}") for i in range(3)]
    _run_export(monkeypatch, tmp_path, rows, {"unexpected": "shape"})
    out = capsys.readouterr().out
    assert "rolled back" not in out
    assert "previous snapshot is intact" not in out
    assert "UNVERIFIED" in out and "check" in out


def test_count_mismatch_says_the_transaction_did_not_do_what_was_asked(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    rows = [dict(_ROW, ticker=f"T{i}") for i in range(3)]
    _run_export(monkeypatch, tmp_path, rows, 2)
    out = capsys.readouterr().out
    assert "FAILED" in out
    assert "rolled back" not in out


def test_export_accepts_either_scalar_response_shape(tmp_path: Path, monkeypatch) -> None:
    """PostgREST returns a scalar function's result bare; client versions differ on whether
    they wrap it in a one-element list. Verified against dev over a direct Postgres
    connection, NOT over REST, so the shape is handled rather than assumed."""
    rows = [dict(_ROW, ticker=f"T{i}") for i in range(3)]
    assert _run_export(monkeypatch, tmp_path, rows, 3)[0] == 0
    assert _run_export(monkeypatch, tmp_path, rows, [3])[0] == 0


def test_inserted_count_rejects_shapes_that_are_not_a_count() -> None:
    assert exp.inserted_count(3) == 3
    assert exp.inserted_count([3]) == 3
    assert exp.inserted_count(None) is None
    assert exp.inserted_count("3") is None
    assert exp.inserted_count([3, 4]) is None
    assert exp.inserted_count(True) is None


def test_mart_rows_are_read_in_a_deterministic_order(tmp_path: Path, monkeypatch) -> None:
    """The source query had no ORDER BY, so which rows landed before a partial failure
    differed every run and the resulting state could not be reproduced. The order is the
    Postgres table's key, (market_code, ticker, snapshot_date), not a prefix of it: the mart
    declares (market_code, ticker) uniqueness, but the exporter orders what it is handed and
    must stay total for a payload that carries a ticker at two dates, as this one does."""
    rows = [dict(_ROW, ticker=t) for t in ("T3", "T1", "T2")] + [
        dict(_ROW, ticker="T1", snapshot_date="2026-05-01")
    ]
    _, calls = _run_export(monkeypatch, tmp_path, rows, len(rows))
    sent = [(r["ticker"], r["snapshot_date"]) for r in calls[0]["params"]["payload"]]
    assert sent == [
        ("T1", "2026-05-01"),
        ("T1", "2026-06-01"),
        ("T2", "2026-06-01"),
        ("T3", "2026-06-01"),
    ]
