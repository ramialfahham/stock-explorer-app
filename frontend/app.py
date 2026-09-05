"""Stock Explorer — card discovery app (Streamlit + Supabase)."""

from __future__ import annotations

import html

import streamlit as st
from dotenv import load_dotenv

from browser_storage import (
    append_interaction,
    clear_interactions,
    ensure_interactions_loaded,
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
    cards_lack_business_summary,
    default_market_filter,
    filter_pool,
    filter_scope_summary,
    market_filter_options,
    saved_keys_with_order,
    sectors_for_market,
)
from markets import eligible_counts_by_market, latest_snapshot_label
from nav_pages import NAV_PAGES, normalize_nav_page
from overflow_menu import render_overflow_menu
import row_ui
from saved_news import render_saved_news
from settings import get_supabase_anon_key, get_supabase_url
from styles import inject_global_css
from supabase_cards import fetch_eligible_cards_with_assessments
from supabase_client import get_anon_client

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
        "search_selected": None,
        "search_query": "",
        "active_page": "Discover",
        "explore_market": default_market_filter(),
        "explore_sector": ALL_SECTORS,
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


def _load_cards(client) -> list[dict]:
    try:
        return fetch_eligible_cards_with_assessments(client)
    except Exception as exc:  # noqa: BLE001
        st.error(f"Could not load cards from Supabase: {exc}")
        return []


def _ensure_all_cards(client) -> list[dict]:
    cards = st.session_state.get("all_cards") or []
    if cards and cards_lack_business_summary(cards):
        cards = []
        st.session_state["all_cards"] = []
    if not cards:
        cards = _load_cards(client)
        st.session_state["all_cards"] = cards
    return cards


def _explore_filters() -> tuple[str, str]:
    market = st.session_state.get("explore_market", default_market_filter())
    sector = st.session_state.get("explore_sector", ALL_SECTORS)
    return market, sector


def _sync_eligible_counts(client) -> None:
    cards = _ensure_all_cards(client)
    st.session_state["eligible_counts"] = eligible_counts_by_market(cards)


def _discover_pool(client) -> list[dict]:
    cards = _ensure_all_cards(client)
    interactions = get_interactions()
    market, sector = _explore_filters()
    pool = filter_pool(cards, interactions, market_code=market, sector=sector)
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


def _saved_count(interactions: list[dict]) -> int:
    return len(saved_keys_with_order(interactions))


def _saved_cards(client, interactions: list[dict]) -> list[dict]:
    save_order = saved_keys_with_order(interactions)
    cards = _ensure_all_cards(client)
    saved = [c for c in cards if (c["market_code"], c["ticker"]) in save_order]
    saved.sort(
        key=lambda c: save_order.get((c["market_code"], c["ticker"]), ""),
        reverse=True,
    )
    return saved


def _card_key(card: dict) -> tuple[str, str]:
    return (card["market_code"], card["ticker"])


def _clear_saved_session() -> None:
    st.session_state["saved_focus_key"] = None


def brand_header_html() -> str:
    return (
        '<div class="ss-brand-header">'
        f'<div class="ss-brand">{html.escape(PRODUCT_NAME)}</div>'
        f'<div class="ss-brand-tagline">{html.escape(PRODUCT_TAGLINE)}</div>'
        '<div class="ss-brand-disclaimer">Not investment advice.</div>'
        "</div>"
    )


def _render_brand_header() -> None:
    st.markdown(brand_header_html(), unsafe_allow_html=True)


def _render_scope_stats(*, remaining: int, saved_count: int, show_remaining: bool) -> None:
    if show_remaining:
        line = f"{remaining} match your filters · {saved_count} saved"
    else:
        line = f"{saved_count} saved"
    st.markdown(
        f'<div class="ss-header-stats ss-header-stats--solo">{html.escape(line)}</div>',
        unsafe_allow_html=True,
    )


def _render_bottom_nav(*, saved_count: int, client) -> str:
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
                cards=cards,
                eligible_counts=st.session_state.get("eligible_counts") or {},
                on_clear_saved=_clear_saved_session,
            )
    selected = normalize_nav_page(
        page or st.session_state.get("bottom_nav"),
        fallback=prior_active,
    )
    st.session_state["active_page"] = selected
    return selected


