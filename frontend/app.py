"""Stock Explorer -- card discovery app (Streamlit + Supabase)."""

from __future__ import annotations

import html

import streamlit as st
from dotenv import load_dotenv

from browser_storage import (
    append_interaction,
    clear_interactions,
    ensure_interactions_loaded,
    flush_storage_writes,
    get_interactions,
    storage_sync_pending,
)
from brand import PRODUCT_NAME, PRODUCT_TAGLINE
from card_copy import (
    freshness_line,
    lead_metric_for_row,
    saved_row_subtitle,
    sector_headline,
)
from card_ui import render_stock_card
from explore_filters import (
    ALL_SECTORS,
    deck_rows_lack_columns,
    default_market_filter,
    filter_pool,
    filter_scope_summary,
    market_filter_options,
    metric_preset_label,
    metric_preset_options,
    saved_keys_with_order,
    sectors_for_market,
)
from markets import eligible_counts_by_market, latest_snapshot_label
from nav_pages import NAV_PAGES, normalize_nav_page
from overflow_menu import render_about_panel
import row_ui
from saved_news import render_saved_news
from settings import get_supabase_anon_key, get_supabase_url
from styles import inject_global_css
from supabase_cards import (
    DECK_COLUMNS,
    export_lacks_business_summary,
    is_undefined_column_error,
    fetch_card_detail,
    fetch_deck,
)
from supabase_client import get_anon_client
import timing

load_dotenv()

EXPLORE_DEFAULTS_VERSION = 5
CARDS_CACHE_VERSION = 3
DISCOVER_PAGE_SIZE = 30

st.set_page_config(
    page_title=PRODUCT_NAME,
    page_icon="📊",
    layout="centered",
    initial_sidebar_state="collapsed",
)


