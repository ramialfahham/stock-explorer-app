"""Tests for app.py's pure HTML-building, Discover-pagination, and Search-state helpers."""

from __future__ import annotations

import pytest
import streamlit as st

import app as app_module
from app import (
    DISCOVER_PAGE_SIZE,
    _discover_page_count,
    _discover_page_slice,
    _sync_search_query,
    _card_open,
    brand_header_html,
)
from brand import PRODUCT_NAME, PRODUCT_TAGLINE
from supabase_cards import DECK_COLUMNS


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


def test_compact_brand_header_is_the_name_alone() -> None:
    """While a card is open the tagline and disclosure give way to the first metric value;
    both stay on every list view, where each visit starts (docs/ui/discover_header.md)."""
    html = brand_header_html(compact=True)
    assert PRODUCT_NAME in html
    assert PRODUCT_TAGLINE not in html
    assert "Not investment advice." not in html
    assert "ss-brand-header--compact" in html
    assert "ss-brand-header--compact" not in brand_header_html()


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


# --- _sync_search_query: plain session_state bookkeeping, no Streamlit widget involved,
# extracted from _render_search_tab specifically so this state-transition is unit-tested
# directly rather than folded into the "Streamlit widget lifecycle, can't unit-test" exemption
# that genuinely applies to the rest of that function's rendering.


@pytest.fixture(autouse=True)
def _clear_search_session_state():
    st.session_state.clear()
    yield
    st.session_state.clear()


def test_sync_search_query_first_call_persists_the_query() -> None:
    _sync_search_query("Apple")
    assert st.session_state["search_query"] == "Apple"


def test_sync_search_query_unchanged_query_leaves_selection_alone() -> None:
    st.session_state["search_query"] = "Apple"
    st.session_state["search_selected"] = ("us_sp500", "AAPL")
    _sync_search_query("Apple")
    assert st.session_state["search_selected"] == ("us_sp500", "AAPL")


def test_sync_search_query_changed_query_clears_a_pinned_selection() -> None:
    """The regression this fix targets: searching "App" after Apple -> Microsoft must not
    silently resurrect Apple's card just because "App" re-matches it as a substring."""
    st.session_state["search_query"] = "Microsoft"
    st.session_state["search_selected"] = ("us_sp500", "AAPL")
    _sync_search_query("App")
    assert st.session_state["search_query"] == "App"
    assert st.session_state["search_selected"] is None


def test_sync_search_query_clearing_the_box_also_clears_a_pinned_selection() -> None:
    st.session_state["search_query"] = "Apple"
    st.session_state["search_selected"] = ("us_sp500", "AAPL")
    _sync_search_query("")
    assert st.session_state["search_query"] == ""
    assert st.session_state["search_selected"] is None


# --- _ensure_all_cards cache invalidation (perf/first-visit-card-load) ---
# The deck is fetched once and reused. The guard that decides "this cached deck is the wrong
# shape, refetch" used to look for `business_summary`, which the deck deliberately no longer
# carries -- left as it was, it would have fired on every rerun and made the cache a no-op,
# which is the exact cost this task exists to remove. These two tests pin both directions.


def _slim_deck_row(**overrides) -> dict:
    row = {column: None for column in DECK_COLUMNS}
    row.update({"market_code": "us_sp500", "ticker": "AAPL", "is_card_eligible": True})
    row.update(overrides)
    return row


def _counting_fetch(deck: list[dict], calls: list[int]):
    """Patched BELOW app.py's @st.cache_data wrapper, at `app_module.fetch_deck` (the name
    app.py bound at import), so these tests run against the real cache. Patching
    `_cached_deck` itself would replace exactly the layer whose invalidation is under test."""

    def _fetch(_client) -> list[dict]:
        calls.append(1)
        return list(deck)

    return _fetch