def _render_sticky_actions(card: dict) -> None:
    """Save or Not now, on the focus card. Both return to the list: Save excludes the
    ticker from the pool going forward (filter_pool's existing save exclusion); Not now is
    logged as an interaction but has no visible effect on the list; there is no walk
    position left to deprioritize it from, so the reader free-scrolls to whatever's next
    instead of being pushed to one."""
    st.markdown('<div class="ss-action-shell"></div>', unsafe_allow_html=True)
    col_save, col_skip = st.columns(2)
    if col_save.button("Save", type="primary", use_container_width=True, key="discover_save"):
        append_interaction(card, "save")
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
    """Market/sector selectboxes are deliberately unkeyed. A `key=`-bound widget's
    session_state entry is evicted by Streamlit whenever the widget isn't instantiated on the
    immediately preceding run -- true even with an explicit key, not just for unkeyed widgets --
    and this popover's content only renders while on Discover (frontend/app.py's own
    `if active == "Discover"` guard), so one glance at Saved or Search was silently wiping the
    selection. Reading/writing the plain (non-widget) session_state value directly and seeding
    each render's `index=` from it survives that eviction, since nothing here is tied to a
    widget's own key lifecycle."""
    cards = _ensure_all_cards(client)
    market, sector = _explore_filters()
    summary = filter_scope_summary(market_code=market, sector=sector)

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

    if st.button("← Back to list", key="discover_back_to_list", use_container_width=False):
        st.session_state["discover_focus_key"] = None
        st.rerun()

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
        if st.button("← Back to list", key="saved_back_to_list", use_container_width=False):
            st.session_state["saved_focus_key"] = None
            st.rerun()
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

    render_saved_news(selected, widget_key_prefix="saved")
    render_stock_card(selected, widget_key_prefix="saved")
    if st.button("Remove from saved", key="saved_remove_current", type="secondary"):
        st.session_state["saved_focus_key"] = None
        append_interaction(selected, "unsave")
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


def _render_search_tab(client) -> None:
    """Unkeyed for the same reason as `_render_explore_filters`'s market/sector
    selectboxes -- this tab's content only renders while Search is the active tab, so a
    `key=`-bound text_input would lose its typed text on every visit to Discover or Saved.
    Reading/writing `search_query` as a plain session_state value and seeding `value=` from it
    survives that."""
    query = st.text_input(
        "Search",
        value=st.session_state.get("search_query", ""),
        placeholder="Ticker or company name",
        label_visibility="collapsed",
    ).strip()
    _sync_search_query(query)

    if not query:
        return

    needle = query.lower()
    cards = _ensure_all_cards(client)
    matches = [
        c
        for c in cards
        if needle in (c.get("ticker") or "").lower()
        or needle in (c.get("company_name") or "").lower()
    ]
    matches.sort(key=lambda c: (c.get("company_name") or c.get("ticker") or "").lower())

    if not matches:
        st.warning(f"No matches for “{query}”.")
        return

    row_ui.render_row_list(
        matches[:20],
        key_prefix="search",
        row_key_fn=lambda c: f"{c['market_code']}_{c['ticker']}",
        title_fn=lambda c: c.get("company_name") or c.get("ticker") or "Unknown",
        subtitle_fn=saved_row_subtitle,
        on_select=_select_search_row,
    )

    selected = st.session_state.get("search_selected")
    if selected:
        match = next((c for c in matches if _card_key(c) == selected), None)
        if match:
            render_stock_card(match, widget_key_prefix="search")


def _discovery_page(client) -> None:
    interactions = get_interactions()
    if storage_sync_pending():
        _sync_eligible_counts(client)

    _ensure_all_cards(client)
    saved_count = _saved_count(interactions)

    _render_brand_header()
    active = _render_bottom_nav(saved_count=saved_count, client=client)

    discover_focused = active == "Discover" and bool(
        st.session_state.get("discover_focus_key")
    )

    if active == "Discover" and not discover_focused:
        _render_explore_filters(client)

    _sync_eligible_counts(client)
    remaining = len(_discover_pool(client)) if active == "Discover" and not discover_focused else 0
    _render_scope_stats(
        remaining=remaining,
        saved_count=saved_count,
        show_remaining=active == "Discover" and not discover_focused,
    )

    focused_card = None

    if active == "Discover":
        focused_card = _render_discover_tab(client)
    elif active == "Saved":
        _render_saved_tab(client, interactions)
    else:
        _render_search_tab(client)

    if focused_card is not None:
        _render_sticky_actions(focused_card)


def main() -> None:
    _init_state()
    inject_global_css()

    if not get_supabase_url() or not get_supabase_anon_key():
        st.error(
            "Missing SUPABASE_URL or SUPABASE_ANON_KEY. "
            "Add them under Streamlit app Settings → Secrets (see .streamlit/secrets.toml.example)."
        )
        return

    ensure_interactions_loaded()

    client = get_anon_client()
    _discovery_page(client)


if __name__ == "__main__":
    main()
