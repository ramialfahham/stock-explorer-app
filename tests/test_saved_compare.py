"""Tests for Saved compare-two table."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "frontend"))

from saved_compare import build_compare_two_html, compare_partner_options  # noqa: E402


def _card(ticker: str, **metrics: float) -> dict:
    base = {
        "market_code": "us_sp500",
        "ticker": ticker,
        "company_name": f"Company {ticker}",
        "forward_pe": 20.0,
        "ebit_margin_pct": 15.0,
        "revenue_growth_yoy_pct": 5.0,
        "net_debt_to_ebitda": 2.0,
        "fcf_margin_pct": 8.0,
    }
    base.update(metrics)
    return base


def test_build_compare_two_includes_both_tickers() -> None:
    html_out = build_compare_two_html(_card("AAPL"), _card("MSFT"))
    assert "AAPL" in html_out
    assert "MSFT" in html_out
    assert "ss-compare-two" in html_out
    assert "Forward P/E" in html_out


def test_compare_partner_options_excludes_focus() -> None:
    cards = [_card("AAPL"), _card("MSFT"), _card("GOOG")]
    options = compare_partner_options(cards, cards[0])
    assert len(options) == 2
    tickers_in_keys = [key.split("::", 1)[1] for _, key in options]
    assert "AAPL" not in tickers_in_keys
