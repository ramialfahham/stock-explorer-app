"""Tests for card metric formulas."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from metric_formulas import compute_card_metrics_from_raw, pct_drift  # noqa: E402


def test_compute_card_metrics_from_raw() -> None:
    row = {
        "info_forward_pe": 20.0,
        "info_operating_margins": 0.25,
        "info_revenue_growth": 0.1,
        "info_net_debt": 100.0,
        "info_ebitda": 50.0,
        "stmt_free_cash_flow": 30.0,
        "stmt_total_revenue": 200.0,
    }
    metrics = compute_card_metrics_from_raw(row)
    assert metrics["forward_pe"] == 20.0
    assert metrics["ebit_margin_pct"] == 25.0
    assert metrics["revenue_growth_yoy_pct"] == 10.0
    assert metrics["net_debt_to_ebitda"] == 2.0
    assert metrics["fcf_margin_pct"] == 15.0


def test_pct_drift() -> None:
    assert pct_drift(110.0, 100.0) == 10.0
    assert pct_drift(None, 100.0) is None
