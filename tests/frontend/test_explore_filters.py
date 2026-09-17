"""Tests for explore filter pool logic."""

from __future__ import annotations

from explore_filters import (  # noqa: E402
    ALL_MARKETS,
    ALL_SECTORS,
    attach_assessments,
    card_matches_metric_presets,
    deck_rows_lack_columns,
    default_market_filter,
    filter_pool,
    filter_scope_summary,
    market_filter_options,
    metric_preset_label,
    metric_preset_options,
    saved_keys_with_order,
    skipped_keys_with_order,
    walk_progress_line,
)


def _card(
    ticker: str, sector: str, market: str = "us_sp500", snapshot_date: str = "2026-06-09"
) -> dict:
    return {
        "market_code": market,
        "ticker": ticker,
        "sector": sector,
        "snapshot_date": snapshot_date,
        "is_card_eligible": True,
    }


def test_default_market_filter_is_all_markets() -> None:
    assert default_market_filter() == ALL_MARKETS


def test_market_filter_options_all_markets_first() -> None:
    cards = [_card("AAPL", "Technology", market="us_sp500")]
    options = market_filter_options(cards)
    assert options[0][0] == ALL_MARKETS
    assert options[0][1] == "All markets"


def test_market_filter_options_all_markets_present_even_with_no_cards() -> None:
    """An empty pool must never leave the Filters popover with zero options."""
    options = market_filter_options([])
    assert options == [(ALL_MARKETS, "All markets")]


def test_market_filter_options_includes_a_market_with_an_eligible_card() -> None:
    cards = [_card("AAPL", "Technology", market="us_sp500")]
    options = market_filter_options(cards)
    codes = {code for code, _ in options}
    assert "us_sp500" in codes


def test_market_filter_options_excludes_a_market_with_zero_eligible_cards() -> None:
    """The actual bug this guards: a market can be onboarded (present in
    MARKET_DISPLAY_NAMES) with zero exported data yet, e.g. the pipeline hasn't run for it
    since onboarding -- the dropdown must not offer a choice that silently returns nothing."""
    cards = [_card("AAPL", "Technology", market="us_sp500")]
    options = market_filter_options(cards)
    codes = {code for code, _ in options}
    assert "fr_cac40" not in codes


def test_market_filter_options_excludes_a_card_marked_not_eligible() -> None:
    ineligible = {**_card("AAPL", "Technology", market="fr_cac40"), "is_card_eligible": False}
    options = market_filter_options([ineligible])
    codes = {code for code, _ in options}
    assert "fr_cac40" not in codes


def test_market_filter_options_preserves_registry_order_among_included_markets() -> None:
    """Ordering must match MARKET_DISPLAY_NAMES's own registry-ingest order, not the order
    cards happen to appear in -- FTSE 100 lists before Nikkei 225 in the registry regardless
    of which one this pool saw an eligible card for first."""
    cards = [
        _card("SONY", "Technology", market="jp_nikkei225"),
        _card("HSBA", "Financial Services", market="uk_ftse100"),
    ]
    options = market_filter_options(cards)
    codes = [code for code, _ in options]
    assert codes.index("uk_ftse100") < codes.index("jp_nikkei225")


def test_filter_scope_summary() -> None:
    assert filter_scope_summary(market_code=ALL_MARKETS, sector=ALL_SECTORS) == (
        "All markets · All sectors"
    )
    assert filter_scope_summary(market_code="us_sp500", sector="Technology") == (
        "S&P 500 · Technology"
    )


def test_walk_progress_line() -> None:
    assert walk_progress_line(position=1, total=464) == "1 of 464"
    assert walk_progress_line(position=3, total=47) == "3 of 47"
    assert walk_progress_line(position=1, total=0) == ""


def test_filter_pool_respects_sector() -> None:
    cards = [
        _card("AAPL", "Technology"),
        _card("ALB", "Basic Materials"),
    ]
    pool = filter_pool(
        cards,
        [],
        market_code="us_sp500",
        sector="Basic Materials",
    )
    tickers = {c["ticker"] for c in pool}
    assert tickers == {"ALB"}


def test_filter_pool_all_markets() -> None:
    cards = [
        _card("AAPL", "Technology", market="us_sp500"),
        _card("BHP", "Materials", market="au_asx200"),
    ]
    pool = filter_pool(
        cards,
        [],
        market_code=ALL_MARKETS,
        sector=ALL_SECTORS,
    )
    assert {c["ticker"] for c in pool} == {"AAPL", "BHP"}


