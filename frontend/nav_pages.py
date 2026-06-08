"""Bottom navigation page ids and normalization."""

from __future__ import annotations

NAV_PAGES = ("Discover", "Saved", "Search")


def normalize_nav_page(value: object | None, *, fallback: str = "Discover") -> str:
    """Map widget/session values to a stable nav page id."""
    if isinstance(value, str) and value in NAV_PAGES:
        return value
    if isinstance(value, str) and value.startswith("Saved"):
        return "Saved"
    if fallback in NAV_PAGES:
        return fallback
    return "Discover"
