"""Tests for explore filter pool logic."""

from __future__ import annotations

from explore_filters import (  # noqa: E402
    ALL_MARKETS,
    ALL_SECTORS,
    attach_assessments,
    cards_lack_business_summary,
    default_market_filter,
    filter_pool,
    filter_scope_summary,
    market_filter_options,
    walk_progress_line,
)


def _card(ticker: str, sector: str, market: str = "us_sp500") -> dict:
    return {
        "market_code": market,
        "ticker": ticker,
        "sector": sector,
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


def test_cards_lack_business_summary_when_column_missing() -> None:
    cards = [_card("AAPL", "Technology")]
    assert cards_lack_business_summary(cards) is True


def test_cards_lack_business_summary_when_all_empty() -> None:
    cards = [{**_card("AAPL", "Technology"), "business_summary": "   "}]
    assert cards_lack_business_summary(cards) is True


def test_cards_lack_business_summary_when_populated() -> None:
    cards = [{**_card("AAPL", "Technology"), "business_summary": "Apple designs products."}]
    assert cards_lack_business_summary(cards) is False


def test_attach_assessments_copies_fields_on_match() -> None:
    cards = [_card("AAPL", "Technology")]
    assessments = {
        ("us_sp500", "AAPL"): {"health_verdict": "green", "ai_read": "Sturdy figures."}
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
    assessments = {("us_sp500", "AAPL"): {"health_verdict": "red", "ai_read": None}}
    result = attach_assessments(cards, assessments)
    assert result[0]["health_verdict"] == "red"
    assert result[0]["ai_read"] is None


def test_attach_assessments_does_not_mutate_the_original_card() -> None:
    card = _card("AAPL", "Technology")
    assessments = {("us_sp500", "AAPL"): {"health_verdict": "green", "ai_read": "text"}}
    attach_assessments([card], assessments)
    assert "health_verdict" not in card