def test_filter_pool_all_markets_collapses_dual_index_ticker() -> None:
    """The bug this guards (issue #7): Airbus is a constituent of both the DAX and CAC 40,
    both resolving to the same yfinance ticker (AIR.PA) -- "All markets" must show it once,
    not once per index."""
    cards = [
        _card("AIR.PA", "Industrials", market="de_dax", snapshot_date="2026-06-09"),
        _card("AIR.PA", "Industrials", market="fr_cac40", snapshot_date="2026-06-09"),
        _card("AAPL", "Technology", market="us_sp500"),
    ]
    pool = filter_pool(
        cards,
        [],
        market_code=ALL_MARKETS,
        sector=ALL_SECTORS,
    )
    tickers = [c["ticker"] for c in pool]
    assert tickers.count("AIR.PA") == 1
    assert set(tickers) == {"AIR.PA", "AAPL"}


def test_filter_pool_dual_index_ticker_keeps_latest_snapshot() -> None:
    cards = [
        _card("AIR.PA", "Industrials", market="de_dax", snapshot_date="2026-05-01"),
        _card("AIR.PA", "Industrials", market="fr_cac40", snapshot_date="2026-06-09"),
    ]
    pool = filter_pool(
        cards,
        [],
        market_code=ALL_MARKETS,
        sector=ALL_SECTORS,
    )
    assert len(pool) == 1
    assert pool[0]["market_code"] == "fr_cac40"


def test_filter_pool_single_market_scope_unaffected_by_dedup() -> None:
    """A market-scoped view must still show every eligible row for that market -- the
    ticker dedup only fires for ALL_MARKETS, never for a single-market filter."""
    cards = [
        _card("AIR.PA", "Industrials", market="de_dax"),
        _card("BMW", "Consumer Cyclical", market="de_dax"),
    ]
    pool = filter_pool(
        cards,
        [],
        market_code="de_dax",
        sector=ALL_SECTORS,
    )
    assert {c["ticker"] for c in pool} == {"AIR.PA", "BMW"}


def test_metric_preset_options_has_five_presets() -> None:
    assert len(metric_preset_options()) == 5


def test_metric_preset_label_is_plain_language() -> None:
    assert metric_preset_label("high_margin") == "High margin"


def test_card_matches_metric_presets_true_when_type_has_no_check() -> None:
    """The rule this guards: a preset the card's company_type has no check for (e.g.
    cash_safe against an operating card) must pass through, never exclude -- the same
    "omit, never fake" rule the health verdict and metric stack already follow."""
    card = _card("AAPL", "Technology")
    card["company_type"] = "operating"
    assert card_matches_metric_presets(card, ["cash_safe"]) is True


def test_card_matches_metric_presets_true_when_type_matches_but_value_missing() -> None:
    """A card whose type HAS a check but is still missing that metric's value (not in its
    type's mandatory eligibility set, e.g. statement_roe_pct for operating) also passes
    through -- it was never guaranteed to have that value."""
    card = _card("AAPL", "Technology")
    card["company_type"] = "operating"
    assert card_matches_metric_presets(card, ["strong_returns"]) is True


def test_card_matches_metric_presets_high_margin_operating_above_threshold() -> None:
    card = _card("AAPL", "Technology")
    card["company_type"] = "operating"
    card["ebit_margin_pct"] = 25.0
    assert card_matches_metric_presets(card, ["high_margin"]) is True


def test_card_matches_metric_presets_high_margin_operating_below_threshold() -> None:
    card = _card("AAPL", "Technology")
    card["company_type"] = "operating"
    card["ebit_margin_pct"] = 10.0
    assert card_matches_metric_presets(card, ["high_margin"]) is False


def test_card_matches_metric_presets_high_margin_financial_uses_net_margin() -> None:
    card = _card("JPM", "Financial Services")
    card["company_type"] = "financial"
    card["net_margin_pct"] = 30.0
    assert card_matches_metric_presets(card, ["high_margin"]) is True


