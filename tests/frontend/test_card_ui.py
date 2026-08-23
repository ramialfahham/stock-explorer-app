"""Card HTML helpers."""

from __future__ import annotations

from card_copy import ALL_METRICS, BENCHMARK_METRICS, _BY_ID, metrics_for_card  # noqa: E402
from card_ui import (  # noqa: E402
    _company_summary_html,
    _health_block_html,
    build_card_html,
    build_learn_panel_body_html,
)


def test_company_summary_truncated_gets_inline_read_more_toggle() -> None:
    """The full description now expands inline on the card face, right where the
    truncated preview ends — not at the bottom of a separate learn panel."""
    card = {
        "business_summary": " ".join(f"word{i}" for i in range(30)),
    }
    html = _company_summary_html(card)
    assert "<details" in html
    assert "Read more" in html
    assert "Show less" in html
    assert "ss-company-summary-full" in html


def test_company_summary_short_has_no_toggle() -> None:
    """Nothing more to reveal when the preview already shows the whole thing."""
    card = {"business_summary": "Short blurb only."}
    html = _company_summary_html(card)
    assert "<details" not in html
    assert "Read more" not in html


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


def _card_with_benchmark_range(**overrides) -> dict:
    card = _card_with_all_metrics("operating")
    card["sector_peer_count"] = 20
    card["ebit_margin_pct"] = 21.5
    card["sector_min_ebit_margin_pct"] = 4.1
    card["sector_median_ebit_margin_pct"] = 15.3
    card["sector_max_ebit_margin_pct"] = 38.9
    card.update(overrides)
    return card


def test_build_card_shows_range_mark_when_benchmark_available() -> None:
    html = build_card_html(_card_with_benchmark_range())
    assert "ss-metric-range" in html
    assert "ss-metric-range-marker" in html
    assert "min 4.1%" in html
    assert "max 38.9%" in html
    assert "median 15.3%" in html


def test_range_mark_direction_cue_shown_for_net_debt() -> None:
    """net_debt_to_ebitda is a rightward-marker-is-bad-news metric -- the gloss line must
    say so, since the mark itself (a bar-and-marker) otherwise reads as "further right =
    better" the way it correctly does for the 3 higher-better metrics."""
    card = _card_with_all_metrics("operating")
    card["sector_peer_count"] = 20
    card["net_debt_to_ebitda"] = 3.9
    card["sector_min_net_debt_to_ebitda"] = -0.4
    card["sector_median_net_debt_to_ebitda"] = 1.9
    card["sector_max_net_debt_to_ebitda"] = 4.2
    html = build_card_html(card)
    assert "Lower is better." in html


def test_range_mark_direction_cue_absent_for_higher_better_metric() -> None:
    html = build_card_html(_card_with_benchmark_range())  # ebit_margin_pct, higher_better
    assert "Lower is better." not in html


def test_range_mark_direction_cue_shown_for_forward_pe() -> None:
    """forward_pe is also catalogued lower_better -- the cue applies uniformly to both
    lower_better metrics. This is a ceteris-paribus statement about the metric's own axis
    (a lower P/E is more attractively priced for the same growth/quality profile), not a
    health judgment; it doesn't conflict with assessment_rules.py excluding P/E from the
    health verdict, which is about not letting P/E alone drive a composite score. The
    caveat that P/E should be read alongside growth belongs in the metric's deep-dive
    explanation, not a hedge in this short gloss line (owner decision)."""
    card = _card_with_all_metrics("operating")
    card["sector_peer_count"] = 20
    card["forward_pe"] = 45.0
    card["sector_min_forward_pe"] = 10.0
    card["sector_median_forward_pe"] = 18.0
    card["sector_max_forward_pe"] = 150.0
    html = build_card_html(card)
    assert "Lower is better." in html


def test_range_mark_direction_cue_suppressed_for_net_cash() -> None:
    """A negative net_debt_to_ebitda already renders the value-aware "Net cash" gloss,
    which states the favorable read directly -- restating the axis on top of it is
    redundant, not informative."""
    card = _card_with_all_metrics("operating")
    card["sector_peer_count"] = 20
    card["net_debt_to_ebitda"] = -1.2
    card["sector_min_net_debt_to_ebitda"] = -2.0
    card["sector_median_net_debt_to_ebitda"] = 1.9
    card["sector_max_net_debt_to_ebitda"] = 4.2
    html = build_card_html(card)
    assert "Net cash" in html
    assert "Lower is better." not in html


def test_direction_cue_catalogue_assumptions_still_hold() -> None:
    """_direction_cue() derives which metrics get ". Lower is better." straight from the
    catalogue's own `direction` field (currently: forward_pe and net_debt_to_ebitda). Pin
    the specific values here: if a future metric_catalogue.csv edit reclassifies either
    metric's direction, or changes the language this docstring's reasoning leans on, this
    test breaks and forces that reasoning to be re-checked against the new catalogue
    content -- instead of the code's comments silently drifting out of sync with the
    single source of truth they're supposed to stay consistent with
    (docs/data_contract.md's "Card metrics -- dbt formulas" section)."""
    assert _BY_ID["forward_pe"]["direction"] == "lower_better"
    assert "growth" in _BY_ID["forward_pe"]["interpretation"].lower()
    assert _BY_ID["net_debt_to_ebitda"]["direction"] == "lower_better"
    assert "safer" in _BY_ID["net_debt_to_ebitda"]["interpretation"].lower()