def _init_state() -> None:
    defaults = {
        "discover_focus_key": None,
        "saved_focus_key": None,
        "search_query": "",
        "active_page": "Discover",
        "explore_market": default_market_filter(),
        "explore_sector": ALL_SECTORS,
        "explore_metric_presets": [],
        "all_cards": [],
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

    if st.session_state.get("_explore_defaults_version", 0) < EXPLORE_DEFAULTS_VERSION:
        st.session_state["explore_market"] = default_market_filter()
        st.session_state["explore_sector"] = ALL_SECTORS
        st.session_state["_explore_defaults_version"] = EXPLORE_DEFAULTS_VERSION

    if st.session_state.get("_cards_cache_version", 0) < CARDS_CACHE_VERSION:
        st.session_state["all_cards"] = []
        st.session_state["_cards_cache_version"] = CARDS_CACHE_VERSION

    st.session_state["active_page"] = normalize_nav_page(st.session_state.get("active_page"))


# Bounded 15-60 min: longer risks masking a Supabase free-tier idle-pause (~7 days) as an
# outage; shorter defeats the cache. Widening the band is a §6 decision, not a tuning choice.
_DECK_TTL_SECONDS = 30 * 60


@st.cache_data(ttl=_DECK_TTL_SECONDS, show_spinner=False)
def _cached_deck(_client) -> list[dict]:
    """Deck rows shared across all browser sessions on this instance.

    `_client` is underscore-prefixed so Streamlit skips hashing it, making the cache key
    constant -- every session shares one cached deck instead of fetching its own.
    """
    return fetch_deck(_client)


@st.cache_data(ttl=_DECK_TTL_SECONDS, show_spinner=False)
def _cached_card_detail(_client, market_code: str, ticker: str) -> dict | None:
    return fetch_card_detail(_client, market_code, ticker)


@st.cache_data(ttl=_DECK_TTL_SECONDS, show_spinner=False)
def _cached_descriptions_missing(_client) -> bool:
    return export_lacks_business_summary(_client)


def _descriptions_missing(client) -> bool:
    """Whether the export is missing `business_summary` (predates migration 004).

    Runs every script run since a st.popover body evaluates eagerly, so caching bounds it
    to one round trip per TTL. Caught outside the cache because @st.cache_data drops a
    raised exception, so a transient failure retries instead of caching a false "no
    problem". Any other error stays silent rather than alarming on a network blip."""
    try:
        return _cached_descriptions_missing(client)
    except Exception as exc:  # noqa: BLE001
        return is_undefined_column_error(exc)


def _load_cards(client) -> list[dict]:
    try:
        return _cached_deck(client)
    except Exception as exc:  # noqa: BLE001
        st.error(f"Could not load cards from Supabase: {exc}")
        return []


def _ensure_all_cards(client) -> list[dict]:
    cards = st.session_state.get("all_cards") or []
    if cards and deck_rows_lack_columns(cards, DECK_COLUMNS):
        # Must clear both caches: clearing only session_state would re-read the same stale
        # rows straight back out of the cross-session cache and re-trip this guard.
        _cached_deck.clear()
        cards = []
        st.session_state["all_cards"] = []
    if not cards:
        cards = _load_cards(client)
        st.session_state["all_cards"] = cards
    return cards


def _hydrate(client, card: dict | None) -> dict | None:
    """Swap a slim deck row for the full card row the card face needs.

    Returns the slim row on fetch failure instead of raising, so the card still renders
    with reduced data. Reuses the existing "Could not load cards" wording rather than a
    new string -- user-visible copy changes need owner sign-off (working agreement §6)."""
    if not card:
        return card
    try:
        detail = _cached_card_detail(client, card["market_code"], card["ticker"])
    except Exception as exc:  # noqa: BLE001
        st.error(f"Could not load cards from Supabase: {exc}")
        return card
    return detail or card


def _explore_filters() -> tuple[str, str]:
    market = st.session_state.get("explore_market", default_market_filter())
    sector = st.session_state.get("explore_sector", ALL_SECTORS)
    return market, sector


def _explore_metric_presets() -> list[str]:
    return st.session_state.get("explore_metric_presets", [])


def _sync_eligible_counts(client) -> None:
    cards = _ensure_all_cards(client)
    st.session_state["eligible_counts"] = eligible_counts_by_market(cards)


def _discover_pool(client) -> list[dict]:
    """The rows Discover's list and its focused card draw from.

    A search query replaces market/sector/preset filtering entirely (matching the full
    deck) rather than combining with it, but both paths just decide which rows land in
    `pool` this run -- the same list, pagination, and focus mechanism render either way, so
    a card opened via search is exactly as saveable as one opened from the filtered list."""
    cards = _ensure_all_cards(client)
    query = st.session_state.get("search_query", "")
    if query:
        return _search_matches(cards, query)
    interactions = get_interactions()
    market, sector = _explore_filters()
    pool = filter_pool(
        cards,
        interactions,
        market_code=market,
        sector=sector,
        metric_presets=_explore_metric_presets(),
    )
    pool.sort(key=lambda c: (c.get("company_name") or c.get("ticker") or "").lower())
    return pool


def _discover_page_count(pool_size: int) -> int:
    """At least 1, even for an empty pool, so a caller never divides by zero."""
    return max(1, -(-pool_size // DISCOVER_PAGE_SIZE))


def _discover_page_slice(pool: list[dict], page: int) -> tuple[list[dict], int]:
    """The pool's rows for one page, plus the page index actually used.

    `page` is clamped to the pool's current bounds rather than trusted as-is: the pool can
    shrink after a page index was chosen (a filter change, a save, a shorter market), and
    an unclamped index would slice past the end into an empty page instead of showing something.
    """
    total_pages = _discover_page_count(len(pool))
    page = max(0, min(page, total_pages - 1))
    start = page * DISCOVER_PAGE_SIZE
    return pool[start : start + DISCOVER_PAGE_SIZE], page


def _cards_for_order(client, order: dict[tuple[str, str], str]) -> list[dict]:
    """Deck rows matching an (market_code, ticker) -> timestamp map, most recent first."""
    cards = _ensure_all_cards(client)
    matched = [c for c in cards if (c["market_code"], c["ticker"]) in order]
    matched.sort(key=lambda c: order.get((c["market_code"], c["ticker"]), ""), reverse=True)
    return matched


def _saved_count(interactions: list[dict]) -> int:
    return len(saved_keys_with_order(interactions))


def _saved_cards(client, interactions: list[dict]) -> list[dict]:
    return _cards_for_order(client, saved_keys_with_order(interactions))


def _clear_saved_session() -> None:
    st.session_state["saved_focus_key"] = None


def brand_header_html(*, compact: bool = False) -> str:
    """compact: brand only, while a card is open on Discover or Saved. The tagline and
    disclosure stay on every list view, dropping on the card view to save vertical space
    (see docs/ui/discover_header.md)."""
    if compact:
        return (
            '<div class="ss-brand-header ss-brand-header--compact">'
            f'<div class="ss-brand">{html.escape(PRODUCT_NAME)}</div>'
            "</div>"
        )
    return (
        '<div class="ss-brand-header">'
        f'<div class="ss-brand">{html.escape(PRODUCT_NAME)}</div>'
        f'<div class="ss-brand-tagline">{html.escape(PRODUCT_TAGLINE)}</div>'
        '<div class="ss-brand-disclaimer">Not investment advice.</div>'
        "</div>"
    )


def _render_brand_header(*, compact: bool = False) -> None:
    st.markdown(brand_header_html(compact=compact), unsafe_allow_html=True)


def _card_open(active: str) -> bool:
    if active == "Discover":
        return bool(st.session_state.get("discover_focus_key"))
    if active == "Saved":
        return bool(st.session_state.get("saved_focus_key"))
    return False


def _render_back_row(*, key: str, saved_count: int | None, on_back) -> None:
    """Back button, replacing the separate stats line while a card is open. saved_count is
    shown next to the button only on the Saved tab -- None on Discover, where the saved
    tally is not this screen's subject."""
    st.markdown('<div class="ss-back-row-marker"></div>', unsafe_allow_html=True)
    with st.container(horizontal=True, vertical_alignment="center", gap="small"):
        if st.button("← Back to list", key=key, use_container_width=False):
            on_back()
            st.rerun()
        if saved_count is not None:
            with st.container(width="stretch"):
                st.markdown(
                    f'<div class="ss-header-stats ss-header-stats--inline">'
                    f"{html.escape(f'{saved_count} saved')}</div>",
                    unsafe_allow_html=True,
                )


def _render_discover_scope_stats(*, remaining: int) -> None:
    label = f"{remaining} company" if remaining == 1 else f"{remaining} companies"
    st.markdown(
        f'<div class="ss-header-stats ss-header-stats--solo">'
        f"{html.escape(label)}</div>",
        unsafe_allow_html=True,
    )


def _render_saved_scope_stats(*, saved_count: int) -> None:
    """The saved count, with `Clear saved` beside it -- lives on the one tab it acts on,
    not the shared overflow menu. Confirms in place: swaps to a "Clear all N saved
    companies?" message with Cancel/Clear-all, no second popover."""
    with st.container(horizontal=True, vertical_alignment="center", gap="small"):
        with st.container(width="stretch"):
            st.markdown(
                f'<div class="ss-header-stats ss-header-stats--inline">'
                f"{html.escape(f'{saved_count} saved')}</div>",
                unsafe_allow_html=True,
            )
        if not st.session_state.get("confirm_clear_saved"):
            if st.button("Clear saved", key="saved_clear", use_container_width=False):
                st.session_state["confirm_clear_saved"] = True
                st.rerun()
    if st.session_state.get("confirm_clear_saved"):
        noun = "company" if saved_count == 1 else "companies"
        st.markdown(f"Clear all {saved_count} saved {noun}? This can't be undone.")
        col_cancel, col_confirm = st.columns(2)
        with col_cancel:
            if st.button("Cancel", key="saved_clear_cancel", use_container_width=True):
                st.session_state["confirm_clear_saved"] = False
                st.rerun()
        with col_confirm:
            if st.button("Clear all", key="saved_clear_confirm", use_container_width=True):
                # clear_interactions() ends with its own st.rerun(), which halts this run --
                # the flag reset and _clear_saved_session() must happen before calling it.
                st.session_state["confirm_clear_saved"] = False
                _clear_saved_session()
                clear_interactions()


def _go_to_nav_page(target: str) -> None:
    """Land on TARGET's plain list, whatever was open -- for both a genuine switch and a
    re-click of the already-active tab, since `st.button` can't tell the two apart from a
    click alone (see `_render_bottom_nav`)."""
    if target == "Discover":
        st.session_state["discover_focus_key"] = None
        _clear_search()
    else:
        st.session_state["saved_focus_key"] = None
    st.session_state["active_page"] = target


def _render_bottom_nav(*, saved_count: int, client) -> str:
    active = normalize_nav_page(st.session_state.get("active_page"))

    st.markdown('<div class="ss-nav-row-marker"></div>', unsafe_allow_html=True)
    with st.container(horizontal=True, vertical_alignment="center", gap="small"):
        # Plain st.button, not st.segmented_control: that widget only reports a NEW
        # selection, so re-tapping the already-active tab would return no signal at all.
        for page in NAV_PAGES:
            is_active = page == active
            if st.button(
                page,
                key=f"nav_{page.lower()}",
                type="primary" if is_active else "secondary",
                use_container_width=True,
            ):
                _go_to_nav_page(page)
                st.rerun()
        with st.popover("About"):
            cards = _ensure_all_cards(client)
            render_about_panel(
                cards=cards,
                counts=st.session_state.get("eligible_counts") or {},
                descriptions_missing=_descriptions_missing(client),
            )
    return active


def _save_card(card: dict) -> None:
    """The one place "save" is recorded, from any surface (Discover's sticky action)."""
    append_interaction(card, "save")


def _render_sticky_actions(card: dict) -> None:
    """The one action on a focus card: Save. Returns to the list, excluding the ticker
    from the pool going forward (filter_pool's existing save exclusion). Declining to save
    needs no separate button -- `← Back to list` already returns to the list unchanged."""
    st.markdown('<div class="ss-action-shell"></div>', unsafe_allow_html=True)
    if st.button("Save", type="primary", use_container_width=True, key="discover_save"):
        _save_card(card)
        st.session_state["discover_focus_key"] = None
        st.rerun()


def _on_filter_change() -> None:
    st.session_state["discover_focus_key"] = None
    st.session_state["discover_page"] = 0


def _render_explore_filters(client) -> None:
    """Market/sector selectboxes and the metric-preset pills are deliberately unkeyed.

    A `key=`-bound widget's session_state entry is evicted whenever the widget isn't
    instantiated on the immediately preceding run, and this popover only renders on
    Discover -- so a keyed widget would silently lose its selection on a glance at Saved.
    Reading/writing the plain session_state value and seeding `index=` from it each render
    survives that eviction instead."""
    cards = _ensure_all_cards(client)
    market, sector = _explore_filters()
    metric_presets = _explore_metric_presets()
    summary = filter_scope_summary(
        market_code=market, sector=sector, metric_presets=metric_presets
    )

    filter_btn, summary_col = st.columns([2, 5], vertical_alignment="center")
    with filter_btn:
        with st.popover("Filters"):
            market_labels = {code: label for code, label in market_filter_options(cards)}
            market_codes = [code for code, _ in market_filter_options(cards)]
            stored_market = st.session_state.get("explore_market", default_market_filter())
            if stored_market not in market_codes:
                stored_market = default_market_filter()
            selected_market = st.selectbox(
                "Market",
                options=market_codes,
                index=market_codes.index(stored_market),
                format_func=lambda code: market_labels[code],
            )
            if selected_market != stored_market:
                st.session_state["explore_market"] = selected_market
                _on_filter_change()
                st.rerun()
            sector_options = [ALL_SECTORS] + sectors_for_market(
                cards,
                market_code=selected_market,
            )
            stored_sector = st.session_state.get("explore_sector", ALL_SECTORS)
            if stored_sector not in sector_options:
                stored_sector = ALL_SECTORS
            selected_sector = st.selectbox(
                "Sector",
                options=sector_options,
                index=sector_options.index(stored_sector),
                format_func=lambda value: "All sectors" if value == ALL_SECTORS else value,
            )
            if selected_sector != stored_sector:
                st.session_state["explore_sector"] = selected_sector
                _on_filter_change()
                st.rerun()
            preset_ids = metric_preset_options(cards)
            stored_presets = [p for p in metric_presets if p in preset_ids]
            selected_presets = st.pills(
                "Metric filters",
                options=preset_ids,
                selection_mode="multi",
                default=stored_presets,
                format_func=metric_preset_label,
                label_visibility="collapsed",
            )
            if set(selected_presets) != set(stored_presets):
                st.session_state["explore_metric_presets"] = selected_presets
                _on_filter_change()
                st.rerun()
    with summary_col:
        st.markdown(
            f'<p class="ss-filter-summary">{html.escape(summary)}</p>',
            unsafe_allow_html=True,
        )


def _select_discover_row(card: dict) -> None:
    st.session_state["discover_focus_key"] = _saved_row_key(card)


def _render_discover_pagination(page: int, total_pages: int) -> None:
    """Previous/Next below the list. Hidden entirely, not just disabled, when the whole
    filtered pool already fits on one page -- a filtered scope small enough for that shouldn't
    show dead controls."""
    if total_pages <= 1:
        return
    prev_col, label_col, next_col = st.columns([2, 3, 2], vertical_alignment="center")
    with prev_col:
        if st.button(
            "Previous", disabled=page == 0, use_container_width=True, key="discover_page_prev"
        ):
            st.session_state["discover_page"] = page - 1
            st.rerun()
    with label_col:
        st.markdown(
            f'<p class="ss-discover-page-label">Page {page + 1} of {total_pages}</p>',
            unsafe_allow_html=True,
        )
    with next_col:
        if st.button(
            "Next",
            disabled=page >= total_pages - 1,
            use_container_width=True,
            key="discover_page_next",
        ):
            st.session_state["discover_page"] = page + 1
            st.rerun()


def _render_discover_tab(client) -> dict | None:
    """The list -- filtered, or search-matched, whichever `_discover_pool` currently
    returns -- or the focused card opened from it. Filters/search box render in
    _discovery_page.

    Returns the focused card so _discovery_page can render sticky actions for it, or None
    when the list (not a focus card) is showing.
    """
    pool = _discover_pool(client)
    query = st.session_state.get("search_query", "")

    if not pool:
        if query:
            st.warning(f"No matches for “{query}”.")
        else:
            st.info("No companies match this scope. Try another market, sector, or clear filters.")
        return None

    focus_key = st.session_state.get("discover_focus_key")

    if not focus_key:
        page_items, page = _discover_page_slice(pool, st.session_state.get("discover_page", 0))
        st.session_state["discover_page"] = page
        row_ui.render_rich_row_list(
            page_items,
            key_prefix="discover_row",
            row_key_fn=_saved_row_key,
            title_fn=lambda c: c.get("company_name") or c.get("ticker") or "Unknown",
            subtitle_fn=saved_row_subtitle,
            metric_fn=lead_metric_for_row,
            on_select=_select_discover_row,
        )
        _render_discover_pagination(page, _discover_page_count(len(pool)))
        return None

    market_code, ticker = focus_key.split("::", 1)
    selected = next(
        (c for c in pool if c["market_code"] == market_code and c["ticker"] == ticker),
        None,
    )
    if not selected:
        st.session_state["discover_focus_key"] = None
        st.rerun()
        return None

    _render_back_row(
        key="discover_back_to_list",
        saved_count=None,
        on_back=lambda: st.session_state.update({"discover_focus_key": None}),
    )

    selected = _hydrate(client, selected)
    render_stock_card(selected, widget_key_prefix="discover")
    return selected


def _saved_row_key(card: dict) -> str:
    return f"{card['market_code']}::{card['ticker']}"


def _select_saved_row(card: dict) -> None:
    st.session_state["saved_focus_key"] = _saved_row_key(card)


def _remove_saved_row(card: dict) -> None:
    append_interaction(card, "unsave")


def _render_saved_tab(client, interactions: list[dict]) -> None:
    saved_cards = _saved_cards(client, interactions)

    if not saved_cards:
        st.info("Nothing saved yet — tap **Save** in Discover to build your learning list on this device.")
        return

    focus_key = st.session_state.get("saved_focus_key")

    if focus_key:
        _render_back_row(
            key="saved_back_to_list",
            saved_count=_saved_count(interactions),
            on_back=lambda: st.session_state.update({"saved_focus_key": None}),
        )
    else:
        snapshot_label = latest_snapshot_label(saved_cards)
        if snapshot_label:
            st.markdown(
                f'<p class="ss-saved-list-fresh">Fundamentals as of '
                f"{html.escape(snapshot_label)}</p>",
                unsafe_allow_html=True,
            )
        row_ui.render_removable_row_list(
            saved_cards,
            key_prefix="saved_row",
            row_key_fn=_saved_row_key,
            title_fn=lambda c: c.get("company_name") or c.get("ticker") or "Unknown",
            subtitle_fn=saved_row_subtitle,
            on_select=_select_saved_row,
            on_remove=_remove_saved_row,
        )
        return

    market_code, ticker = focus_key.split("::", 1)
    selected = next(
        (
            c
            for c in saved_cards
            if c["market_code"] == market_code and c["ticker"] == ticker
        ),
        None,
    )
    if not selected:
        st.session_state["saved_focus_key"] = None
        st.rerun()
        return

    selected = _hydrate(client, selected)
    render_saved_news(selected, widget_key_prefix="saved")
    render_stock_card(selected, widget_key_prefix="saved")
    if st.button("Remove from saved", key="saved_remove_current", type="secondary"):
        st.session_state["saved_focus_key"] = None
        append_interaction(selected, "unsave")
        st.rerun()


def _sync_search_query(query: str) -> None:
    """Persist the query -- plain session_state bookkeeping, no Streamlit widget involved,
    so it's unit-tested directly (test_app.py). A query change naturally changes what
    `_discover_pool` returns, which `_render_discover_tab` already re-validates
    `discover_focus_key` against, so no separate focus-clearing logic is needed here."""
    st.session_state["search_query"] = query


def _clear_search() -> None:
    """Resets the plain mirror and drops the widget's own keyed state.

    Pops the key rather than assigning to it: Streamlit forbids writing to an
    already-instantiated keyed widget's session_state entry within the same run. The
    following `st.rerun()` leaves the key absent, which `_search_query_widget`'s own
    reseed-when-absent logic then picks up from the now-empty `search_query`."""
    st.session_state["search_query"] = ""
    st.session_state.pop(_SEARCH_QUERY_WIDGET_KEY, None)


_SEARCH_QUERY_WIDGET_KEY = "search_query_widget"


def _search_query_widget(*, placeholder: str) -> str:
    """The `key=`-owned text_input behind Discover's persistent search box.

    Deliberately not the unkeyed `value=`-seeded pattern used elsewhere (see
    `_render_explore_filters`): this widget's seed (`search_query`) is written from the
    widget's own output on every edit, so an unkeyed widget's identity would churn after
    the first keystroke and Streamlit would treat each run as a new widget, ignoring
    input. Instead a stable `key=` owns the live value, reseeded from `search_query` only
    when the key is absent (the tab-switch eviction case) -- never unconditionally, which
    would reintroduce the same churn."""
    if _SEARCH_QUERY_WIDGET_KEY not in st.session_state:
        st.session_state[_SEARCH_QUERY_WIDGET_KEY] = st.session_state.get("search_query", "")
    query = st.text_input(
        "Search",
        key=_SEARCH_QUERY_WIDGET_KEY,
        placeholder=placeholder,
        label_visibility="collapsed",
    ).strip()
    _sync_search_query(query)
    return query


def _search_matches(cards: list[dict], query: str) -> list[dict]:
    """Ticker/company-name substring match, case-insensitive, sorted by display name.
    Global lookup across the full deck -- not scoped to Discover's market/sector filter or
    its saved-ticker exclusion."""
    needle = query.lower()
    matches = [
        c
        for c in cards
        if needle in (c.get("ticker") or "").lower()
        or needle in (c.get("company_name") or "").lower()
    ]
    matches.sort(key=lambda c: (c.get("company_name") or c.get("ticker") or "").lower())
    return matches


def _render_discover_search_box() -> str:
    """Persistent search above Discover's list, always visible on the list view.

    A "Clear" control appears once there's a query -- an explicit, always-visible way out
    of search, since re-tapping the Discover nav pill is not a reliable escape hatch."""
    with st.container(horizontal=True, vertical_alignment="center", gap="small"):
        with st.container(width="stretch"):
            query = _search_query_widget(placeholder="Search ticker or company name")
        if query:
            if st.button("✕", key="discover_search_clear", help="Clear search"):
                _clear_search()
                st.rerun()
    return query


def _discovery_page(client) -> None:
    interactions = get_interactions()
    if storage_sync_pending():
        _sync_eligible_counts(client)

    loading = st.empty()
    if not st.session_state.get("all_cards"):
        loading.markdown('<p class="ss-loading">Loading cards</p>', unsafe_allow_html=True)
    _ensure_all_cards(client)
    loading.empty()
    timing.mark("deck")
    saved_count = _saved_count(interactions)
    # Ahead of the nav row, not after: the About popover it renders also reads
    # eligible_counts, so it needs this synced before that popover can render.
    _sync_eligible_counts(client)

    # The brand header is already on screen (main() renders it first); the nav reads the same
    # session-state page the header's compact flag was computed from.
    active = _render_bottom_nav(
        saved_count=saved_count,
        client=client,
    )

    discover_focused = active == "Discover" and bool(
        st.session_state.get("discover_focus_key")
    )
    card_open = _card_open(active)

    discover_search_query = ""
    if active == "Discover" and not discover_focused:
        discover_search_query = _render_discover_search_box()
        # A query replaces filter-narrowing entirely: a market/sector filter is
        # meaningless once the query is searching the full deck globally.
        if not discover_search_query:
            _render_explore_filters(client)

    remaining = len(_discover_pool(client)) if active == "Discover" and not discover_focused else 0
    if not card_open:
        if active == "Discover" and not discover_focused:
            _render_discover_scope_stats(remaining=remaining)
        elif active == "Saved":
            _render_saved_scope_stats(saved_count=saved_count)

    focused_card = None

    if active == "Discover":
        focused_card = _render_discover_tab(client)
    else:
        _render_saved_tab(client, interactions)

    if focused_card is not None:
        _render_sticky_actions(focused_card)


def main() -> None:
    timing.start_run()
    _init_state()
    inject_global_css()
    timing.mark("css")
    # First pixels before anything that can wait: the storage gate below may force a full
    # rerun and the deck fetch can take seconds, so the session-state-only header goes first.
    _render_brand_header(compact=_card_open(
        normalize_nav_page(st.session_state.get("active_page"))
    ))
    timing.mark("header")

    if not get_supabase_url() or not get_supabase_anon_key():
        st.error(
            "Missing SUPABASE_URL or SUPABASE_ANON_KEY. "
            "Add them under Streamlit app Settings → Secrets (see .streamlit/secrets.toml.example)."
        )
        return

    ensure_interactions_loaded()
    timing.mark("cookies")

    client = get_anon_client()
    _discovery_page(client)
    flush_storage_writes()
    timing.mark("page")
    timing.render_report()


if __name__ == "__main__":
    main()