def test_card_matches_metric_presets_operating_ignores_a_co_populated_net_margin() -> None:
    """The bug this guards (cto-reviewer, this task): ebit_margin_pct and net_margin_pct
    are NOT mutually exclusive in the real data -- int_stock__card_metrics.sql computes
    both straight from statement fields with no company_type gate, so most operating cards
    also carry a non-null net_margin_pct. An operating card with a strong operating margin
    but a thin net margin (interest, tax) must still match high_margin -- checking by
    presence alone would wrongly AND the two thresholds together."""
    card = _card("AAPL", "Technology")
    card["company_type"] = "operating"
    card["ebit_margin_pct"] = 25.0
    card["net_margin_pct"] = 2.0
    assert card_matches_metric_presets(card, ["high_margin"]) is True


def test_card_matches_metric_presets_low_debt_uses_lower_better_direction() -> None:
    card = _card("AAPL", "Technology")
    card["company_type"] = "operating"
    card["net_debt_to_ebitda"] = 1.5
    assert card_matches_metric_presets(card, ["low_debt"]) is True
    card["net_debt_to_ebitda"] = 3.0
    assert card_matches_metric_presets(card, ["low_debt"]) is False


def test_card_matches_metric_presets_all_active_presets_must_pass() -> None:
    card = _card("AAPL", "Technology")
    card["company_type"] = "operating"
    card["ebit_margin_pct"] = 25.0
    card["net_debt_to_ebitda"] = 3.0
    assert card_matches_metric_presets(card, ["high_margin"]) is True
    assert card_matches_metric_presets(card, ["high_margin", "low_debt"]) is False


def test_filter_pool_applies_active_metric_preset() -> None:
    cards = [
        _card("AAPL", "Technology"),
        _card("MSFT", "Technology"),
    ]
    for c in cards:
        c["company_type"] = "operating"
    cards[0]["ebit_margin_pct"] = 25.0
    cards[1]["ebit_margin_pct"] = 10.0
    pool = filter_pool(
        cards,
        [],
        market_code="us_sp500",
        sector=ALL_SECTORS,
        metric_presets=["high_margin"],
    )
    assert {c["ticker"] for c in pool} == {"AAPL"}


def test_filter_pool_no_presets_is_unaffected() -> None:
    cards = [_card("AAPL", "Technology"), _card("MSFT", "Technology")]
    cards[0]["company_type"] = "operating"
    cards[0]["ebit_margin_pct"] = 10.0
    pool = filter_pool(
        cards,
        [],
        market_code="us_sp500",
        sector=ALL_SECTORS,
    )
    assert {c["ticker"] for c in pool} == {"AAPL", "MSFT"}


def test_filter_scope_summary_includes_active_presets() -> None:
    summary = filter_scope_summary(
        market_code="us_sp500",
        sector=ALL_SECTORS,
        metric_presets=["low_debt", "high_margin"],
    )
    assert summary == "S&P 500 · All sectors · High margin, Low debt"


def test_filter_scope_summary_no_presets_omits_suffix() -> None:
    summary = filter_scope_summary(market_code="us_sp500", sector=ALL_SECTORS)
    assert summary == "S&P 500 · All sectors"


def test_filter_pool_excludes_saved() -> None:
    cards = [_card("AAPL", "Technology"), _card("MSFT", "Technology")]
    interactions = [{"market_code": "us_sp500", "ticker": "AAPL", "action": "save"}]
    pool = filter_pool(
        cards,
        interactions,
        market_code="us_sp500",
        sector=ALL_SECTORS,
    )
    assert [c["ticker"] for c in pool] == ["MSFT"]


def test_filter_pool_reincludes_a_ticker_after_unsave() -> None:
    """The bug this guards: filter_pool used to have its own separate 'is this saved' copy
    with no concept of unsave, so removing a saved company from the Saved tab would leave it
    excluded from Discover forever, with no way back in since Search has no Save action."""
    cards = [_card("AAPL", "Technology"), _card("MSFT", "Technology")]
    interactions = [
        {"market_code": "us_sp500", "ticker": "AAPL", "action": "save", "created_at": "t1"},
        {"market_code": "us_sp500", "ticker": "AAPL", "action": "unsave", "created_at": "t2"},
    ]
    pool = filter_pool(
        cards,
        interactions,
        market_code="us_sp500",
        sector=ALL_SECTORS,
    )
    assert {c["ticker"] for c in pool} == {"AAPL", "MSFT"}


def test_saved_keys_with_order_absent_when_never_saved() -> None:
    assert saved_keys_with_order([]) == {}