def test_range_mark_direction_cue_absent_when_range_mark_itself_unavailable() -> None:
    """No mark to disambiguate below the peer threshold -> no cue either, same
    availability check as the range mark."""
    card = _card_with_all_metrics("operating")
    card["sector_peer_count"] = 7
    card["net_debt_to_ebitda"] = 3.9
    card["sector_min_net_debt_to_ebitda"] = -0.4
    card["sector_median_net_debt_to_ebitda"] = 1.9
    card["sector_max_net_debt_to_ebitda"] = 4.2
    html = build_card_html(card)
    assert "Lower is better." not in html


def test_build_card_omits_range_mark_below_peer_threshold() -> None:
    html = build_card_html(_card_with_benchmark_range(sector_peer_count=7))
    assert "ss-metric-range" not in html


def test_build_card_range_mark_replaces_old_text_indicator() -> None:
    """The card face no longer shows the old inline "Higher/Lower than sector median"
    text at all -- that class only survives in the separate learn-panel recap list."""
    html = build_card_html(_card_with_benchmark_range())
    assert "ss-bench-indicator" not in html
    assert "Higher than sector median" not in html


def test_range_mark_bar_end_reaches_track_end_not_shortened() -> None:
    """Regression: the end bar segment anchors its outer edge via `right:0` (in CSS) and
    only pulls its inner edge in from the median with `left:calc(...+ 2px)` -- it must not
    set its own `width`, which previously shrank the segment from its outer edge instead,
    leaving it 2px short of the true sector-max position (cto-reviewer round 1)."""
    html = build_card_html(_card_with_benchmark_range())
    assert 'class="ss-metric-range-bar ss-metric-range-bar-end" style="left:calc(' in html
    assert "% + 2px)\"></div>" in html


def test_range_mark_median_label_position_clamped_near_track_edges() -> None:
    """A median close to its sector's min or max (realistic for skewed data, e.g. a fat-
    tailed forward P/E) must not push the label's centered text past the track bounds
    (cto-reviewer round 1: nothing previously bounded label-vs-track-edge proximity)."""
    card = _card_with_benchmark_range(
        sector_min_ebit_margin_pct=2.0,
        sector_median_ebit_margin_pct=37.5,
        sector_max_ebit_margin_pct=38.0,
        ebit_margin_pct=30.0,
    )
    html = build_card_html(card)
    assert "left:clamp(3rem," in html


def test_build_card_range_mark_omitted_for_degenerate_sector() -> None:
    html = build_card_html(
        _card_with_benchmark_range(
            ebit_margin_pct=20.0,
            sector_min_ebit_margin_pct=20.0,
            sector_median_ebit_margin_pct=20.0,
            sector_max_ebit_margin_pct=20.0,
        )
    )
    assert "ss-metric-range" not in html


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


def test_build_card_has_exactly_one_disclosure_for_truncated_description() -> None:
    """build_card_html's own output contains at most one <details> — the company
    description's inline toggle, when the preview is truncated. The learn panel's own
    per-metric disclosures render separately (render_learn_panel is not part of this
    function's return value), so they never show up here."""
    card = _card_with_all_metrics("operating")
    card["business_summary"] = " ".join(f"word{i}" for i in range(30))
    html = build_card_html(card)
    assert html.count("<details") == 1


def test_build_card_has_no_disclosure_for_short_description() -> None:
    card = _card_with_all_metrics("operating")
    card["business_summary"] = "Short blurb only."
    html = build_card_html(card)
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


def test_learn_panel_body_gives_each_metric_its_own_disclosure() -> None:
    """Each metric's full explanation sits behind its own Read more/Show less — not
    concatenated into one always-visible wall of text. Analogy and heading stay
    unconditionally visible; only the long paragraph is behind the toggle."""
    card = _card_with_all_metrics("operating")
    html = build_learn_panel_body_html(card)
    metric_count = len(metrics_for_card(card))
    assert html.count("<details") == metric_count
    assert "ss-metric-learn-item" in html
    assert "ss-metric-learn-heading" in html
    assert "ss-metric-analogy" in html


def test_learn_panel_body_drops_redundant_gloss_line() -> None:
    """ss-metric-gloss-inline restated the label in flatter language once the full
    paragraph moved behind its own toggle — dropped, not just hidden."""
    html = build_learn_panel_body_html(_card_with_all_metrics("operating"))
    assert "ss-metric-gloss-inline" not in html


def test_learn_panel_body_never_includes_company_description() -> None:
    """About-this-company has its own inline toggle on the card face now — it must never
    render inside the learn panel, truncated or not."""
    card = _card_with_all_metrics("operating")
    card["business_summary"] = " ".join(f"word{i}" for i in range(30))
    html = build_learn_panel_body_html(card)
    assert "About this company" not in html


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
