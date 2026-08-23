"""Card copy helpers."""

from __future__ import annotations

from datetime import date, timedelta

import pytest

from card_copy import (  # noqa: E402
    ALL_METRICS,
    BUSINESS_SUMMARY_PREVIEW_WORDS,
    STALE_SNAPSHOT_DAYS,
    benchmark_range,
    business_summary_is_truncated,
    business_summary_preview,
    format_metric_value,
    freshness_line,
    metric_analogy,
    metric_gloss,
    metric_label,
    metric_learn_text,
    metrics_for_card,
    saved_row_subtitle,
    truncate_words,
)


def test_metric_gloss_net_cash_when_ratio_negative() -> None:
    assert metric_gloss("net_debt_to_ebitda", -3.6) == "Net cash — cash on hand exceeds debt"


def test_metric_gloss_leverage_when_ratio_positive() -> None:
    gloss = metric_gloss("net_debt_to_ebitda", 2.5)
    assert "repay" in gloss.lower() or "debt" in gloss.lower()


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
    assert "forward_pe" in metrics  # valuation still applies to banks


# The bank card (4b): 7 metrics, lens-grouped (valuation, valuation, profitability, growth, returns×3).
_BANK_CARD = (
    "forward_pe",
    "price_to_tangible_book",
    "net_margin_pct",
    "revenue_growth_yoy_pct",
    "statement_roe_pct",
    "roa_pct",
    "dividend_yield_pct",
)


def test_metrics_for_card_financial_is_the_bank_set_lens_grouped() -> None:
    assert metrics_for_card(_full_card("financial")) == _BANK_CARD


def test_metrics_for_card_financial_omits_operating_only_and_the_new_bank_metrics_are_financial() -> None:
    financial = set(metrics_for_card(_full_card("financial")))
    operating = set(metrics_for_card(_full_card("operating")))
    # the 4 new bank metrics render on the bank card, not the operating card
    for metric in ("price_to_tangible_book", "net_margin_pct", "roa_pct", "dividend_yield_pct"):
        assert metric in financial and metric not in operating
    # operating solvency/cash metrics are not on the bank card
    for metric in ("ebit_margin_pct", "net_debt_to_ebitda", "fcf_margin_pct"):
        assert metric in operating and metric not in financial


# The pre-revenue survival card (4c): 4 metrics, lens-grouped (valuation, liquidity, cash, cash).
_PRE_REVENUE_CARD = (
    "net_cash_to_market_cap",
    "working_capital",
    "cash_runway_months",
    "burn_rate_monthly",
)


def test_metrics_for_card_pre_revenue_is_the_survival_set() -> None:
    assert metrics_for_card(_full_card("pre_revenue")) == _PRE_REVENUE_CARD


def test_metrics_for_card_pre_revenue_omits_operating_and_financial_metrics() -> None:
    pre = set(metrics_for_card(_full_card("pre_revenue")))
    for metric in (
        "forward_pe", "ebit_margin_pct", "net_debt_to_ebitda", "fcf_margin_pct",
        "price_to_tangible_book", "roa_pct", "dividend_yield_pct", "statement_roe_pct",
    ):
        assert metric not in pre


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
    assert "forward_pe" in tier1  # hero three
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


def _range_card(*, value=21.5, minimum=4.1, median=15.3, maximum=38.9, peer_count=20) -> dict:
    return {
        "sector_peer_count": peer_count,
        "ebit_margin_pct": value,
        "sector_min_ebit_margin_pct": minimum,
        "sector_median_ebit_margin_pct": median,
        "sector_max_ebit_margin_pct": maximum,
    }


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
