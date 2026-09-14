"""Card copy helpers."""

from __future__ import annotations

from datetime import date, timedelta

import pytest

from card_copy import (  # noqa: E402
    ALL_METRICS,
    BUSINESS_SUMMARY_PREVIEW_WORDS,
    METRIC_ANALOGY,
    METRIC_LEARN,
    STALE_SNAPSHOT_DAYS,
    ai_read_sentences,
    benchmark_range,
    business_summary_is_truncated,
    business_summary_preview,
    format_metric_value,
    freshness_line,
    lead_metric_for_row,
    metric_analogy,
    metric_direction,
    metric_gloss,
    metric_label,
    metric_learn_text,
    metric_perspective_label,
    metrics_for_card,
    saved_row_subtitle,
    truncate_words,
)


def test_metric_gloss_net_cash_when_ratio_negative() -> None:
    assert metric_gloss("net_debt_to_ebitda", -3.6) == "Net cash: cash on hand exceeds debt"


def test_metric_gloss_leverage_when_ratio_positive() -> None:
    gloss = metric_gloss("net_debt_to_ebitda", 2.5)
    assert "repay" in gloss.lower() or "debt" in gloss.lower()
    assert gloss.endswith(". Lower is better.")  # universal cue, net_debt_to_ebitda is lower_better


def test_metric_gloss_negative_equity_when_debt_to_equity_negative() -> None:
    """Same failure shape as net_debt_to_ebitda's "Net cash" branch: since debt is
    always >= 0, a negative debt_to_equity ratio structurally means equity itself has
    gone negative (equity-analyst-reviewer finding -- the catalogue's own applicability
    text warns the ratio "flips or explodes" here). Suppressing the universal cue on
    top matters just as much: a more negative number is not a "better" version of low
    leverage, it is a different, broken reading."""
    gloss = metric_gloss("debt_to_equity", -0.4)
    assert gloss == "Negative equity, so this ratio isn't a normal leverage read"
    assert "Lower is better" not in gloss


def test_metric_gloss_leverage_when_debt_to_equity_positive() -> None:
    gloss = metric_gloss("debt_to_equity", 1.2)
    assert gloss.endswith(". Lower is better.")


def test_metric_analogy_and_learn_text_cover_negative_equity() -> None:
    analogy = metric_analogy("debt_to_equity", -0.4)
    learn = metric_learn_text("debt_to_equity", -0.4)
    assert "negative" in analogy.lower()
    assert "negative" in learn.lower()
    # positive-value path is unaffected -- still the plain catalogue text
    assert metric_analogy("debt_to_equity", 1.2) == METRIC_ANALOGY["debt_to_equity"]
    assert metric_learn_text("debt_to_equity", 1.2) == METRIC_LEARN["debt_to_equity"]


# --- Universal direction cue (metric_direction / metric_gloss's ". Higher/Lower is
# better." suffix) -- applies to every catalogued metric, not just the 9 with a range
# mark (owner's ceteris-paribus generalization; see card_copy.metric_gloss docstring).
# Integration smoke checks that build_card_html() renders this live in test_card_ui.py;
# the branch coverage over metric_direction()/metric_gloss() itself lives here.


def test_metric_direction_higher_better() -> None:
    assert metric_direction("ebit_margin_pct") == "higher"


def test_metric_direction_lower_better() -> None:
    assert metric_direction("net_debt_to_ebitda") == "lower"


def test_metric_direction_unknown_metric_defaults_neutral() -> None:
    """Defensive fallback -- no catalogued metric is actually 'neutral' today (all 13
    are higher_better or lower_better), but an unrecognized id must not raise or
    silently pick a direction it has no basis for."""
    assert metric_direction("not_a_real_metric") == "neutral"


def test_metric_gloss_appends_higher_is_better_cue() -> None:
    assert metric_gloss("ebit_margin_pct", 21.5).endswith(". Higher is better.")


def test_metric_gloss_appends_lower_is_better_cue() -> None:
    assert metric_gloss("burn_rate_monthly", 1.0e6).endswith(". Lower is better.")


def test_metric_gloss_cue_applies_without_a_range_mark() -> None:
    """The cue is universal now -- it does not depend on whether this metric is one of
    the 9 with a sector range mark. working_capital has no range mark at all."""
    assert metric_gloss("working_capital", 2_100_000_000.0).endswith(". Higher is better.")


