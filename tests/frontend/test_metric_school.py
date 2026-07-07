"""Tests for metric playground seed values."""

from __future__ import annotations

from metric_school import (  # noqa: E402
    seed_ebit_margin_playground,
    seed_fcf_margin_playground,
    seed_net_debt_playground,
    seed_revenue_growth_playground,
)


def test_negative_net_debt_ratio_seeds_within_bounds() -> None:
    """Cash-rich companies can have negative net debt / EBITDA on the card."""
    debt, ebitda = seed_net_debt_playground({"net_debt_to_ebitda": -3.62})
    assert debt < 0
    assert debt >= -500.0
    assert ebitda >= 0.1


def test_extreme_negative_net_debt_ratio_clamps_to_min() -> None:
    debt, _ebitda = seed_net_debt_playground({"net_debt_to_ebitda": -100.0})
    assert debt == -500.0


def test_extreme_negative_ebit_margin_clamps_operating_profit() -> None:
    """Deep-loss companies can have margins below widget min (e.g. -601%)."""
    _revenue, operating = seed_ebit_margin_playground({"ebit_margin_pct": -601.5})
    assert operating == -500.0


def test_extreme_positive_ebit_margin_clamps_operating_profit() -> None:
    _revenue, operating = seed_ebit_margin_playground({"ebit_margin_pct": 800.0})
    assert operating == 500.0


def test_extreme_negative_fcf_margin_clamps_cash_flow() -> None:
    _revenue, fcf = seed_fcf_margin_playground({"fcf_margin_pct": -601.5})
    assert fcf == -500.0


def test_extreme_negative_revenue_growth_clamps_current_revenue() -> None:
    prior, current = seed_revenue_growth_playground({"revenue_growth_yoy_pct": -150.0})
    assert prior == 100.0
    assert current == 0.0