def test_saved_keys_with_order_present_after_a_single_save() -> None:
    interactions = [
        {"market_code": "us_sp500", "ticker": "AAPL", "action": "save", "created_at": "t1"},
    ]
    assert saved_keys_with_order(interactions) == {("us_sp500", "AAPL"): "t1"}


def test_saved_keys_with_order_absent_after_save_then_unsave() -> None:
    interactions = [
        {"market_code": "us_sp500", "ticker": "AAPL", "action": "save", "created_at": "t1"},
        {"market_code": "us_sp500", "ticker": "AAPL", "action": "unsave", "created_at": "t2"},
    ]
    assert saved_keys_with_order(interactions) == {}


def test_saved_keys_with_order_present_with_second_timestamp_after_resave() -> None:
    """Save, unsave, save again -- must key on the SECOND save's timestamp, not the first,
    so a re-saved company sorts as freshly saved rather than retaining a stale position."""
    interactions = [
        {"market_code": "us_sp500", "ticker": "AAPL", "action": "save", "created_at": "t1"},
        {"market_code": "us_sp500", "ticker": "AAPL", "action": "unsave", "created_at": "t2"},
        {"market_code": "us_sp500", "ticker": "AAPL", "action": "save", "created_at": "t3"},
    ]
    assert saved_keys_with_order(interactions) == {("us_sp500", "AAPL"): "t3"}


def test_saved_keys_with_order_absent_when_unsaved_without_ever_saving() -> None:
    """An unsave with no prior save shouldn't crash or appear saved -- e.g. a stale/replayed
    interaction row for a ticker this device never actually saved."""
    interactions = [
        {"market_code": "us_sp500", "ticker": "AAPL", "action": "unsave", "created_at": "t1"},
    ]
    assert saved_keys_with_order(interactions) == {}


def test_skipped_keys_with_order_absent_when_never_skipped() -> None:
    assert skipped_keys_with_order([]) == {}


def test_skipped_keys_with_order_present_after_a_single_skip() -> None:
    interactions = [
        {"market_code": "us_sp500", "ticker": "AAPL", "action": "skip", "created_at": "t1"},
    ]
    assert skipped_keys_with_order(interactions) == {("us_sp500", "AAPL"): "t1"}


def test_skipped_keys_with_order_absent_after_skip_then_unskip() -> None:
    interactions = [
        {"market_code": "us_sp500", "ticker": "AAPL", "action": "skip", "created_at": "t1"},
        {"market_code": "us_sp500", "ticker": "AAPL", "action": "unskip", "created_at": "t2"},
    ]
    assert skipped_keys_with_order(interactions) == {}


def test_skipped_keys_with_order_present_with_second_timestamp_after_reskip() -> None:
    interactions = [
        {"market_code": "us_sp500", "ticker": "AAPL", "action": "skip", "created_at": "t1"},
        {"market_code": "us_sp500", "ticker": "AAPL", "action": "unskip", "created_at": "t2"},
        {"market_code": "us_sp500", "ticker": "AAPL", "action": "skip", "created_at": "t3"},
    ]
    assert skipped_keys_with_order(interactions) == {("us_sp500", "AAPL"): "t3"}


def test_skipped_keys_with_order_independent_of_save_state() -> None:
    """skip/unskip and save/unsave are separate action pairs -- a save interaction must
    never register as a skip, and vice versa."""
    interactions = [
        {"market_code": "us_sp500", "ticker": "AAPL", "action": "save", "created_at": "t1"},
        {"market_code": "us_sp500", "ticker": "MSFT", "action": "skip", "created_at": "t2"},
    ]
    assert skipped_keys_with_order(interactions) == {("us_sp500", "MSFT"): "t2"}
    assert saved_keys_with_order(interactions) == {("us_sp500", "AAPL"): "t1"}


def test_dedupe_coalesces_summary_from_older_snapshot() -> None:
    cards = [
        {
            "market_code": "us_sp500",
            "ticker": "TEST",
            "snapshot_date": "2026-06-09",
            "business_summary": None,
        },
        {
            "market_code": "us_sp500",
            "ticker": "TEST",
            "snapshot_date": "2026-05-01",
            "business_summary": "Older snapshot summary text.",
        },
    ]
    from explore_filters import dedupe_to_latest_snapshot

    deduped = dedupe_to_latest_snapshot(cards)
    assert len(deduped) == 1
    assert deduped[0]["business_summary"] == "Older snapshot summary text."