def test_metric_gloss_annual_ebit_margin_still_gets_cue() -> None:
    """The annual-basis variant swaps the base text but must still get the same
    universal suffix appended after it, not lose it."""
    card = {"ebit_margin_basis": "annual_latest"}
    gloss = metric_gloss("ebit_margin_pct", 21.5, card)
    assert gloss.startswith("Operating profit as share of sales (latest annual)")
    assert gloss.endswith(". Higher is better.")


def test_metric_gloss_net_cash_suppresses_the_cue() -> None:
    """The value-aware "Net cash" branch already states the favorable read directly --
    no suffix appended on top of it (exact match: nothing follows)."""
    assert metric_gloss("net_debt_to_ebitda", -3.6) == "Net cash: cash on hand exceeds debt"


# --- "vs sector" (benchmarked=True) -- names the range mark's population where a
# reader is actually looking, since the sector is otherwise only stated once, higher up
# the card. Owner decision: fold into the gloss line rather than a new word-labels row,
# which was already tight on space (docs/ui/card_metric_cell.md's own collision notes).


def test_metric_gloss_names_the_sector_when_benchmarked() -> None:
    gloss = metric_gloss("ebit_margin_pct", 18.2, benchmarked=True)
    assert gloss == "Operating profit as share of sales (TTM), vs sector. Higher is better."


def test_metric_gloss_omits_vs_sector_when_not_benchmarked() -> None:
    """Default (and what every metric without a range mark gets): no sector mentioned --
    the "No sector comparison for this metric." line under the bar already says so."""
    gloss = metric_gloss("ebit_margin_pct", 18.2)
    assert "sector" not in gloss.lower()
    assert gloss == "Operating profit as share of sales (TTM). Higher is better."


def test_metric_perspective_label_title_cases_the_catalogue_lens() -> None:
    assert metric_perspective_label("ebit_margin_pct") == "Profitability"
    assert metric_perspective_label("net_debt_to_ebitda") == "Solvency"


def test_metric_perspective_label_unknown_metric_is_blank() -> None:
    assert metric_perspective_label("not_a_real_metric") == ""


def test_metric_learn_net_cash_mentions_sign() -> None:
    text = metric_learn_text("net_debt_to_ebitda", -1.0)
    assert "net cash" in text.lower()


def test_metric_analogy_net_cash() -> None:
    text = metric_analogy("net_debt_to_ebitda", -0.5)
    assert "cash" in text.lower()


def test_saved_row_subtitle_ticker_and_sector() -> None:
    card = {"ticker": "AAPL", "sector": "Technology"}
    assert saved_row_subtitle(card) == "AAPL · Technology"


def test_metric_label_annual_operating_margin() -> None:
    card = {"ebit_margin_basis": "annual_latest"}
    assert metric_label("ebit_margin_pct", card) == "Operating margin (annual)"


def test_truncate_words_short_text_unchanged() -> None:
    text = "One two three four five."
    preview, truncated = truncate_words(text, 10)
    assert preview == text
    assert truncated is False


def test_truncate_words_adds_ellipsis() -> None:
    text = " ".join(f"word{i}" for i in range(25))
    preview, truncated = truncate_words(text, 20)
    assert truncated is True
    assert preview.endswith("…")
    assert len(preview.split()) == 20


def test_ai_read_sentences_splits_one_bullet_per_sentence() -> None:
    text = "Revenue grew 6.5%. Margins held steady. Debt stayed low."
    assert ai_read_sentences(text) == (
        "Revenue grew 6.5%.",
        "Margins held steady.",
        "Debt stayed low.",
    )


def test_ai_read_sentences_does_not_split_on_a_decimal_point() -> None:
    text = "Net debt to EBITDA is 9.44 times, which is high for this sector."
    assert ai_read_sentences(text) == (text,)


def test_ai_read_sentences_does_not_split_inside_an_abbreviation() -> None:
    """scope-auditor's round-1 finding: a plain whitespace-after-terminator split breaks
    "U.S. markets rose" into "U" / "S. markets rose" -- the text after the abbreviation's own
    period is not capitalized, so the real sentence boundary (before "Margins") is the only
    one that should split."""
    text = "This is common in the U.S. markets rose this year. Margins held steady."
    assert ai_read_sentences(text) == (
        "This is common in the U.S. markets rose this year.",
        "Margins held steady.",
    )


