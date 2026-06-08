"""Tests for overflow menu copy helpers."""

from __future__ import annotations

import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "frontend"))

from explore_filters import ALL_MARKETS, ALL_SECTORS  # noqa: E402
from markets import latest_snapshot_label  # noqa: E402
from overflow_menu import (  # noqa: E402
    discover_scope_line,
    quick_tip_line,
    right_now_line,
)


def test_discover_scope_all_markets_sectors() -> None:
    line = discover_scope_line(
        market=ALL_MARKETS,
        sector=ALL_SECTORS,
        surprise_me=False,
    )
    assert line == "Exploring: All markets · All sectors"


def test_discover_scope_surprise_me() -> None:
    line = discover_scope_line(
        market=ALL_MARKETS,
        sector=ALL_SECTORS,
        surprise_me=True,
    )
    assert "Surprise me worldwide" in line
    assert "mixed markets" in line


def test_right_now_saved_tab() -> None:
    line = right_now_line(active_tab="Saved", saved_count=3)
    assert line == "3 saved companies on this device"
    assert "learning list" not in line.lower()


def test_right_now_saved_tab_singular() -> None:
    line = right_now_line(active_tab="Saved", saved_count=1)
    assert line == "1 saved company on this device"


def test_right_now_search_tab() -> None:
    line = right_now_line(active_tab="Search", saved_count=0)
    assert "five-metric snapshot" in line


def test_quick_tip_varies_by_tab() -> None:
    discover = quick_tip_line(active_tab="Discover")
    assert "Save keeps" in discover
    assert "learning list" not in discover.lower()
    assert "headlines" in quick_tip_line(active_tab="Saved")
    assert "five fundamentals" in quick_tip_line(active_tab="Search")


def test_latest_snapshot_label_picks_max_date() -> None:
    cards = [
        {"is_card_eligible": True, "snapshot_date": "2026-05-01"},
        {"is_card_eligible": True, "snapshot_date": "2026-06-08"},
        {"is_card_eligible": False, "snapshot_date": "2099-01-01"},
    ]
    label = latest_snapshot_label(cards)
    assert label == date(2026, 6, 8).strftime("%B %d, %Y")
