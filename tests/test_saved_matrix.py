"""Saved tab comparison matrix."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FRONTEND = ROOT / "frontend"
sys.path.insert(0, str(FRONTEND))

from saved_matrix import build_saved_matrix_html, saved_card_options  # noqa: E402


def _card(ticker: str, **overrides: object) -> dict:
    base = {
        "market_code": "us_sp500",
        "ticker": ticker,
        "company_name": f"Company {ticker}",
        "sector": "Technology",
        "forward_pe": 20.0,
        "ebit_margin_pct": 15.0,
        "revenue_growth_yoy_pct": 8.0,
        "net_debt_to_ebitda": 1.5,
        "fcf_margin_pct": 12.0,
    }
    base.update(overrides)
    return base


def test_build_saved_matrix_includes_tickers_and_metrics() -> None:
    cards = [_card("AAPL"), _card("MSFT", market_code="us_sp500")]
    html_out = build_saved_matrix_html(cards)
    assert "AAPL" in html_out
    assert "MSFT" in html_out
    assert "Forward P/E" in html_out
    assert "FCF margin" in html_out
    assert "ss-saved-matrix" in html_out


def test_saved_card_options_labels() -> None:
    cards = [_card("AAPL")]
    options = saved_card_options(cards)
    assert len(options) == 1
    assert "AAPL" in options[0][0]
    assert options[0][1] == "us_sp500::AAPL"


def test_build_saved_matrix_empty_returns_empty_string() -> None:
    assert build_saved_matrix_html([]) == ""