def test_ai_read_sentences_single_sentence_is_one_bullet() -> None:
    assert ai_read_sentences("Turns sales into profit at a healthy rate.") == (
        "Turns sales into profit at a healthy rate.",
    )


def test_ai_read_sentences_empty_text_is_no_bullets() -> None:
    assert ai_read_sentences("") == ()
    assert ai_read_sentences("   ") == ()


def test_business_summary_preview_uses_original_wording() -> None:
    card = {
        "business_summary": (
            "NVIDIA Corporation provides graphics and compute products for gaming "
            "and professional markets and is a leader in accelerated computing "
            "and artificial intelligence."
        ),
    }
    preview = business_summary_preview(card, max_words=12)
    assert preview is not None
    assert preview.startswith("NVIDIA Corporation provides graphics")
    assert preview.endswith("…")


def test_business_summary_preview_empty_when_no_summary() -> None:
    assert business_summary_preview({}) is None
    assert business_summary_preview({"business_summary": "   "}) is None


def test_business_summary_is_truncated() -> None:
    long_card = {
        "business_summary": " ".join(f"word{i}" for i in range(30)),
    }
    short_card = {"business_summary": "Short company blurb."}
    assert business_summary_is_truncated(long_card) is True
    assert business_summary_is_truncated(short_card) is False
    assert BUSINESS_SUMMARY_PREVIEW_WORDS == 20


# --- Sector/Lifecycle Router: per-type render rule (metrics_for_card) ---

_NEW_OPERATING_METRICS = ("debt_to_equity", "current_ratio_stmt", "statement_roe_pct")
# Solvency/liquidity metrics that stay operating-only across slices (banks never show them).
_BANK_INAPPLICABLE = {"debt_to_equity", "current_ratio_stmt"}


def _full_card(company_type: str | None = "operating") -> dict:
    """A card with every catalogued metric populated (value 1.0)."""
    card = {metric: 1.0 for metric in ALL_METRICS}
    if company_type is None:
        card.pop("company_type", None)
    else:
        card["company_type"] = company_type
    return card


def test_metrics_for_card_operating_includes_new_metrics_in_order() -> None:
    metrics = metrics_for_card(_full_card("operating"))
    for metric in _NEW_OPERATING_METRICS:
        assert metric in metrics
    order = [ALL_METRICS.index(m) for m in metrics]
    assert order == sorted(order), "render order must follow catalogue display order"


def test_metrics_for_card_financial_omits_bank_inapplicable() -> None:
    metrics = metrics_for_card(_full_card("financial"))
    assert _BANK_INAPPLICABLE.isdisjoint(metrics)
    # No valuation metric survives on any card: forward_pe, price_to_tangible_book and
    # dividend_yield_pct were dropped for carrying the share price.
    for dropped in ("forward_pe", "price_to_tangible_book", "dividend_yield_pct"):
        assert dropped not in metrics


# The bank card: 4 metrics, lens-grouped (profitability, growth, returns x2). It was 7 before
# the three price-carrying metrics were dropped. All four now feed the bank verdict: three as
# full axes, and revenue_growth_yoy_pct one-sidedly (a decline blocks green, growth never
# earns it).
_BANK_CARD = (
    "net_margin_pct",
    "revenue_growth_yoy_pct",
    "statement_roe_pct",
    "roa_pct",
)


def test_metrics_for_card_financial_is_the_bank_set_lens_grouped() -> None:
    assert metrics_for_card(_full_card("financial")) == _BANK_CARD


def test_metrics_for_card_financial_omits_operating_only_and_the_new_bank_metrics_are_financial() -> None:
    financial = set(metrics_for_card(_full_card("financial")))
    operating = set(metrics_for_card(_full_card("operating")))
    # the 4 new bank metrics render on the bank card, not the operating card
    for metric in ("net_margin_pct", "roa_pct"):
        assert metric in financial and metric not in operating
    # operating solvency/cash metrics are not on the bank card
    for metric in ("ebit_margin_pct", "net_debt_to_ebitda", "fcf_margin_pct"):
        assert metric in operating and metric not in financial


# The pre-revenue survival card (4c): 4 metrics, lens-grouped (liquidity, cash x3). net_cash
# replaced net_cash_to_market_cap -- same cash-minus-debt idea, as a money
# amount rather than a ratio against market cap, so no share price is involved. That also
# moved its lens from valuation to cash, which is why it now renders AFTER working_capital
# (liquidity sorts before cash) rather than first. Cash-minus-debt is a cash figure; it only
# sat under valuation while it was measured against the share price.
_PRE_REVENUE_CARD = (
    "working_capital",
    "net_cash",
    "cash_runway_months",
    "burn_rate_monthly",
)


