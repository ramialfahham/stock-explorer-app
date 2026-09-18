"""Stock Explorer — card discovery app (Streamlit + Supabase)."""

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
    skipped_keys_with_order,
)
from markets import eligible_counts_by_market, latest_snapshot_label
from nav_pages import NAV_PAGES, normalize_nav_page
from overflow_menu import render_overflow_menu
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
        "not_now_open": False,
        "not_now_focus_key": None,
        "search_selected": None,
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
    if "bottom_nav" in st.session_state:
        st.session_state["bottom_nav"] = normalize_nav_page(
            st.session_state.get("bottom_nav"),
            fallback=st.session_state["active_page"],
        )


# Short enough that a pipeline export shows up the same day without a redeploy, and short
# enough that ordinary traffic keeps querying Supabase -- the free tier pauses after ~7 idle
# days, so a long TTL would turn the cache into an outage risk (open item 6). Kept inside a
# 15-60 minute band; moving outside that band is a §6 decision, not a tuning choice.
_DECK_TTL_SECONDS = 30 * 60


@st.cache_data(ttl=_DECK_TTL_SECONDS, show_spinner=False)
def _cached_deck(_client) -> list[dict]:
    """Deck rows shared across ALL browser sessions on this instance.

    `_client` is underscore-prefixed so Streamlit skips hashing it; with no other argument the
    cache key is constant, which is the point -- the previous session_state cache made every
    first-time visitor re-download and re-dedupe the whole deck before anything rendered.
    """
    return fetch_deck(_client)


@st.cache_data(ttl=_DECK_TTL_SECONDS, show_spinner=False)
def _cached_card_detail(_client, market_code: str, ticker: str) -> dict | None:
    return fetch_card_detail(_client, market_code, ticker)


@st.cache_data(ttl=_DECK_TTL_SECONDS, show_spinner=False)
def _cached_descriptions_missing(_client) -> bool:
    return export_lacks_business_summary(_client)


def _descriptions_missing(client) -> bool:
    """The probe runs on every script run, not only when the menu is opened: a st.popover's
    body is computed eagerly unless it opts into `on_change="rerun"`. The cache is what keeps
    that to one round trip per TTL window. Catching OUTSIDE the cached call matters -- a
    transient PostgREST error raised through @st.cache_data is not stored, so the diagnostic
    retries on the next run instead of reporting "no problem" for the full TTL.

    A missing `business_summary` COLUMN is not a failure to swallow -- it IS the state the
    caption announces (an export predating migration 004), so it answers True. Any other
    error stays silent: showing an operator a data-quality alarm because of a transient
    network blip would be worse than showing nothing."""
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
        # Both copies hold the stale shape. Clearing only session_state would re-read the same
        # rows straight back out of the cross-session cache and trip this guard again on every
        # rerun -- a spin, not a recovery.
        _cached_deck.clear()
        cards = []
        st.session_state["all_cards"] = []
    if not cards:
        cards = _load_cards(client)
        st.session_state["all_cards"] = cards
    return cards


