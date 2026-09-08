"""Tests for the metric audit (Phase 2: no Python formula mirror).

Covers the offline path (CI smoke) and the drift helper. The live path rebuilds metrics through
dbt on fresh raw and is exercised by the pipeline, not unit tests (it needs network + a dbt run).
"""

from __future__ import annotations

import json
import sys

import duckdb

import audit_mart_vs_yfinance as audit  # noqa: E402


def _make_mart_duckdb(path: Path) -> None:
    con = duckdb.connect(str(path))
    text_cols = {"market_code", "ticker", "company_name", "sector", "snapshot_date", "business_summary"}
    defs = ", ".join(
        f"{c} VARCHAR" if c in text_cols
        else (f"{c} BOOLEAN" if c == "is_card_eligible" else f"{c} DOUBLE")
        for c in audit.MART_COLUMNS
    )
    con.execute("create schema if not exists marts")
    con.execute(f"create table marts.mart_stock_cards ({defs})")
    con.execute(
        "insert into marts.mart_stock_cards values "
        "('us_sp500','AAA','Co A','Technology','2026-06-01','A summary',20.0,25.0,8.0,0.5,10.0,2.5,true)"
    )
    con.execute(
        "insert into marts.mart_stock_cards values "
        "('us_sp500','BBB','Co B','Energy','2026-06-01','',18.0,15.0,5.0,1.2,9.0,4.1,true)"
    )
    con.close()


def test_no_metric_formulas_dependency() -> None:
    # The Python formula mirror is gone; the audit must import without it.
    assert "metric_formulas" not in sys.modules
    assert hasattr(audit, "main")


def test_pct_drift() -> None:
    assert audit.pct_drift(110.0, 100.0) == 10.0
    assert audit.pct_drift(90.0, 100.0) == -10.0
    assert audit.pct_drift(None, 100.0) is None
    assert audit.pct_drift(100.0, 0.0) is None


def test_offline_audit_runs(tmp_path: Path) -> None:
    db = tmp_path / "mart.duckdb"
    _make_mart_duckdb(db)
    out_dir = tmp_path / "audit"
    rc = audit.main(
        ["--source", "duckdb", "--duckdb-path", str(db), "--offline",
         "--sample-size", "5", "--output-dir", str(out_dir)]
    )
    assert rc == 0
    json_files = list(out_dir.glob("metric_audit_*.json"))
    assert json_files
    data = json.loads(json_files[0].read_text(encoding="utf-8"))
    assert data["summary"]["rows"] == 2
    row = data["rows"][0]
    assert "mart_forward_pe" in row
    # Offline path does no live fetch / dbt rebuild → no drift columns.
    assert "drift_pct_forward_pe" not in row
