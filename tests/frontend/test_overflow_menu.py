"""Tests for overflow menu copy helpers."""

from __future__ import annotations

from datetime import date

from explore_filters import ALL_MARKETS, ALL_SECTORS  # noqa: E402
from markets import latest_snapshot_label  # noqa: E402
from overflow_menu import (  # noqa: E402
    MENU_METRICS_LINE,
    discover_scope_line,
    quick_tip_line,
    right_now_line,
)


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


def test_right_now_search_tab() -> None:
    line = right_now_line(active_tab="Search", saved_count=0)
    assert "fundamentals snapshot" in line


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
    assert "complete set of fundamentals" in quick_tip_line(active_tab="Search")


def test_latest_snapshot_label_picks_max_date() -> None:
    cards = [
        {"is_card_eligible": True, "snapshot_date": "2026-05-01"},
        {"is_card_eligible": True, "snapshot_date": "2026-06-08"},
        {"is_card_eligible": False, "snapshot_date": "2099-01-01"},
    ]
    label = latest_snapshot_label(cards)
    assert label == date(2026, 6, 8).strftime("%B %d, %Y")