def _hydrate(client, card: dict | None) -> dict | None:
    """Swap a slim deck row for the full card row the card face needs.

    Falls back to the slim row on a fetch failure: a card missing its metrics still renders
    its name, sector and lead metric, which beats an exception on the only screen that
    matters. Reuses _load_cards' existing error wording rather than introducing a second
    string -- user-visible copy changes go through working agreement §6."""
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
    cards = _ensure_all_cards(client)
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
    shrink after a page index was chosen (a filter change, a save/skip, a shorter market), and
    an unclamped index would slice past the end into an empty page instead of showing something.
    """
    total_pages = _discover_page_count(len(pool))
    page = max(0, min(page, total_pages - 1))
    start = page * DISCOVER_PAGE_SIZE
    return pool[start : start + DISCOVER_PAGE_SIZE], page


def _cards_for_order(client, order: dict[tuple[str, str], str]) -> list[dict]:
    """Deck rows matching an (market_code, ticker) -> timestamp map, most recent first.
    Shared by Saved and the Not-now panel (issue #16) so the two lists can't diverge in how
    they resolve keys back to cards or order them."""
    cards = _ensure_all_cards(client)
    matched = [c for c in cards if (c["market_code"], c["ticker"]) in order]
    matched.sort(key=lambda c: order.get((c["market_code"], c["ticker"]), ""), reverse=True)
    return matched


def _saved_count(interactions: list[dict]) -> int:
    return len(saved_keys_with_order(interactions))


def _saved_cards(client, interactions: list[dict]) -> list[dict]:
    return _cards_for_order(client, saved_keys_with_order(interactions))


def _not_now_count(interactions: list[dict]) -> int:
    return len(skipped_keys_with_order(interactions))


def _not_now_cards(client, interactions: list[dict]) -> list[dict]:
    return _cards_for_order(client, skipped_keys_with_order(interactions))


def _card_key(card: dict) -> tuple[str, str]:
    return (card["market_code"], card["ticker"])


def _clear_saved_session() -> None:
    st.session_state["saved_focus_key"] = None


def brand_header_html(*, compact: bool = False) -> str:
    """compact: brand only, while a card is open on Discover or Saved. The tagline and
    disclosure stay on every list view, where each visit starts; on the card view they drop
    to save vertical space (owner composition call, docs/ui/discover_header.md)."""
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
        return bool(st.session_state.get("discover_focus_key")) or bool(
            st.session_state.get("search_selected")
        )
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
    st.markdown(
        f'<div class="ss-header-stats ss-header-stats--solo">'
        f"{html.escape(f'{remaining} match your filters')}</div>",
        unsafe_allow_html=True,
    )


def _render_saved_scope_stats(*, saved_count: int) -> None:
    st.markdown(
        f'<div class="ss-header-stats ss-header-stats--solo">'
        f"{html.escape(f'{saved_count} saved')}</div>",
        unsafe_allow_html=True,
    )


def _render_bottom_nav(*, saved_count: int, not_now_count: int, client) -> str:
    prior_active = normalize_nav_page(st.session_state.get("active_page"))
    if "bottom_nav" in st.session_state:
        st.session_state["bottom_nav"] = normalize_nav_page(
            st.session_state.get("bottom_nav"),
            fallback=prior_active,
        )

    st.markdown('<div class="ss-nav-row-marker"></div>', unsafe_allow_html=True)
    with st.container(horizontal=True, vertical_alignment="center", gap="small"):
        with st.container(width="stretch"):
            page = st.segmented_control(
                "Navigation",
                options=list(NAV_PAGES),
                default=prior_active,
                label_visibility="collapsed",
                key="bottom_nav",
            )
        st.markdown('<div class="ss-icon-btn-marker"></div>', unsafe_allow_html=True)
        with st.popover("⋯"):
            cards = _ensure_all_cards(client)
            render_overflow_menu(
                active_tab=normalize_nav_page(st.session_state.get("active_page")),
                saved_count=saved_count,
                not_now_count=not_now_count,
                cards=cards,
                eligible_counts=st.session_state.get("eligible_counts") or {},
                on_clear_saved=_clear_saved_session,
                on_open_not_now=_open_not_now_panel,
                descriptions_missing=_descriptions_missing(client),
            )
    selected = normalize_nav_page(
        page or st.session_state.get("bottom_nav"),
        fallback=prior_active,
    )
    if selected != prior_active:
        # A genuine tab switch abandons the Not-now overlay and any active search, the
        # same way it already abandons a focused Discover/Saved card -- otherwise the
        # reader would tap Saved and back to Discover and still be stuck showing old
        # search results, with no way out short of deleting the query by hand (found live
        # by the owner: clicking the already-active Discover pill is a no-op -- Streamlit's
        # segmented_control gives no signal that the same option was reselected, so a tab
        # click was never a reliable way to clear search in the first place).
        _close_not_now_panel()
        _clear_search()
    st.session_state["active_page"] = selected
    return selected


def _save_card(card: dict) -> None:
    """The one place "save" is recorded, from any surface (Discover's sticky action, the
    Not-now panel). Always also records "unskip": a card cannot be both currently-saved and
    currently-skipped at once, so saving a previously-skipped card must clear its skip
    status too, or it would stay stuck in the Not-now list after being saved (issue #16 --
    found by the e2e test this exact scenario writes, in the Not-now panel's own Save
    button; generalized here so no other Save button can reintroduce the same bug)."""
    append_interaction(card, "save")
    append_interaction(card, "unskip")


def _render_sticky_actions(card: dict) -> None:
    """Save or Not now, on the focus card. Both return to the list: Save excludes the
    ticker from the pool going forward (filter_pool's existing save exclusion); Not now is
    logged as an interaction and surfaces in the overflow menu's Not-now review list
    (issue #16), though it has no effect on THIS list -- there is no walk position left to
    deprioritize it from, so the reader free-scrolls to whatever's next instead of being
    pushed to one."""
    st.markdown('<div class="ss-action-shell"></div>', unsafe_allow_html=True)
    col_save, col_skip = st.columns(2)
    if col_save.button("Save", type="primary", use_container_width=True, key="discover_save"):
        _save_card(card)
        st.session_state["discover_focus_key"] = None
        st.rerun()

    if col_skip.button("Not now", use_container_width=True, key="discover_skip"):
        append_interaction(card, "skip")
        st.session_state["discover_focus_key"] = None
        st.rerun()


def _on_filter_change() -> None:
    st.session_state["discover_focus_key"] = None
    st.session_state["discover_page"] = 0


def _render_explore_filters(client) -> None:
    """Market/sector selectboxes and the metric-preset pills are deliberately unkeyed.
    A `key=`-bound widget's
    session_state entry is evicted by Streamlit whenever the widget isn't instantiated on the
    immediately preceding run -- true even with an explicit key, not just for unkeyed widgets --
    and this popover's content only renders while on Discover (frontend/app.py's own
    `if active == "Discover"` guard), so one glance at Saved was silently wiping the
    selection. Reading/writing the plain (non-widget) session_state value directly and seeding
    each render's `index=` from it survives that eviction, since nothing here is tied to a
    widget's own key lifecycle."""
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
            preset_ids = metric_preset_options()
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
    """Filtered list, or the focused card. Filters run in _discovery_page.

    Returns the focused card so _discovery_page can render sticky actions for it, or None
    when the list (not a focus card) is showing.
    """
    pool = _discover_pool(client)

    if not pool:
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
        row_ui.render_row_list(
            saved_cards,
            key_prefix="saved_row",
            row_key_fn=_saved_row_key,
            title_fn=lambda c: c.get("company_name") or c.get("ticker") or "Unknown",
            subtitle_fn=saved_row_subtitle,
            on_select=_select_saved_row,
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


def _open_not_now_panel() -> None:
    st.session_state["not_now_open"] = True
    st.session_state["not_now_focus_key"] = None


def _close_not_now_panel() -> None:
    st.session_state["not_now_open"] = False
    st.session_state["not_now_focus_key"] = None


def _select_not_now_row(card: dict) -> None:
    st.session_state["not_now_focus_key"] = _saved_row_key(card)


def _render_not_now_panel(client, interactions: list[dict]) -> None:
    """A "Not now" review list, structurally identical to `_render_saved_tab` (issue #16)
    -- reachable from the overflow menu on any tab, not a fourth NAV_PAGES entry, since
    `st.segmented_control`'s `default=` must be one of its own `options` and this panel
    isn't meant to appear as a bottom-nav pill. `_render_bottom_nav` closes it whenever the
    reader taps an actual nav tab, mirroring how switching tabs already abandons whatever
    focus state the prior tab was in."""
    not_now_cards = _not_now_cards(client, interactions)
    focus_key = st.session_state.get("not_now_focus_key")

    if focus_key:
        _render_back_row(
            key="not_now_back_to_list",
            saved_count=None,
            on_back=lambda: st.session_state.update({"not_now_focus_key": None}),
        )
    else:
        st.markdown('<div class="ss-back-row-marker"></div>', unsafe_allow_html=True)
        if st.button("← Close", key="not_now_close", use_container_width=False):
            _close_not_now_panel()
            st.rerun()

    if not not_now_cards:
        st.info("Nothing skipped yet -- companies you tap **Not now** on appear here.")
        return

    if not focus_key:
        row_ui.render_row_list(
            not_now_cards,
            key_prefix="not_now_row",
            row_key_fn=_saved_row_key,
            title_fn=lambda c: c.get("company_name") or c.get("ticker") or "Unknown",
            subtitle_fn=saved_row_subtitle,
            on_select=_select_not_now_row,
        )
        return

    market_code, ticker = focus_key.split("::", 1)
    selected = next(
        (
            c
            for c in not_now_cards
            if c["market_code"] == market_code and c["ticker"] == ticker
        ),
        None,
    )
    if not selected:
        st.session_state["not_now_focus_key"] = None
        st.rerun()
        return

    selected = _hydrate(client, selected)
    render_stock_card(selected, widget_key_prefix="not_now")
    col_save, col_remove = st.columns(2)
    with col_save:
        if st.button(
            "Save", key="not_now_save", type="primary", use_container_width=True
        ):
            st.session_state["not_now_focus_key"] = None
            _save_card(selected)
            st.rerun()
    with col_remove:
        if st.button("Remove", key="not_now_remove", use_container_width=True):
            st.session_state["not_now_focus_key"] = None
            append_interaction(selected, "unskip")
            st.rerun()


def _select_search_row(card: dict) -> None:
    st.session_state["search_selected"] = _card_key(card)


def _sync_search_query(query: str) -> None:
    """Persist the query and, if it changed, clear any pinned selection -- plain
    session_state bookkeeping, no Streamlit widget involved, so it's unit-tested directly
    (test_app.py). A later query that happens to re-match an old selection's ticker/name as a
    substring must not silently resurrect a card the reader never clicked for this query."""
    stored_query = st.session_state.get("search_query", "")
    if query != stored_query:
        st.session_state["search_query"] = query
        st.session_state["search_selected"] = None


def _clear_search() -> None:
    """The one way out of an active search, besides deleting every typed character by
    hand. Resets the plain mirror and DROPS the widget's own keyed state -- `del`, not
    assignment: Streamlit forbids writing to an already-instantiated keyed widget's
    session_state entry within the same run (the Clear button's own click handler runs
    after `_search_query_widget` already rendered this run), but removing the key entirely
    is allowed. On the next run (`st.rerun()`, called by every caller right after this),
    the key is simply absent, and `_search_query_widget`'s own reseed-when-absent logic
    (its own docstring) picks that up and seeds it from the now-empty `search_query`."""
    st.session_state["search_query"] = ""
    st.session_state["search_selected"] = None
    st.session_state.pop(_SEARCH_QUERY_WIDGET_KEY, None)


_SEARCH_QUERY_WIDGET_KEY = "search_query_widget"


def _search_query_widget(*, placeholder: str) -> str:
    """The `key=`-owned text_input behind Discover's persistent search box.

    NOT a `value=`-seeded unkeyed widget, despite that being this file's usual pattern for
    surviving cross-tab eviction (see `_render_explore_filters`). That pattern is wrong
    here specifically: an unkeyed widget's identity is a function of its `value=` argument,
    and this widget's seed (`search_query`) is written from the widget's OWN output on
    every edit (`_sync_search_query`) -- so the identity moves out from under itself after
    the very first keystroke, and Streamlit treats every following run as a brand-new
    widget that ignores whatever the frontend is trying to submit. Confirmed as a real, live
    bug against a running dev server, not an AppTest artifact: typing a second query, or
    clearing the box, silently did nothing (found when this app still had a separate
    standalone Search tab sharing this same widget, since removed as redundant -- the bug
    itself was in this widget, not in having two entry points).

    The fix: give the widget a stable `key=` so Streamlit owns its live value across edits
    with no identity churn, and re-seed `st.session_state[key]` from `search_query` only
    when the key is ABSENT (the tab-switch eviction case this file's usual pattern exists
    to survive) -- never unconditionally, which would reintroduce the same churn."""
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


def _render_search_results(client, query: str, *, key_prefix: str) -> None:
    """The list of matches for `query`. Never called with a selection already pinned --
    selecting a row moves to `_render_search_focused_card` on the next run instead of
    rendering the card inline here (issue: search-opened cards previously never entered a
    focused state, unlike every other card-open path in the app)."""
    cards = _ensure_all_cards(client)
    matches = _search_matches(cards, query)

    if not matches:
        st.warning(f"No matches for “{query}”.")
        return

    row_ui.render_row_list(
        matches[:20],
        key_prefix=key_prefix,
        row_key_fn=lambda c: f"{c['market_code']}_{c['ticker']}",
        title_fn=lambda c: c.get("company_name") or c.get("ticker") or "Unknown",
        subtitle_fn=saved_row_subtitle,
        on_select=_select_search_row,
    )


def _render_search_focused_card(client) -> None:
    """The focused view for a card opened from search results -- mirrors Discover's and
    Saved's own list-to-card focus pattern (hide the list, show a back row + the card)
    instead of leaving the search box and result row rendered above the card indefinitely,
    which was the one card-open path in the app that never got this treatment. Back
    returns to the search RESULTS for the same query, not to an empty box or the full
    Discover pool -- same as Discover's/Saved's own back buttons return to their own list,
    not further up."""
    query = st.session_state.get("search_query", "")
    cards = _ensure_all_cards(client)
    matches = _search_matches(cards, query)
    selected = st.session_state.get("search_selected")
    match = next((c for c in matches if _card_key(c) == selected), None)
    if not match:
        st.session_state["search_selected"] = None
        st.rerun()
        return

    _render_back_row(
        key="discover_search_back_to_results",
        saved_count=None,
        on_back=lambda: st.session_state.update({"search_selected": None}),
    )
    render_stock_card(_hydrate(client, match), widget_key_prefix="discover_search")


def _render_discover_search_box() -> str:
    """Persistent search above Discover's list (issue #20) -- always visible on the list
    view. The only search entry point; the earlier separate Search tab was redundant with
    this and removed.

    A "Clear" control appears once there's a query -- the explicit, always-visible way out
    of search a reader actually needs (found live by the owner: clicking the already-active
    Discover nav pill did nothing, since Streamlit's segmented_control gives no signal that
    the same option was reselected; a nav click was never going to be a reliable escape
    hatch, an explicit control in the search row is)."""
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

    # The brand header is already on screen (main() renders it first); the nav reads the same
    # session-state page the header's compact flag was computed from.
    active = _render_bottom_nav(
        saved_count=saved_count,
        not_now_count=_not_now_count(interactions),
        client=client,
    )

    if st.session_state.get("not_now_open"):
        _render_not_now_panel(client, interactions)
        return

    discover_focused = active == "Discover" and bool(
        st.session_state.get("discover_focus_key")
    )
    search_focused = active == "Discover" and bool(st.session_state.get("search_selected"))
    card_open = _card_open(active)

    if search_focused:
        # Same focus pattern as Discover's and Saved's own list-to-card transitions: the
        # search box and result row are not rendered at all while a search-opened card is
        # focused, not just visually hidden -- the widget's own reseed-when-key-absent
        # logic (_search_query_widget's docstring) restores its value once it reappears.
        _render_search_focused_card(client)
        return

    discover_search_query = ""
    if active == "Discover" and not discover_focused:
        discover_search_query = _render_discover_search_box()

    if discover_search_query:
        # Replaces Filters and the filtered pool entirely rather than showing alongside
        # them -- a market/sector filter is meaningless once the query is searching
        # globally (decided via AskUserQuestion, issue #20).
        _render_search_results(client, discover_search_query, key_prefix="discover_search")
        return

    if active == "Discover" and not discover_focused:
        _render_explore_filters(client)

    _sync_eligible_counts(client)
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
    # rerun and the deck fetch can take seconds, and Streamlit paints nothing until the first
    # element arrives. The header depends only on session state, so it goes out first.
    _render_brand_header(compact=_card_open(
        normalize_nav_page(
            st.session_state.get("bottom_nav") or st.session_state.get("active_page")
        )
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