def test_metrics_for_card_pre_revenue_is_the_survival_set() -> None:
    assert metrics_for_card(_full_card("pre_revenue")) == _PRE_REVENUE_CARD


def test_metrics_for_card_pre_revenue_omits_operating_and_financial_metrics() -> None:
    pre = set(metrics_for_card(_full_card("pre_revenue")))
    for metric in (
        "ebit_margin_pct", "net_debt_to_ebitda", "fcf_margin_pct",
        "roa_pct", "statement_roe_pct",
    ):
        assert metric not in pre


# Discover list row's lead metric (Variant B). Operating margin for operating (its core,
# verdict-deciding axis), Return on equity for financial (its own core axis), cash runway
# for pre_revenue -- each is a CORE input to that type's own verdict rule in
# scripts/assessment_rules.py, not just any input of any weight. An earlier version used
# Return on equity for operating too, but that metric is only a tie-breaking supporting axis
# for _verdict_operating, not one of the three axes that actually decide red/green -- caught
# by equity-analyst-reviewer round 5, corrected before merge.
def test_lead_metric_for_row_operating_is_operating_margin() -> None:
    assert lead_metric_for_row(_full_card("operating")) == ("Operating margin (TTM)", "1.0%")


def test_lead_metric_for_row_financial_is_return_on_equity() -> None:
    assert lead_metric_for_row(_full_card("financial")) == ("Return on equity", "1.0%")


def test_lead_metric_for_row_pre_revenue_is_cash_runway() -> None:
    assert lead_metric_for_row(_full_card("pre_revenue")) == ("Cash runway", "1.0")


def test_lead_metric_for_row_defaults_to_operating_when_type_missing() -> None:
    assert lead_metric_for_row(_full_card(None)) == ("Operating margin (TTM)", "1.0%")


def test_lead_metric_for_row_is_none_when_the_value_is_missing() -> None:
    """A row degrades to title/subtitle only, never a blank or invented number."""
    card = _full_card("operating")
    card["ebit_margin_pct"] = None
    assert lead_metric_for_row(card) is None


def test_currency_compact_format() -> None:
    assert format_metric_value("working_capital", 2_100_000_000.0, "USD") == "$2.1B"
    assert format_metric_value("burn_rate_monthly", -58_300_000.0, "GBP") == "-£58.3M"
    assert format_metric_value("working_capital", 950_000.0, "JPY") == "¥950.0K"
    # unknown currency -> code prefix; no currency -> no symbol
    assert format_metric_value("working_capital", 1_000_000.0, "CHF") == "CHF 1.0M"
    assert format_metric_value("working_capital", 1_000_000.0, None) == "1.0M"
    # ratio/percent metrics are unaffected by the new format path
    assert format_metric_value("cash_runway_months", 36.0) == "36.0"


def test_metrics_for_card_pre_revenue_omits_bank_inapplicable() -> None:
    metrics = metrics_for_card(_full_card("pre_revenue"))
    assert _BANK_INAPPLICABLE.isdisjoint(metrics)


def test_metrics_for_card_omits_null_valued_metric() -> None:
    card = _full_card("operating")
    card["current_ratio_stmt"] = None
    metrics = metrics_for_card(card)
    assert "current_ratio_stmt" not in metrics  # omitted, never rendered as an em-dash
    assert "debt_to_equity" in metrics  # other operating metrics still present


def test_metrics_for_card_missing_company_type_defaults_operating() -> None:
    assert metrics_for_card(_full_card(None)) == metrics_for_card(_full_card("operating"))


def test_metrics_for_card_tier_split() -> None:
    card = _full_card("operating")
    tier1 = metrics_for_card(card, tier=1)
    tier2 = metrics_for_card(card, tier=2)
    assert set(tier1).isdisjoint(tier2)
    assert set(tier1) | set(tier2) == set(metrics_for_card(card))
    assert "ebit_margin_pct" in tier1  # tier-1 metrics render on the card face
    assert "statement_roe_pct" in tier2  # balance metric below the fold