@pytest.fixture
def clean_caches():
    """A finalizer, not a trailing call: st.cache_data is global and constant-keyed here, so a
    failing assertion would otherwise leak a populated deck into every later test."""
    st.cache_data.clear()
    st.session_state.clear()
    yield
    st.cache_data.clear()
    st.session_state.clear()


def test_ensure_all_cards_fetches_a_slim_deck_only_once(
    monkeypatch: pytest.MonkeyPatch, clean_caches: None
) -> None:
    """Mutation-verified: reverting deck_rows_lack_columns to the old
    `any("business_summary" not in card ...)` check makes this fail with 3 fetches instead of
    1. (Adding a column to DECK_COLUMNS would NOT catch it -- _slim_deck_row derives its keys
    from DECK_COLUMNS, so the row grows with it.)"""
    calls: list[int] = []
    monkeypatch.setattr(app_module, "fetch_deck", _counting_fetch([_slim_deck_row()], calls))

    client = object()
    app_module._ensure_all_cards(client)
    app_module._ensure_all_cards(client)
    app_module._ensure_all_cards(client)

    assert len(calls) == 1


def test_ensure_all_cards_clears_the_shared_cache_not_just_session_state(
    monkeypatch: pytest.MonkeyPatch, clean_caches: None
) -> None:
    """The stale shape lives in BOTH the session_state copy and the cross-session cache.
    Dropping only session_state re-reads the same rows out of the cache and trips the guard
    again on the next rerun -- a spin, not a recovery. Mutation check: remove
    `_cached_deck.clear()` from _ensure_all_cards and the second fetch never happens."""
    calls: list[int] = []
    monkeypatch.setattr(app_module, "fetch_deck", _counting_fetch([_slim_deck_row()], calls))

    client = object()
    app_module._ensure_all_cards(client)
    assert len(calls) == 1

    st.session_state["all_cards"] = [{"market_code": "us_sp500", "ticker": "AAPL"}]
    app_module._ensure_all_cards(client)

    assert len(calls) == 2


def test_descriptions_missing_reports_true_on_a_pre_004_schema(
    monkeypatch: pytest.MonkeyPatch, clean_caches: None
) -> None:
    """An export predating migration 004 has no `business_summary` column, so the probe raises
    42703. That IS the state the overflow-menu caption announces -- swallowing it into False
    made the diagnostic fail open on the one failure it exists to report."""

    class _ApiError(Exception):
        code = "42703"

    def _raise(_client):
        raise _ApiError("column mart_stock_cards.business_summary does not exist")

    monkeypatch.setattr(app_module, "export_lacks_business_summary", _raise)
    assert app_module._descriptions_missing(object()) is True


def test_descriptions_missing_stays_quiet_on_a_transient_failure(
    monkeypatch: pytest.MonkeyPatch, clean_caches: None
) -> None:
    def _raise(_client):
        raise TimeoutError("connection reset")

    monkeypatch.setattr(app_module, "export_lacks_business_summary", _raise)
    assert app_module._descriptions_missing(object()) is False


# --- _card_open: what decides the compact header, read from session state before the nav
# widget renders (see _discovery_page). Plain state, no widget, so it is unit-tested here.


def test_card_open_on_discover_follows_the_discover_focus_key() -> None:
    assert _card_open("Discover") is False
    st.session_state["discover_focus_key"] = "us_sp500::MMM"
    assert _card_open("Discover") is True
    assert _card_open("Saved") is False, "a Discover focus does not compact the Saved list"


def test_card_open_on_saved_follows_the_saved_focus_key() -> None:
    st.session_state["saved_focus_key"] = "us_sp500::MMM"
    assert _card_open("Saved") is True
    assert _card_open("Discover") is False


def test_card_open_is_never_true_on_search() -> None:
    """Search renders a card under its results, not as a view of its own, so the header
    stays full there."""
    st.session_state["search_selected"] = "us_sp500::MMM"
    st.session_state["discover_focus_key"] = "us_sp500::MMM"
    assert _card_open("Search") is False
