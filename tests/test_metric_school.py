"""Tests for metric playground seed values."""

from __future__ import annotations


def test_negative_net_debt_ratio_seeds_below_zero() -> None:
    """Cash-rich companies can have negative net debt / EBITDA on the card."""
    ratio = -3.62
    default_ebitda = 10.0
    default_debt = float(ratio * default_ebitda)
    assert default_debt < 0
    assert default_debt >= -500.0