def test_freshness_line_silent_within_normal_cadence() -> None:
    """A snapshot from the tail of a healthy 1st/15th cycle must NOT read as stale —
    that's the exact noise this threshold exists to avoid. Pinned to a literal day
    count, not derived from STALE_SNAPSHOT_DAYS itself — deriving the fixture from the
    same constant under test would pass at any threshold value, including a wrong one."""
    snapshot = date.today() - timedelta(days=18)
    line = freshness_line({"snapshot_date": snapshot.isoformat()})
    assert "may be up to" not in line


def test_freshness_line_flags_genuinely_stale_snapshot() -> None:
    snapshot = date.today() - timedelta(days=19)
    line = freshness_line({"snapshot_date": snapshot.isoformat()})
    assert "may be up to" in line


def test_stale_snapshot_days_covers_worst_case_healthy_gap() -> None:
    """Regression guard for the bug this exact constant already shipped once: a
    threshold left over from a shorter cadence flags every normal refresh as stale.
    15th -> 1st after a 31-day month is the longest gap between two healthy runs
    under the 1st/15th cron; the threshold must clear it."""
    worst_case_healthy_gap_days = 17
    assert STALE_SNAPSHOT_DAYS > worst_case_healthy_gap_days


def _range_card(
    *, value=21.5, minimum=4.1, median=15.3, maximum=38.9, peer_count=20, q1=None, q3=None
) -> dict:
    card = {
        "sector_peer_count": peer_count,
        "ebit_margin_pct": value,
        "sector_min_ebit_margin_pct": minimum,
        "sector_median_ebit_margin_pct": median,
        "sector_max_ebit_margin_pct": maximum,
    }
    if q1 is not None:
        card["sector_q1_ebit_margin_pct"] = q1
    if q3 is not None:
        card["sector_q3_ebit_margin_pct"] = q3
    return card


def test_benchmark_range_computes_position_and_median_pct() -> None:
    card = _range_card()
    rng = benchmark_range(card, "ebit_margin_pct", "sector_median_ebit_margin_pct")
    assert rng is not None
    assert rng["min"] == 4.1
    assert rng["median"] == 15.3
    assert rng["max"] == 38.9
    assert rng["value"] == 21.5
    # (15.3 - 4.1) / (38.9 - 4.1) * 100
    assert rng["median_pct"] == pytest.approx(32.18, abs=0.01)
    # (21.5 - 4.1) / (38.9 - 4.1) * 100
    assert rng["position_pct"] == pytest.approx(50.0, abs=0.01)


def test_benchmark_range_none_below_peer_threshold() -> None:
    card = _range_card(peer_count=7)
    assert benchmark_range(card, "ebit_margin_pct", "sector_median_ebit_margin_pct") is None


def test_benchmark_range_none_when_degenerate_min_equals_max() -> None:
    """Every eligible peer reports the same value -- no range to show, and no
    division by zero. This is a real data shape, not just a defensive edge case: a
    tightly-clustered or small-but-above-threshold sector can land here."""
    card = _range_card(value=20.0, minimum=20.0, median=20.0, maximum=20.0)
    assert benchmark_range(card, "ebit_margin_pct", "sector_median_ebit_margin_pct") is None


def test_benchmark_range_clamps_value_outside_min_max() -> None:
    """Defensive: the card's own company should always fall within its own cohort's
    min/max by construction, but don't trust that invariant blindly."""
    card = _range_card(value=999.0, minimum=4.1, median=15.3, maximum=38.9)
    rng = benchmark_range(card, "ebit_margin_pct", "sector_median_ebit_margin_pct")
    assert rng is not None
    assert rng["position_pct"] == 100.0
    assert rng["high_off_scale"] is True
    assert rng["low_off_scale"] is False


# --- Outlier-aware display range, Gemini feedback point 5 --------------------------------

def test_benchmark_range_falls_back_to_raw_min_max_when_quartiles_absent() -> None:
    """A sector exported before this shipped (or any transitional state) has null q1/q3 --
    must render the old way, not disappear or error."""
    card = _range_card(value=21.5, minimum=4.1, median=15.3, maximum=38.9, q1=None, q3=None)
    rng = benchmark_range(card, "ebit_margin_pct", "sector_median_ebit_margin_pct")
    assert rng is not None
    assert rng["min"] == 4.1
    assert rng["max"] == 38.9
    assert rng["low_off_scale"] is False
    assert rng["high_off_scale"] is False


