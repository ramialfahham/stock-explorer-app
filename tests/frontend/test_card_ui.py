"""Card HTML helpers."""

from __future__ import annotations

from card_copy import ALL_METRICS, BENCHMARK_METRICS  # noqa: E402
from card_ui import (  # noqa: E402
    _company_about_body_html,
    _company_summary_html,
    _health_block_html,
    build_card_html,
    build_learn_panel_body_html,
)


def test_company_summary_truncated_is_preview_only_no_toggle() -> None:
    """Slice 6c: the card face shows only the preview now — the full text and its
    "Read full description" toggle moved into the one learn panel."""
    card = {
        "business_summary": " ".join(f"word{i}" for i in range(30)),
    }
    html = _company_summary_html(card)
    assert "Read full description" not in html
    assert "<details" not in html
    assert "ss-company-summary" in html


def test_company_summary_short_has_no_toggle() -> None:
    card = {"business_summary": "Short blurb only."}
    html = _company_summary_html(card)
    assert "Read full description" not in html
    assert "<details" not in html


def test_company_about_body_present_only_when_truncated() -> None:
    truncated = {"business_summary": " ".join(f"word{i}" for i in range(30))}
    short = {"business_summary": "Short blurb only."}
    assert "About this company" in _company_about_body_html(truncated)
    assert _company_about_body_html(short) == ""


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


def test_build_card_never_contains_a_nested_disclosure() -> None:
    """Slice 6c: the ~11 prior separate disclosures (company description, the learn
    panel, one <details> per metric) collapse to a single st.expander rendered outside
    build_card_html — its own HTML output should contain zero <details> elements."""
    html = build_card_html(_card_with_all_metrics("operating"))
    assert "<details" not in html


def test_health_block_present_with_full_assessment() -> None:
    card = _card_with_all_metrics("operating")
    card["health_verdict"] = "green"
    card["ai_read"] = "This company shows healthy leverage and margins on these figures."
    html = _health_block_html(card)
    assert "🟢" in html
    assert "Sturdy" in html
    assert "healthy leverage" in html


def test_health_block_absent_without_matching_assessment() -> None:
    """No card_assessments row matched (pipeline lag) -> omit entirely, never a
    placeholder or a "not yet assessed" line."""
    card = _card_with_all_metrics("operating")
    assert _health_block_html(card) == ""
    assert "ss-health-block" not in build_card_html(card)


def test_health_block_shows_badge_without_ai_read_when_null() -> None:
    card = _card_with_all_metrics("operating")
    card["health_verdict"] = "yellow"
    card["ai_read"] = None
    html = _health_block_html(card)
    assert "🟡" in html
    assert "Mixed" in html
    assert "ss-ai-read" not in html


def test_health_block_ignores_unrecognized_verdict_token() -> None:
    card = _card_with_all_metrics("operating")
    card["health_verdict"] = "unknown-future-token"
    card["ai_read"] = "some text"
    assert _health_block_html(card) == ""


def test_learn_panel_body_flattens_metric_definitions_no_nested_details() -> None:
    """Per-metric explanations used to be individually-toggled <details> — Slice 6c
    flattens them into one always-visible-once-the-panel-is-open list."""
    html = build_learn_panel_body_html(_card_with_all_metrics("operating"))
    assert "<details" not in html
    assert "ss-metric-learn-item" in html
    assert "ss-metric-learn-heading" in html


def test_learn_panel_body_includes_about_section_when_truncated() -> None:
    card = _card_with_all_metrics("operating")
    card["business_summary"] = " ".join(f"word{i}" for i in range(30))
    html = build_learn_panel_body_html(card)
    assert "About this company" in html


def test_benchmark_indicator_shows_words_not_arrow_glyphs() -> None:
    card = _card_with_all_metrics("operating")
    html = build_card_html(card)
    for glyph in ("↑", "↓", "→"):
        assert glyph not in html


def test_learn_panel_compare_section_shows_words_not_arrow_glyphs() -> None:
    """The compare section (incl. its median primer) must not reference the retired
    arrow-glyph legend now that per-metric lines show words instead."""
    card = _card_with_all_metrics("operating")
    card["sector_peer_count"] = 20
    for metric, median_key, _direction in BENCHMARK_METRICS:
        card[median_key] = 1.0  # every metric value is 1.5 -> resolves to "above"
    html = build_learn_panel_body_html(card)
    assert "How we compare to similar companies" in html
    assert "Higher than sector median" in html
    for glyph in ("↑", "↓", "→"):
        assert glyph not in html
