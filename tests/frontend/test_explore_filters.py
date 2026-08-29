"""Tests for explore filter pool logic."""

from __future__ import annotations

from explore_filters import (  # noqa: E402
    ALL_MARKETS,
    ALL_SECTORS,
    attach_assessments,
    card_venue_line,
    cards_lack_business_summary,
    default_market_filter,
    filter_pool,
    filter_scope_summary,
    market_filter_options,
    walk_progress_line,
)
from markets import market_display_name


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
    options = market_filter_options()
    assert options[0][0] == ALL_MARKETS
    assert options[0][1] == "All markets"


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


def test_card_venue_line() -> None:
    """Market leads, position follows: the approved-mockup format (Option B)."""
    assert (
        card_venue_line(position=3, total=47, market_code="uk_ftse100")
        == "FTSE 100 · 3 of 47"
    )
    assert (
        card_venue_line(position=31, total=47, market_code="nl_aex")
        == "AEX · 31 of 47"
    )


def test_card_venue_line_is_empty_with_no_queue() -> None:
    assert card_venue_line(position=1, total=0, market_code="us_sp500") == ""


def test_card_venue_line_degrades_for_an_unknown_market() -> None:
    """A missing or unrecognized market_code must not crash the card render; it falls back
    to whatever `market_display_name` itself resolves to, rather than raising.

    Derives the expected prefix from `market_display_name` directly instead of hardcoding its
    return value, so this test exercises the composition, not `markets.py`'s own fallback
    choice, which is that module's concern to test.
    """
    assert card_venue_line(position=1, total=5, market_code=None) == (
        f"{market_display_name(None)} · 1 of 5"
    )
    assert card_venue_line(position=1, total=5, market_code="not_a_market") == (
        "Not A Market · 1 of 5"
    )


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
