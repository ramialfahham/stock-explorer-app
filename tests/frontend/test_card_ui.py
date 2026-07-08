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
