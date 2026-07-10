"""Card HTML helpers."""

from __future__ import annotations

from card_copy import ALL_METRICS  # noqa: E402
from card_ui import _company_summary_html, build_card_html  # noqa: E402


def test_company_summary_truncated_has_read_and_show_less() -> None:
    card = {
        "business_summary": " ".join(f"word{i}" for i in range(30)),
    }
    html = _company_summary_html(card)
    assert "Read full description" in html
    assert "Show less" in html
    assert "ss-disclosure-preview" in html
    assert "ss-company-about-wrap" in html
    assert html.index("ss-disclosure-preview") < html.index("ss-disclosure-toggle")


def test_company_summary_short_has_no_toggle() -> None:
    card = {"business_summary": "Short blurb only."}
    html = _company_summary_html(card)
    assert "Read full description" not in html
    assert "<details" not in html


def _card_with_all_metrics(company_type: str) -> dict:
    card = {
        "company_name": "Test Co",
        "ticker": "TST",
        "market_code": "us_sp500",
        "sector": "Technology",
        "currency": "USD",
        "company_type": company_type,
    }
    for metric in ALL_METRICS:
        card[metric] = 1.5
    return card


def test_build_card_operating_shows_new_operating_metrics() -> None:
    html = build_card_html(_card_with_all_metrics("operating"))
    for label in ("Debt / equity", "Current ratio", "Return on equity"):
        assert label in html


def test_build_card_financial_omits_bank_inapplicable_no_dash() -> None:
    html = build_card_html(_card_with_all_metrics("financial"))
    for label in ("Debt / equity", "Current ratio"):
        assert label not in html  # honestly blank for banks -> omitted
    assert 'ss-metric-value">—<' not in html  # never an un-valued em-dash cell


def test_build_card_financial_shows_bank_metrics() -> None:
    html = build_card_html(_card_with_all_metrics("financial"))
    for label in ("Price / tangible book", "Net margin", "Return on assets", "Dividend yield"):
        assert label in html


def test_build_card_pre_revenue_shows_survival_metrics_no_dash() -> None:
    html = build_card_html(_card_with_all_metrics("pre_revenue"))
    for label in ("Net cash vs price", "Working capital", "Cash runway", "Cash burn (monthly)"):
        assert label in html
    for label in ("Forward P/E", "Operating margin", "Return on equity"):
        assert label not in html  # operating/financial metrics omitted for pre-revenue
    assert 'ss-metric-value">—<' not in html
    assert 'ss-metric-value">$' in html  # currency_compact metrics render with the card's currency symbol
