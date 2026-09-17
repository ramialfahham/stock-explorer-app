"""Bottom nav page normalization."""

from __future__ import annotations

from nav_pages import normalize_nav_page  # noqa: E402


def test_normalize_nav_page_stable_ids() -> None:
    assert normalize_nav_page("Discover") == "Discover"
    assert normalize_nav_page("Saved") == "Saved"


def test_normalize_nav_page_migrates_saved_count_label() -> None:
    assert normalize_nav_page("Saved (3)") == "Saved"
    assert normalize_nav_page("Saved (0)") == "Saved"


def test_normalize_nav_page_unknown_falls_back() -> None:
    """"Search" is also an unknown id now (the standalone tab was removed) -- a session
    that still has it stored from before the removal must fall back like any other
    unrecognized value, not resolve to a tab that no longer exists."""
    assert normalize_nav_page("Search", fallback="Discover") == "Discover"
    assert normalize_nav_page(None, fallback="Discover") == "Discover"
    assert normalize_nav_page("bogus", fallback="Discover") == "Discover"
