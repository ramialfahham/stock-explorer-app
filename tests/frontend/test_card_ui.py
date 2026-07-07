"""Card HTML helpers."""

from __future__ import annotations

from card_ui import _company_summary_html  # noqa: E402


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