def test_benchmark_range_fence_is_a_no_op_without_a_real_outlier() -> None:
    """A normally-spread sector's Tukey fence is WIDER than its true min/max (that's the
    whole point of the convention), so the clamp changes nothing here. min=10, Q1=13.5,
    median=17, Q3=20.5, max=24 (hand-verified against DuckDB quantile_cont in
    dbt_analytics's sector_benchmarks_computes_quartiles_with_real_spread unit test);
    IQR=7.0, fence = [13.5-1.5*7, 20.5+1.5*7] = [3.0, 31.0], both wider than [10, 24]."""
    card = _range_card(value=17.0, minimum=10.0, median=17.0, maximum=24.0, q1=13.5, q3=20.5)
    rng = benchmark_range(card, "ebit_margin_pct", "sector_median_ebit_margin_pct")
    assert rng is not None
    assert rng["min"] == 10.0
    assert rng["max"] == 24.0


def test_benchmark_range_clamps_the_axis_when_a_real_outlier_exists() -> None:
    """The actual bug this fixes: peers [-800, 5, 7, 9, 11, 13, 15, 17] (min=-800, Q1=6.5,
    median=10, Q3=13.5, max=17 -- fence = [6.5-1.5*7, 13.5+1.5*7] = [-4.0, 24.0], and since
    24.0 > true max 17.0 the upper bound stays the true max). A normal peer at 11.0: under
    the OLD raw-min/max scaling this would land at (11-(-800))/(17-(-800))*100 ~= 99.3%,
    almost indistinguishable from the sector maximum. Clamped, it lands in the middle of
    the range instead -- the whole point of this task."""
    card = _range_card(value=11.0, minimum=-800.0, median=10.0, maximum=17.0, q1=6.5, q3=13.5)
    rng = benchmark_range(card, "ebit_margin_pct", "sector_median_ebit_margin_pct")
    assert rng is not None
    assert rng["min"] == -4.0
    assert rng["max"] == 17.0
    # (11 - (-4)) / (17 - (-4)) * 100
    assert rng["position_pct"] == pytest.approx(71.43, abs=0.01)
    assert rng["low_off_scale"] is False
    assert rng["high_off_scale"] is False


def test_benchmark_range_flags_the_outlier_itself_as_off_scale() -> None:
    """Same sector as above, but this IS the outlier card (-800.0). Its marker pins to the
    clamped edge (0%) rather than reporting a meaningless raw position; low_off_scale is
    the signal frontend/card_ui.py uses to draw the off-scale arrow. Its raw value is a
    completely separate code path (_metric_cell_html's value row) and is never touched
    here -- benchmark_range() only ever computes a POSITION, never a displayed value."""
    card = _range_card(value=-800.0, minimum=-800.0, median=10.0, maximum=17.0, q1=6.5, q3=13.5)
    rng = benchmark_range(card, "ebit_margin_pct", "sector_median_ebit_margin_pct")
    assert rng is not None
    assert rng["position_pct"] == 0.0
    assert rng["low_off_scale"] is True
    assert rng["high_off_scale"] is False
    assert rng["value"] == -800.0  # the raw value is carried through unchanged


def test_hardcoded_analogy_overrides_name_no_currency() -> None:
    """`metric_analogy` can return a hardcoded string instead of the catalogue one (the
    annual-basis operating-margin override, the negative-equity ones). Those live in
    card_copy.py, not in the seed, so the catalogue currency guard in tests/tooling cannot
    see them: this is the second home for the same defect and needs its own check.

    A margin is a percentage and carries no currency, so a beginner reading a Nikkei or DAX
    card must not be told about dollars, pounds or cents.
    """
    import re

    currency_words = ("dollar", "cent", "pound", "pence", "penny", "euro", "yen", "franc")
    symbols = ("$", "£", "¥", "€")
    cards = (
        None,
        {"ebit_margin_basis": "annual_latest"},
        {"ebit_margin_basis": "ttm_quarters"},
    )
    for metric in ALL_METRICS:
        for card in cards:
            for value in (12.0, -1.5, None):
                text = metric_analogy(metric, value, card)
                lowered = text.lower()
                for word in currency_words:
                    assert not re.search(rf"\b{word}s?\b", lowered), (
                        f"{metric} analogy names a currency: {text!r}"
                    )
                for symbol in symbols:
                    assert symbol not in text, f"{metric} analogy names {symbol}: {text!r}"
