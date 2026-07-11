"""Offline test for the assessment generator (Slice 5a) — no Supabase, no network."""

from __future__ import annotations

from pathlib import Path

import duckdb

import generate_assessments as gen
from assessment_rules import VERDICTS

_ROWS = [
    # operating, green (older snapshot)
    {"market_code": "us_sp500", "ticker": "OPX", "company_type": "operating", "snapshot_date": "2026-06-01",
     "net_debt_to_ebitda": 1.1, "ebit_margin_pct": 24.0, "fcf_margin_pct": 16.0},
    # SAME ticker, later snapshot, now red (fcf negative) -> dedupe must keep this one
    {"market_code": "us_sp500", "ticker": "OPX", "company_type": "operating", "snapshot_date": "2026-07-01",
     "net_debt_to_ebitda": 1.1, "ebit_margin_pct": 24.0, "fcf_margin_pct": -3.0},
    # financial, green
    {"market_code": "us_sp500", "ticker": "FINX", "company_type": "financial", "snapshot_date": "2026-07-01",
     "statement_roe_pct": 13.0, "net_margin_pct": 30.0, "roa_pct": 1.2},
    # pre_revenue, red (short runway)
    {"market_code": "us_sp500", "ticker": "PREX", "company_type": "pre_revenue", "snapshot_date": "2026-07-01",
     "cash_runway_months": 8.0, "net_cash_to_market_cap": 0.1, "working_capital": -5.0e7},
]


def _make_mart(path: Path, rows: list[dict]) -> None:
    text_cols = {"market_code", "ticker", "company_type", "snapshot_date"}
    defs = ", ".join(
        f"{c} VARCHAR" if c in text_cols else f"{c} DOUBLE"
        for c in gen.ASSESSMENT_INPUT_COLUMNS
    )
    con = duckdb.connect(str(path))
    con.execute("create schema if not exists marts")
    con.execute(f"create table marts.mart_stock_cards ({defs})")
    for row in rows:
        cols = list(row.keys())
        placeholders = ", ".join("?" for _ in cols)
        con.execute(
            f"insert into marts.mart_stock_cards ({', '.join(cols)}) values ({placeholders})",
            [row[c] for c in cols],
        )
    con.close()


def test_build_records_dedupes_and_assigns_verdicts(tmp_path: Path) -> None:
    db = tmp_path / "mart.duckdb"
    _make_mart(db, _ROWS)
    records = gen.build_assessment_records(gen._load_mart_rows(db))

    by_ticker = {r["ticker"]: r for r in records}
    assert set(by_ticker) == {"OPX", "FINX", "PREX"}   # one record per (market, ticker)
    assert len(records) == 3                            # coverage: every eligible card gets a verdict

    # dedupe kept the latest snapshot (which flipped OPX to red)
    assert by_ticker["OPX"]["snapshot_date"] == "2026-07-01"
    assert by_ticker["OPX"]["health_verdict"] == "red"
    assert by_ticker["FINX"]["health_verdict"] == "green"
    assert by_ticker["PREX"]["health_verdict"] == "red"

    for rec in records:
        assert rec["health_verdict"] in VERDICTS
        assert "ai_read" not in rec and "read_model" not in rec  # 5a never writes/clobbers the read
        assert len(rec["input_hash"]) == 64
        assert set(rec) == {
            "market_code", "ticker", "company_type", "health_verdict",
            "input_hash", "snapshot_date", "generated_at",
        }


def test_dry_run_needs_no_credentials(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.delenv("SUPABASE_URL", raising=False)
    monkeypatch.delenv("SUPABASE_SERVICE_ROLE_KEY", raising=False)
    db = tmp_path / "mart.duckdb"
    _make_mart(db, _ROWS)
    assert gen.main(["--duckdb-path", str(db), "--dry-run"]) == 0


def test_missing_duckdb_returns_error() -> None:
    assert gen.main(["--duckdb-path", "/no/such/mart.duckdb", "--dry-run"]) == 1
