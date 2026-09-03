"""Card HTML helpers."""

from __future__ import annotations

from assessment_rules import VERDICT_MEANING  # noqa: E402

from card_copy import (  # noqa: E402
    ALL_METRICS,
    BENCHMARK_METRICS,
    VERDICT_BADGE_LABEL,
    VERDICT_FALLBACK_READ,
    _BY_ID,
    metric_perspective_label,
    metrics_for_card,
)
from card_ui import (  # noqa: E402
    BLOCK_LABEL_ASSESSMENT,
    BLOCK_LABEL_DESCRIPTION,
    BLOCK_LABEL_VERDICT_MEANING,
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


def test_assessment_and_description_are_separate_labelled_blocks() -> None:
    """The card face must not run the AI assessment and the company's own description
    together as one wall of text — a reader cannot tell model-written prose from the
    company's words. Each gets its own wrapper and a label naming where it came from."""
    card = {
        "company_name": "Test Co",
        "ticker": "TST",
        "market_code": "us_sp500",
        "health_verdict": "green",
        "ai_read": "Turns sales into profit at a healthy rate.",
        "business_summary": "Test Co makes things and sells them worldwide.",
    }
    health = _health_block_html(card)
    summary = _company_summary_html(card)

    assert '<div class="ss-health-block">' in health
    assert BLOCK_LABEL_ASSESSMENT in health
    assert '<div class="ss-company-block">' in summary
    assert BLOCK_LABEL_DESCRIPTION in summary
    # Each label belongs to exactly one block — swapping them would defeat the point.
    assert BLOCK_LABEL_DESCRIPTION not in health
    assert BLOCK_LABEL_ASSESSMENT not in summary


def test_assessment_label_says_ai_written_not_summary() -> None:
    """Owner-chosen wording (§6). "Summary" would misdescribe it: the read is written
    from the card's figures, it does not condense a longer text. Pinned so a later
    tidy-up cannot quietly soften it back."""
    assert BLOCK_LABEL_ASSESSMENT == "What the numbers say · AI-written"
    assert BLOCK_LABEL_DESCRIPTION == "About the company"


def test_description_block_label_present_whether_or_not_truncated() -> None:
    """The wrapper is what separates this block visually, so it cannot appear only on
    the truncated path — a short description would otherwise lose its label and merge
    back into the assessment above it."""
    long_card = {"business_summary": " ".join(f"word{i}" for i in range(30))}
    short_card = {"business_summary": "Short blurb only."}
    for card in (long_card, short_card):
        html = _company_summary_html(card)
        assert '<div class="ss-company-block">' in html
        assert BLOCK_LABEL_DESCRIPTION in html


def test_no_description_renders_nothing_at_all() -> None:
    """No description means no empty labelled box announcing its own absence."""
    assert _company_summary_html({"business_summary": None}) == ""
    assert _company_summary_html({}) == ""


def test_no_assessment_renders_nothing_at_all() -> None:
    """Same for the assessment: a card with no matching card_assessments row shows no
    panel, not a labelled empty one."""
    assert _health_block_html({"company_name": "Test Co"}) == ""


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
    """New structure: a numbers row (bare values, no "min"/"max" text prefix) above the
    bar, a words row ("min"/"median"/"max") below it -- see docs/ui/card_metric_cell.md."""
    html = build_card_html(_card_with_benchmark_range())
    assert "ss-metric-range" in html
    assert "ss-metric-range-marker" in html
    assert 'class="ss-metric-range-number" style="left:0%">4.1%<' in html
    assert 'class="ss-metric-range-number" style="left:100%">38.9%<' in html
    assert "15.3%" in html  # median value, position is clamp()'d -- checked separately
    assert 'class="ss-metric-range-word" style="left:0%">min<' in html
    assert 'class="ss-metric-range-word" style="left:100%">max<' in html
    assert ">median<" in html


def test_range_mark_min_median_max_share_identical_alignment_rule() -> None:
    """Regression: an earlier draft edge-anchored min/max (`left:0`/`right:0`-style,
    text growing outward from the track's ends) while median centered on its own point
    -- inconsistent, and the max label drifted away from its tick. All three points must
    resolve through the same class (`.ss-metric-range-number` / `-word`, both
    `transform: translateX(-50%)` in CSS) with only their `left` position differing, so
    they read as one consistent reference frame instead of three different rules."""
    html = build_card_html(_card_with_benchmark_range())
    assert html.count('class="ss-metric-range-number"') == 3  # min, median, max -- one class
    assert html.count('class="ss-metric-range-word"') == 3
    assert "ss-metric-range-min" not in html  # old per-role classes are gone
    assert "ss-metric-range-max" not in html
    assert "ss-metric-range-median-label" not in html


def test_range_mark_direction_cue_shown_for_net_debt() -> None:
    """net_debt_to_ebitda is a rightward-marker-is-bad-news metric -- the gloss line must
    say so, since the mark itself (a bar-and-marker) otherwise reads as "further right =
    better" the way it correctly does for the other, higher-better benchmarked metrics. The cue's full
    branch coverage (every catalogued direction, the net-cash suppression) lives in
    test_card_copy.py against metric_gloss() directly; this is an integration smoke
    check that build_card_html() actually renders what that function returns."""
    card = _card_with_all_metrics("operating")
    card["sector_peer_count"] = 20
    card["net_debt_to_ebitda"] = 3.9
    card["sector_min_net_debt_to_ebitda"] = -0.4
    card["sector_median_net_debt_to_ebitda"] = 1.9
    card["sector_max_net_debt_to_ebitda"] = 4.2
    html = build_card_html(card)
    assert "Lower is better." in html


def test_range_mark_direction_cue_matches_higher_better_metric() -> None:
    """ebit_margin_pct is catalogued higher_better -- its own gloss line must say
    "Higher is better.", not "Lower". (Other lower_better metrics on the same card get
    their own "Lower is better." cue now that the rule is universal -- see
    test_card_copy.py -- so this checks the metric's own composed gloss line, not
    whole-page absence of that phrase.)"""
    card = _card_with_benchmark_range()  # ebit_margin_pct, higher_better
    html = build_card_html(card)
    assert "Operating profit as share of sales (TTM). Higher is better." in html
    assert "Operating profit as share of sales (TTM). Lower is better." not in html


def test_range_mark_direction_cue_suppressed_for_net_cash() -> None:
    """A negative net_debt_to_ebitda already renders the value-aware "Net cash" gloss,
    which states the favorable read directly -- restating the axis on top of it is
    redundant, not informative. Checks net_debt_to_ebitda's own composed gloss line, not
    whole-page absence, since other lower_better metrics on this all-metrics card
    legitimately show "Lower is better." on their own rows now."""
    card = _card_with_all_metrics("operating")
    card["sector_peer_count"] = 20
    card["net_debt_to_ebitda"] = -1.2
    card["sector_min_net_debt_to_ebitda"] = -2.0
    card["sector_median_net_debt_to_ebitda"] = 1.9
    card["sector_max_net_debt_to_ebitda"] = 4.2
    html = build_card_html(card)
    assert "Net cash" in html
    # nothing appended after the value-aware gloss -- </p> immediately follows it
    assert "Net cash: cash on hand exceeds debt</p>" in html


def test_direction_cue_catalogue_assumptions_still_hold() -> None:
    """metric_direction()/metric_gloss() (frontend/card_copy.py) derive the ". Higher/
    Lower is better." suffix straight from the catalogue's own `direction` field, for
    every metric that has one. Pin the specific values here for the two metrics this
    file's other tests exercise: if a future metric_catalogue.csv edit reclassifies
    either metric's direction, or changes the language this docstring's reasoning leans
    on, this test breaks and forces that reasoning to be re-checked against the new
    catalogue content -- instead of the code's comments silently drifting out of sync
    with the single source of truth they're supposed to stay consistent with
    (docs/data_contract.md's "Card metrics -- dbt formulas" section)."""
    # forward_pe used to be the second lower_better metric checked here. It was dropped from
    # the catalogue (it carries the share price, which a twice-monthly pipeline
    # cannot keep current), so burn_rate_monthly is now the other one.
    assert _BY_ID["burn_rate_monthly"]["direction"] == "lower_better"
    assert _BY_ID["net_debt_to_ebitda"]["direction"] == "lower_better"
    assert "safer" in _BY_ID["net_debt_to_ebitda"]["interpretation"].lower()


def test_range_mark_direction_cue_shown_even_when_range_mark_itself_unavailable() -> None:
    """Below the peer threshold the range MARK is suppressed (no sector to compare
    against), but the direction cue is a ceteris-paribus statement about the metric's
    own axis, independent of whether a mark is currently drawn (owner decision) -- so it
    still shows. This is the opposite of the old (mark-gated) behavior; see
    card_copy.metric_gloss()'s docstring."""
    card = _card_with_all_metrics("operating")
    card["sector_peer_count"] = 7
    card["net_debt_to_ebitda"] = 3.9
    card["sector_min_net_debt_to_ebitda"] = -0.4
    card["sector_median_net_debt_to_ebitda"] = 1.9
    card["sector_max_net_debt_to_ebitda"] = 4.2
    html = build_card_html(card)
    assert "ss-metric-range-marker" not in html  # no mark below the peer threshold...
    assert "Lower is better." in html  # ...but the cue still shows


def test_build_card_omits_range_mark_below_peer_threshold() -> None:
    """No mark -- but the "No sector comparison" placeholder fills the gap it would
    have left, so the absence reads as deliberate rather than a missing element
    (owner feedback: a blank gap "still looks like a bug")."""
    html = build_card_html(_card_with_benchmark_range(sector_peer_count=7))
    assert "ss-metric-range-marker" not in html
    assert "ss-metric-range-unavailable" in html
    assert "No sector comparison for this metric." in html


def test_build_card_shows_unavailable_placeholder_for_never_benchmarked_metric() -> None:
    """net_cash is not in BENCHMARK_METRICS at all (a different code path from the
    below-threshold/degenerate cases, which start from a benchmarkable metric that
    becomes unavailable for a specific card) -- it must still get the placeholder, not
    a silent gap, on every card that shows it. Pre-revenue is the only company type with
    a never-benchmarked metric left: the 5-metric benchmark expansion (owner-approved
    follow-up to MR #22) made every operating/financial metric benchmarkable, so
    debt_to_equity (this test's example before that change) no longer fits."""
    card = _card_with_all_metrics("pre_revenue")
    card["sector_peer_count"] = 20  # would be plenty for a benchmarkable metric
    html = build_card_html(card)
    assert "Cash left after clearing all debt" in html  # net_cash's own gloss, sanity check
    assert "ss-metric-range-unavailable" in html


def test_build_card_shows_negative_equity_gloss_for_debt_to_equity() -> None:
    """End-to-end regression for the debt_to_equity value-aware branch (cto-reviewer
    round 2: the unit-level metric_gloss() tests don't prove build_card_html() actually
    renders it) -- the card face must show the negative-equity gloss, not the plain
    "Borrowed money..." text or a "Lower is better." cue on top of it."""
    card = _card_with_all_metrics("operating")
    card["debt_to_equity"] = -2.3
    html = build_card_html(card)
    assert "Negative equity, so this ratio" in html  # apostrophe in "isn't" is HTML-escaped
    assert "Borrowed money vs owners" not in html
    assert "leverage read. Lower is better." not in html


def test_learn_panel_shows_negative_equity_analogy_and_learn_text_for_debt_to_equity() -> None:
    """Same regression, learn panel side -- the analogy/learn text swap, not just the
    card-face gloss (cto-reviewer round 2: this end-to-end path had no test either)."""
    card = _card_with_all_metrics("operating")
    card["debt_to_equity"] = -2.3
    html = build_learn_panel_body_html(card)
    assert "mortgage-versus-equity comparison breaks down" in html
    assert "the owners" in html and "stake itself has gone negative" in html
    assert "Like comparing a mortgage to home equity" not in html  # plain analogy replaced


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
    assert "ss-metric-range-marker" not in html
    assert "ss-metric-range-unavailable" in html


# --- Outlier-aware display range, Gemini feedback point 5 --------------------------------
# Same hand-verified peer set as test_card_copy.py's fence tests: min=-800, Q1=6.5,
# median=10, Q3=13.5, max=17 -- fence clamps the display range to [-4.0, 17.0].

def test_range_mark_no_off_scale_arrow_for_a_normal_peer_within_the_fence() -> None:
    card = _card_with_benchmark_range(
        ebit_margin_pct=11.0,
        sector_min_ebit_margin_pct=-800.0,
        sector_median_ebit_margin_pct=10.0,
        sector_max_ebit_margin_pct=17.0,
        sector_q1_ebit_margin_pct=6.5,
        sector_q3_ebit_margin_pct=13.5,
    )
    html = build_card_html(card)
    assert "ss-metric-range-offscale" not in html
    # the axis label is the CLAMPED bound, not the raw sector minimum
    assert 'class="ss-metric-range-number" style="left:0%">-4.0%<' in html
    assert "-800.0%" not in html


def test_range_mark_off_scale_arrow_for_the_outlier_card_itself() -> None:
    """The outlier's own marker pins to the clamped edge with an off-scale arrow -- its
    RAW value keeps showing correctly in the value row, a completely separate code path
    from the range mark."""
    card = _card_with_benchmark_range(
        ebit_margin_pct=-800.0,
        sector_min_ebit_margin_pct=-800.0,
        sector_median_ebit_margin_pct=10.0,
        sector_max_ebit_margin_pct=17.0,
        sector_q1_ebit_margin_pct=6.5,
        sector_q3_ebit_margin_pct=13.5,
    )
    html = build_card_html(card)
    assert "ss-metric-range-offscale ss-metric-range-offscale-low" in html
    assert '<div class="ss-metric-range-marker" style="left:0.0%">' in html
    assert '<span class="ss-metric-value">-800.0%</span>' in html  # true value, unaffected


def test_range_mark_falls_back_to_raw_min_max_when_quartiles_null() -> None:
    """A sector exported before this shipped has null q1/q3 on every row -- the mark must
    still render the old way (raw min/max), not disappear."""
    html = build_card_html(_card_with_benchmark_range())  # no q1/q3 override -> both null
    assert "ss-metric-range-offscale" not in html
    assert 'class="ss-metric-range-number" style="left:0%">4.1%<' in html


def test_build_card_financial_shows_bank_metrics() -> None:
    html = build_card_html(_card_with_all_metrics("financial"))
    for label in ("Net margin", "Return on assets", "Return on equity"):
        assert label in html
    # The bank card lost its three price-carrying metrics.
    for label in ("Forward P/E", "Price / tangible book", "Dividend yield"):
        assert label not in html


def test_build_card_pre_revenue_shows_survival_metrics_no_dash() -> None:
    html = build_card_html(_card_with_all_metrics("pre_revenue"))
    for label in ("Net cash", "Working capital", "Cash runway", "Cash burn (monthly)"):
        assert label in html
    for label in ("Operating margin", "Return on equity"):
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
    assert VERDICT_BADGE_LABEL["green"] in html
    assert "healthy leverage" in html


def test_labels_render_inside_the_card_identity_section() -> None:
    """The CSS that styles these labels is scoped `.ss-card-identity .ss-block-label`.
    Testing the helpers alone would not catch build_card_html() later moving either block
    into a different section, which would kill the selector silently — the exact way six
    dead selectors reached production in this repo. Assert the ancestry, through the real
    renderer."""
    card = _card_with_all_metrics("operating")
    card["health_verdict"] = "green"
    card["ai_read"] = "Turns sales into profit at a healthy rate."
    card["business_summary"] = "Test Co makes things and sells them worldwide."
    html = build_card_html(card)
    identity = html.split('<section class="ss-card ss-card-identity">', 1)[1]
    identity = identity.split("</section>", 1)[0]
    assert BLOCK_LABEL_ASSESSMENT in identity
    assert BLOCK_LABEL_DESCRIPTION in identity


def test_ai_label_never_appears_without_ai_text() -> None:
    """A verdict can be stored with a null ai_read: 5a writes verdicts, and
    generate_assessments isolates a per-card read failure (or a hallucination-guard reject)
    rather than failing the batch. The badge is rule-computed, so it must still render -- but
    heading it "AI-written" with no AI-written words under it would be a plain falsehood about
    where the assessment came from. The deterministic fallback gets its OWN, honest heading
    instead (BLOCK_LABEL_VERDICT_MEANING), never BLOCK_LABEL_ASSESSMENT."""
    card = {"company_name": "Test Co", "ticker": "TST", "health_verdict": "green"}
    html = _health_block_html(card)
    assert VERDICT_BADGE_LABEL["green"] in html
    assert BLOCK_LABEL_ASSESSMENT not in html
    assert "ss-ai-read" not in html
    assert BLOCK_LABEL_VERDICT_MEANING in html
    assert VERDICT_FALLBACK_READ["green"] in html


def test_ai_label_heads_the_prose_not_the_rule_computed_badge() -> None:
    """Ordering is the claim being made: the verdict badge is decided by fixed rules in
    scripts/assessment_rules.py, never by the model. If the AI label were to drift back
    above the badge, the card would credit the deterministic half of the assessment to a
    language model."""
    card = {
        "company_name": "Test Co",
        "ticker": "TST",
        "health_verdict": "green",
        "ai_read": "Turns sales into profit at a healthy rate.",
    }
    html = _health_block_html(card)
    assert html.index("ss-verdict-badge") < html.index("ss-block-label"), (
        "the AI-written label must not precede the rules-computed verdict badge"
    )


def test_badge_labels_match_the_words_the_model_is_told_to_end_on() -> None:
    """The badge and the prose must not contradict each other. VERDICT_MEANING is what
    the model is told the verdict means, and the prompt tells it to end on that wording;
    if the badge says one word and the paragraph under it lands on another, the card
    argues with itself. Pins the owner-chosen set (§6)."""
    assert VERDICT_BADGE_LABEL == {"green": "Healthy", "yellow": "Mixed", "red": "Fragile"}
    for token, badge in VERDICT_BADGE_LABEL.items():
        assert badge.lower() in VERDICT_MEANING[token].lower(), (
            f"badge {badge!r} for {token!r} does not appear in the model-facing meaning "
            f"{VERDICT_MEANING[token]!r} — the prose would end on a different word than "
            f"the badge shows."
        )


def test_verdict_fallback_read_covers_every_badge_token() -> None:
    """No mechanical wording sync is possible against VERDICT_MEANING (the fallback
    deliberately explains the rule, not the model-facing fragment -- see card_copy.py's
    comment), but every verdict the badge can show must have a fallback sentence, or a card
    whose read is absent would fall back to nothing for that one color."""
    assert set(VERDICT_FALLBACK_READ) == set(VERDICT_BADGE_LABEL)


def test_health_block_absent_without_matching_assessment() -> None:
    """No card_assessments row matched (pipeline lag) -> omit entirely, never a
    placeholder or a "not yet assessed" line."""
    card = _card_with_all_metrics("operating")
    assert _health_block_html(card) == ""
    assert "ss-health-block" not in build_card_html(card)


def test_health_block_shows_badge_and_fallback_without_ai_read_when_null() -> None:
    card = _card_with_all_metrics("operating")
    card["health_verdict"] = "yellow"
    card["ai_read"] = None
    html = _health_block_html(card)
    assert "🟡" in html
    assert "Mixed" in html
    assert "ss-ai-read" not in html
    assert "ss-verdict-fallback" in html
    assert VERDICT_FALLBACK_READ["yellow"] in html
    assert html.index("ss-verdict-badge") < html.index("ss-verdict-fallback"), (
        "the fallback, like the AI read, must not precede the rules-computed verdict badge"
    )


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


def test_metric_groups_render_in_lens_order_on_card_face() -> None:
    """Group headings surface the same analytical-lens grouping metrics_for_card()
    already sorts by (card_copy.py's _LENS_ORDER) -- previously only affected silent
    ordering, now a visible <p class="ss-metric-group-heading"> once per lens
    transition. Expected headings are derived from metrics_for_card()/
    metric_perspective_label() directly -- the same primitives build_card_html() itself
    uses -- rather than a hand-typed catalogue snapshot, so this pins that
    build_card_html() actually surfaces whatever grouping those primitives establish,
    without rotting if the catalogue's perspective assignments change."""
    card = _card_with_all_metrics("operating")
    ordered_metrics = metrics_for_card(card)
    expected_groups: list[str] = []
    for metric in ordered_metrics:
        label = metric_perspective_label(metric)
        if not expected_groups or expected_groups[-1] != label:
            expected_groups.append(label)
    assert len(expected_groups) > 1  # operating cards span more than one lens

    html = build_card_html(card)
    assert html.count("ss-metric-group-heading") == len(expected_groups)
    positions = [html.index(f'ss-metric-group-heading">{label}<') for label in expected_groups]
    assert positions == sorted(positions)  # lens order, no repeated heading per group


def test_metric_groups_also_render_in_learn_panel() -> None:
    """_metric_stack_with_groups() backs both the card face and the learn panel --
    confirm the learn panel gets headings too, not just the card face."""
    card = _card_with_all_metrics("operating")
    html = build_learn_panel_body_html(card)
    assert "ss-metric-group-heading" in html
    # Profitability is the first lens on an operating card now. It used to be Valuation, which
    # led the card purely because the lens taxonomy put it first -- and its only metric,
    # forward_pe, was dropped. No card leads with price any more.
    assert ">Profitability<" in html
