"""Bottom nav page normalization."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FRONTEND = ROOT / "frontend"
sys.path.insert(0, str(FRONTEND))

from nav_pages import normalize_nav_page  # noqa: E402


def test_normalize_nav_page_stable_ids() -> None:
    assert normalize_nav_page("Discover") == "Discover"
    assert normalize_nav_page("Saved") == "Saved"
    assert normalize_nav_page("Search") == "Search"


def test_normalize_nav_page_migrates_saved_count_label() -> None:
    assert normalize_nav_page("Saved (3)") == "Saved"
    assert normalize_nav_page("Saved (0)") == "Saved"


def test_normalize_nav_page_unknown_falls_back() -> None:
    assert normalize_nav_page(None, fallback="Search") == "Search"
    assert normalize_nav_page("bogus", fallback="Discover") == "Discover"
