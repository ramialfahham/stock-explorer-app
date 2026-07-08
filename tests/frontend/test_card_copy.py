"""Card copy helpers."""

from __future__ import annotations

from card_copy import (  # noqa: E402
    ALL_METRICS,
    BUSINESS_SUMMARY_PREVIEW_WORDS,
    business_summary_is_truncated,
    business_summary_preview,
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
