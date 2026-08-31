"""Tests for app.py's pure HTML-building and Discover-pagination helpers."""

from __future__ import annotations

from app import (
    DISCOVER_PAGE_SIZE,
    _discover_page_count,
    _discover_page_slice,
    brand_header_html,
)
from brand import PRODUCT_NAME, PRODUCT_TAGLINE


def test_brand_header_html_includes_the_disclaimer() -> None:
    """The header is the only place this renders now that the landing screen is gone."""
    html = brand_header_html()
    assert PRODUCT_NAME in html
    assert PRODUCT_TAGLINE in html
    assert "Not investment advice." in html


def test_brand_header_html_orders_name_then_tagline_then_disclaimer() -> None:
    html = brand_header_html()
    name_pos = html.index(PRODUCT_NAME)
    tagline_pos = html.index(PRODUCT_TAGLINE)
    disclaimer_pos = html.index("Not investment advice.")
    assert name_pos < tagline_pos < disclaimer_pos


# --- Discover list pagination (perf/paginate-discover-list) ---
# The list used to mount every filtered row's tap-target button unconditionally, which
# measured at ~2.4s before Streamlit even registered a click against the full ~923-row pool.
# Pagination caps the live widget count per render; these test the pure slicing/clamping logic,
# not the Streamlit-calling render function (see row_ui.py's own pure/render split for the
# established pattern this follows).


def test_discover_page_count_divides_evenly() -> None:
    assert _discover_page_count(DISCOVER_PAGE_SIZE * 3) == 3


def test_discover_page_count_rounds_up_a_partial_last_page() -> None:
    assert _discover_page_count(DISCOVER_PAGE_SIZE * 2 + 1) == 3


def test_discover_page_count_is_at_least_one_for_an_empty_pool() -> None:
    """An empty pool must never divide-by-zero a caller computing page fractions."""
    assert _discover_page_count(0) == 1


def test_discover_page_slice_returns_the_requested_page() -> None:
    pool = [{"ticker": str(i)} for i in range(DISCOVER_PAGE_SIZE * 2 + 5)]
    page_items, page = _discover_page_slice(pool, 1)
    assert page == 1
    assert len(page_items) == DISCOVER_PAGE_SIZE
    assert page_items[0]["ticker"] == str(DISCOVER_PAGE_SIZE)


def test_discover_page_slice_last_page_is_a_partial_page() -> None:
    pool = [{"ticker": str(i)} for i in range(DISCOVER_PAGE_SIZE * 2 + 5)]
    page_items, page = _discover_page_slice(pool, 2)
    assert page == 2
    assert len(page_items) == 5


def test_discover_page_slice_clamps_a_page_index_past_the_end() -> None:
    """The pool can shrink after a page index was chosen (a filter change, a save/skip, a
    shorter market) -- an unclamped index would slice past the end into an empty page instead
    of showing something."""
    pool = [{"ticker": str(i)} for i in range(10)]
    page_items, page = _discover_page_slice(pool, 99)
    assert page == 0
    assert len(page_items) == 10


def test_discover_page_slice_clamps_a_negative_page_index() -> None:
    pool = [{"ticker": str(i)} for i in range(10)]
    page_items, page = _discover_page_slice(pool, -1)
    assert page == 0
    assert len(page_items) == 10


def test_discover_page_slice_handles_an_empty_pool() -> None:
    page_items, page = _discover_page_slice([], 0)
    assert page == 0
    assert page_items == []