def test_deck_rows_lack_columns_when_a_required_column_is_absent() -> None:
    cards = [_card("AAPL", "Technology")]
    assert deck_rows_lack_columns(cards, ("market_code", "ticker", "cash_runway_months")) is True


def test_deck_rows_lack_columns_is_false_when_every_column_is_present() -> None:
    """Present-but-null still counts as present. A metric a company genuinely has no value for
    is normal; only a MISSING key means the cached row predates the current code."""
    cards = [{**_card("AAPL", "Technology"), "cash_runway_months": None}]
    assert deck_rows_lack_columns(cards, ("market_code", "ticker", "cash_runway_months")) is False


def test_deck_rows_lack_columns_ignores_extra_columns() -> None:
    cards = [{**_card("AAPL", "Technology"), "unexpected": 1}]
    assert deck_rows_lack_columns(cards, ("market_code", "ticker")) is False


def test_deck_rows_lack_columns_is_false_for_an_empty_deck() -> None:
    """An empty deck is a load that has not happened yet, not a stale shape -- returning True
    here would make _ensure_all_cards refetch on every run against an empty export."""
    assert deck_rows_lack_columns([], ("market_code",)) is False


def test_attach_assessments_copies_fields_on_match() -> None:
    cards = [_card("AAPL", "Technology")]
    assessments = {
        ("us_sp500", "AAPL"): {
            "snapshot_date": "2026-06-09",
            "health_verdict": "green",
            "ai_read": "Sturdy figures.",
        }
    }
    result = attach_assessments(cards, assessments)
    assert result[0]["health_verdict"] == "green"
    assert result[0]["ai_read"] == "Sturdy figures."


def test_attach_assessments_leaves_card_unchanged_without_a_match() -> None:
    """No row for this (market_code, ticker) — assessments pipeline can lag a
    newly-eligible card. Card is returned as-is, never a placeholder key."""
    cards = [_card("AAPL", "Technology")]
    result = attach_assessments(cards, assessments={})
    assert "health_verdict" not in result[0]
    assert "ai_read" not in result[0]


def test_attach_assessments_preserves_null_ai_read() -> None:
    cards = [_card("AAPL", "Technology")]
    assessments = {
        ("us_sp500", "AAPL"): {
            "snapshot_date": "2026-06-09",
            "health_verdict": "red",
            "ai_read": None,
        }
    }
    result = attach_assessments(cards, assessments)
    assert result[0]["health_verdict"] == "red"
    assert result[0]["ai_read"] is None


def test_attach_assessments_does_not_mutate_the_original_card() -> None:
    card = _card("AAPL", "Technology")
    assessments = {
        ("us_sp500", "AAPL"): {
            "snapshot_date": "2026-06-09",
            "health_verdict": "green",
            "ai_read": "text",
        }
    }
    attach_assessments([card], assessments)
    assert "health_verdict" not in card


def test_attach_assessments_withholds_a_verdict_from_another_snapshot() -> None:
    """The verdict is the product's central claim and a reader cannot tell which numbers it
    was computed from, so a verdict that does not belong to the numbers on screen is withheld
    rather than shown. Both directions occur: the assessments step can fail after a successful
    export, and the atomic export can roll a card back to an earlier snapshot."""
    for label, assessment_date in (("older", "2026-06-08"), ("newer", "2026-06-10")):
        cards = [_card("AAPL", "Technology", snapshot_date="2026-06-09")]
        assessments = {
            ("us_sp500", "AAPL"): {
                "snapshot_date": assessment_date,
                "health_verdict": "green",
                "ai_read": "Sturdy figures.",
            }
        }
        result = attach_assessments(cards, assessments)
        assert "health_verdict" not in result[0], label
        assert "ai_read" not in result[0], label


def test_attach_assessments_compares_snapshots_after_normalising_them() -> None:
    """A date column read back as a timestamp must not blank every verdict app-wide. The
    module already normalises this field for dedupe_to_latest_snapshot; the gate uses the same
    normaliser so a time component cannot silently suppress the whole deck."""
    cards = [_card("AAPL", "Technology", snapshot_date="2026-06-09")]
    assessments = {
        ("us_sp500", "AAPL"): {
            "snapshot_date": "2026-06-09T00:00:00+00:00",
            "health_verdict": "green",
            "ai_read": "Sturdy figures.",
        }
    }
    result = attach_assessments(cards, assessments)
    assert result[0]["health_verdict"] == "green"
