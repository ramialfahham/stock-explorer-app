"""Tests for card metric formulas."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from metric_formulas import (  # noqa: E402
    compute_card_metrics_from_raw,
    operating_margin_ttm_pct,
    pct_drift,
    reference_operating_margin_info,
)


def test_compute_card_metrics_from_raw() -> None:
    row = {
        "info_forward_pe": 20.0,
        "info_revenue_growth": 0.1,
        "info_net_debt": 100.0,
        "info_ebitda": 50.0,
        "stmt_free_cash_flow": 30.0,
        "stmt_total_revenue": 200.0,
        "qtr_operating_income_0": 25.0,
        "qtr_operating_income_1": 25.0,
        "qtr_operating_income_2": 25.0,
        "qtr_operating_income_3": 25.0,
        "qtr_total_revenue_0": 100.0,
        "qtr_total_revenue_1": 100.0,
        "qtr_total_revenue_2": 100.0,
        "qtr_total_revenue_3": 100.0,
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


def test_operating_margin_ttm_pct() -> None:
    row = {
        "qtr_operating_income_0": 100.0,
        "qtr_operating_income_1": 80.0,
        "qtr_operating_income_2": 90.0,
        "qtr_operating_income_3": 70.0,
        "qtr_total_revenue_0": 500.0,
        "qtr_total_revenue_1": 480.0,
        "qtr_total_revenue_2": 490.0,
        "qtr_total_revenue_3": 470.0,
    }
    assert operating_margin_ttm_pct(row) == 20.0


def test_operating_margin_ttm_pct_requires_four_quarters() -> None:
    row = {
        "qtr_operating_income_0": 100.0,
        "qtr_operating_income_1": 80.0,
        "qtr_total_revenue_0": 500.0,
        "qtr_total_revenue_1": 480.0,
    }
    assert operating_margin_ttm_pct(row) is None


def test_reference_operating_margin_info() -> None:
    assert reference_operating_margin_info({"operatingMargins": 0.032}) == 3.2
