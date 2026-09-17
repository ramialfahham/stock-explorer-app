"""Tests for overflow menu copy helpers."""

from __future__ import annotations

from datetime import date

from explore_filters import ALL_MARKETS, ALL_SECTORS  # noqa: E402
from markets import eligible_breakdown_lines, latest_snapshot_label  # noqa: E402
from overflow_menu import (  # noqa: E402
    MENU_METRICS_LINE,
    discover_scope_line,
    markets_line,
    quick_tip_line,
    right_now_line,
)


def test_markets_line_names_only_markets_that_have_cards() -> None:
    """The coverage line is derived, and this is the property that makes deriving worth it.

    A market is onboarded on one branch and first exports cards on the next production run. A
    line built from the registry or from `MARKET_DISPLAY_NAMES` claims coverage in that gap; this
    one cannot, because it only ever names keys of the counts dict.
    """
    line = markets_line({"us_sp500": 400, "de_dax": 39})
    assert line == "Markets: S&P 500, DAX"
    assert "AEX" not in line and "SMI" not in line


def test_markets_line_puts_the_hero_market_first() -> None:
    assert markets_line({"de_dax": 39, "us_sp500": 400}).startswith("Markets: S&P 500")


def test_markets_line_is_empty_without_cards() -> None:
    """Before the first sync `eligible_counts` is {}. Saying nothing beats claiming coverage."""
    assert markets_line({}) == ""


def test_markets_line_and_the_breakdown_cannot_disagree() -> None:
    """Both lines render in the same expander, so a drifted order is visible to one user.

    They shared a copied sort key in two modules until `markets_in_deck_order` was extracted.
    This pins the property rather than the extraction, so it still holds if either is rewritten.
    """
    counts = {"jp_nikkei225": 60, "us_sp500": 400, "au_asx200": 180, "de_dax": 39}
    from_line = markets_line(counts).removeprefix("Markets: ").split(", ")
    from_breakdown = [entry.rsplit(": ", 1)[0] for entry in eligible_breakdown_lines(counts)]
    assert from_line == from_breakdown


def test_discover_scope_all_markets_sectors() -> None:
    line = discover_scope_line(
        market=ALL_MARKETS,
        sector=ALL_SECTORS,
    )
    assert line == "Exploring: All markets · All sectors"


def test_right_now_saved_tab() -> None:
    line = right_now_line(active_tab="Saved", saved_count=3)
    assert line == "3 saved companies on this device"
    assert "learning list" not in line.lower()


def test_right_now_saved_tab_singular() -> None:
    line = right_now_line(active_tab="Saved", saved_count=1)
    assert line == "1 saved company on this device"


def test_menu_metrics_line_has_no_stale_metric_count() -> None:
    """Regression guard: this constant ("About the data" menu section) has been
    rewritten multiple times in one task alone to drop a stale "five" metric-count
    claim, each time caught only by manual inspection, not a test — the card's
    per-company-type metric count varies (8/7/4, never exactly 5), so this must
    never assert a specific number again."""
    assert "five" not in MENU_METRICS_LINE.lower()
    assert "—" not in MENU_METRICS_LINE
    assert MENU_METRICS_LINE == "Fundamentals per company, no substitutes"


def test_quick_tip_varies_by_tab() -> None:
    discover = quick_tip_line(active_tab="Discover")
    assert "Save keeps" in discover
    assert "learning list" not in discover.lower()
    assert "headlines" in quick_tip_line(active_tab="Saved")


def test_latest_snapshot_label_picks_max_date() -> None:
    cards = [
        {"is_card_eligible": True, "snapshot_date": "2026-05-01"},
        {"is_card_eligible": True, "snapshot_date": "2026-06-08"},
        {"is_card_eligible": False, "snapshot_date": "2099-01-01"},
    ]
    label = latest_snapshot_label(cards)
    assert label == date(2026, 6, 8).strftime("%B %d, %Y")
