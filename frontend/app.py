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
from card_copy import freshness_line, saved_row_subtitle, sector_headline
from card_ui import render_stock_card
from discovery_queue import build_queue
from explore_filters import (
    ALL_MARKETS,
    ALL_SECTORS,
    cards_lack_business_summary,
    default_market_filter,
    filter_pool,
    filter_scope_summary,
    market_filter_options,
    sectors_for_market,
    walk_progress_line,
)
from landing import render_landing
from markets import HERO_MARKET_CODE, eligible_counts_by_market, latest_snapshot_label
from nav_pages import NAV_PAGES, normalize_nav_page
from overflow_menu import render_overflow_menu
from saved_news import render_saved_news
from settings import get_supabase_anon_key, get_supabase_url
from styles import inject_global_css
from supabase_cards import fetch_eligible_cards
from supabase_client import get_anon_client

load_dotenv()

EXPLORE_DEFAULTS_VERSION = 5
CARDS_CACHE_VERSION = 2

st.set_page_config(
    page_title=PRODUCT_NAME,
    page_icon="📊",
    layout="centered",
    initial_sidebar_state="collapsed",
)


def _init_state() -> None:
    defaults = {
        "queue": [],
        "queue_index": 0,
        "market_index": 0,
        "sector_shown": {},
        "saved_focus_key": None,
        "search_selected": None,
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
        return fetch_eligible_cards(client)
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


def _refresh_queue(client, *, interactions: list[dict] | None = None) -> None:
    cards = _ensure_all_cards(client)
    if interactions is None:
        interactions = get_interactions()
    counts = eligible_counts_by_market(cards)
    st.session_state["eligible_counts"] = counts

    market, sector = _explore_filters()
    pool = filter_pool(
        cards,
        interactions,
        market_code=market,
        sector=sector,
    )
    start_market = None if market == ALL_MARKETS else market
    st.session_state["queue"] = build_queue(
        pool,
        interactions,
        market_index=st.session_state["market_index"],
        sector_shown=st.session_state["sector_shown"],
        start_market=start_market or HERO_MARKET_CODE,
    )
    st.session_state["queue_index"] = min(
        st.session_state["queue_index"],
        max(len(st.session_state["queue"]) - 1, 0),
    )


def _sync_discover_queue(client, *, interactions: list[dict] | None = None) -> None:
    """Rebuild walk queue from current filter session state."""
    _refresh_queue(client, interactions=interactions)


def _scoped_remaining() -> int:
    return max(len(st.session_state["queue"]) - st.session_state["queue_index"], 0)


def _reset_walk_state() -> None:
    """Reset walk pointers only — queue rebuild happens after filters render."""
    st.session_state["queue_index"] = 0
    st.session_state["market_index"] = 0
    st.session_state["sector_shown"] = {}


def _start_over() -> None:
    _reset_walk_state()


def _saved_count(interactions: list[dict]) -> int:
    return sum(1 for row in interactions if row.get("action") == "save")


def _saved_cards(client, interactions: list[dict]) -> list[dict]:
    saved_keys = {
        (i["market_code"], i["ticker"]) for i in interactions if i.get("action") == "save"
    }
    save_order: dict[tuple[str, str], str] = {}
    for row in interactions:
        if row.get("action") != "save":
            continue
        key = (row["market_code"], row["ticker"])
        created = row.get("created_at") or ""
        if key not in save_order or created >= save_order[key]:
            save_order[key] = created

    cards = _ensure_all_cards(client)
    saved = [c for c in cards if (c["market_code"], c["ticker"]) in saved_keys]
    saved.sort(
        key=lambda c: save_order.get((c["market_code"], c["ticker"]), ""),
        reverse=True,
    )
    return saved


def _card_key(card: dict) -> tuple[str, str]:
    return (card["market_code"], card["ticker"])


def _clear_saved_session() -> None:
    st.session_state["saved_focus_key"] = None


def _render_brand_header() -> None:
    st.markdown(
        f"""
        <div class="ss-brand-header">
            <div class="ss-brand">{PRODUCT_NAME}</div>
            <div class="ss-brand-tagline">{html.escape(PRODUCT_TAGLINE)}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _render_scope_stats(*, remaining: int, saved_count: int, show_remaining: bool) -> None:
    if show_remaining:
        line = f"{remaining} left · {saved_count} saved"
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
    tabs_col, menu_col = st.columns([6, 1], vertical_alignment="center", gap="small")
    with tabs_col:
        page = st.segmented_control(
            "Navigation",
            options=list(NAV_PAGES),
            default=prior_active,
            label_visibility="collapsed",
            key="bottom_nav",
        )
    with menu_col:
        with st.popover("⋯"):
            cards = _ensure_all_cards(client)
            render_overflow_menu(
                active_tab=normalize_nav_page(st.session_state.get("active_page")),
                saved_count=saved_count,
                cards=cards,
                eligible_counts=st.session_state.get("eligible_counts") or {},
                on_start_over=_start_over,
                on_clear_saved=_clear_saved_session,
            )
    selected = normalize_nav_page(
        page or st.session_state.get("bottom_nav"),
        fallback=prior_active,
    )
    st.session_state["active_page"] = selected
    return selected


def _queue_index_for_card(card: dict) -> int:
    queue = st.session_state["queue"]
    key = _card_key(card)
    for idx, row in enumerate(queue):
        if _card_key(row) == key:
            return idx
    return st.session_state["queue_index"]


def _render_sticky_actions(client, card: dict) -> None:
    idx = _queue_index_for_card(card)
    st.markdown('<div class="ss-action-shell"></div>', unsafe_allow_html=True)
    col_save, col_skip = st.columns(2)
    if col_save.button("Save", type="primary", use_container_width=True, key="discover_save"):
        append_interaction(card, "save")
        st.session_state["queue_index"] = idx + 1
        _refresh_queue(client, interactions=get_interactions())
        st.rerun()

    if col_skip.button("Not now", use_container_width=True, key="discover_skip"):
        append_interaction(card, "skip")
        st.session_state["queue_index"] = idx + 1
        st.session_state["market_index"] = st.session_state["market_index"] + 1
        sector = card.get("sector") or "Unknown"
        key = (card["market_code"], sector)
        st.session_state["sector_shown"][key] = (
            st.session_state["sector_shown"].get(key, 0) + 1
        )
        _refresh_queue(client, interactions=get_interactions())
        st.rerun()


def _on_filter_change() -> None:
    st.session_state["queue_index"] = 0
    st.session_state["market_index"] = 0
    st.session_state["sector_shown"] = {}


def _render_explore_filters(client) -> None:
    cards = _ensure_all_cards(client)
    market, sector = _explore_filters()
    summary = filter_scope_summary(market_code=market, sector=sector)

    filter_btn, summary_col = st.columns([2, 5], vertical_alignment="center")
    with filter_btn:
        with st.popover("Filters"):
            market_labels = {code: label for code, label in market_filter_options()}
            market_codes = [code for code, _ in market_filter_options()]
            st.selectbox(
                "Market",
                options=market_codes,
                format_func=lambda code: market_labels[code],
                key="explore_market",
                on_change=_on_filter_change,
            )
            current_market = st.session_state.get("explore_market", default_market_filter())
            sector_options = [ALL_SECTORS] + sectors_for_market(
                cards,
                market_code=current_market,
            )
            if st.session_state.get("explore_sector") not in sector_options:
                st.session_state["explore_sector"] = ALL_SECTORS
            st.selectbox(
                "Sector",
                options=sector_options,
                format_func=lambda value: "All sectors" if value == ALL_SECTORS else value,
                key="explore_sector",
                on_change=_on_filter_change,
            )
    with summary_col:
        st.markdown(
            f'<p class="ss-filter-summary">{html.escape(summary)}</p>',
            unsafe_allow_html=True,
        )


def _render_discover_tab(client) -> bool:
    """Render discover walk card. Filters and queue sync run in _discovery_page."""
    queue = st.session_state["queue"]

    if not queue:
        st.info("No companies left in this scope — try another market, sector, or clear filters.")
        return False

    idx = st.session_state["queue_index"]

    if idx >= len(queue):
        st.info("Walk complete in this scope.")
        if st.button(
            "Start over in this scope",
            type="primary",
            use_container_width=True,
            key="discover_start_over",
        ):
            _start_over()
            st.rerun()
        return False

    card = queue[idx]
    scope_meta = walk_progress_line(position=idx + 1, total=len(queue))

    render_stock_card(
        card,
        scope_meta=scope_meta,
        widget_key_prefix="discover",
    )

    if st.button("Next company", use_container_width=True, key="discover_next"):
        st.session_state["queue_index"] = min(idx + 1, len(queue) - 1)
        st.rerun()

    return True


def _saved_row_key(card: dict) -> str:
    return f"{card['market_code']}::{card['ticker']}"


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
        for card in saved_cards:
            row_key = _saved_row_key(card)
            company = card.get("company_name") or card.get("ticker") or "Unknown"
            subtitle = saved_row_subtitle(card)
            row_text, row_action = st.columns([5, 1])
            with row_text:
                st.markdown(
                    f'<div class="ss-saved-list-row">'
                    f'<p class="ss-saved-name">{html.escape(company)}</p>'
                    f'<p class="ss-saved-sector">{html.escape(subtitle)}</p>'
                    f"</div>",
                    unsafe_allow_html=True,
                )
            with row_action:
                if st.button("Open", key=f"saved_open_{row_key}", use_container_width=True):
                    st.session_state["saved_focus_key"] = row_key
                    st.rerun()
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


def _render_search_tab(client) -> None:
    query = st.text_input(
        "Search",
        placeholder="Ticker or company name",
        label_visibility="collapsed",
    ).strip()

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

    for card in matches[:20]:
        label = card.get("company_name") or card.get("ticker")
        ticker = card.get("ticker")
        if st.button(f"{label} ({ticker})", key=f"search_{card['market_code']}_{ticker}"):
            st.session_state["search_selected"] = _card_key(card)
            st.rerun()

    selected = st.session_state.get("search_selected")
    if selected:
        match = next((c for c in matches if _card_key(c) == selected), None)
        if match:
            render_stock_card(match, widget_key_prefix="search")


def _discovery_page(client) -> None:
    interactions = get_interactions()
    if storage_sync_pending():
        _sync_discover_queue(client, interactions=interactions)

    _ensure_all_cards(client)
    saved_count = _saved_count(interactions)

    _render_brand_header()
    active = _render_bottom_nav(saved_count=saved_count, client=client)

    if active == "Discover":
        _render_explore_filters(client)

    _sync_discover_queue(client, interactions=interactions)
    remaining = _scoped_remaining()
    _render_scope_stats(
        remaining=remaining,
        saved_count=saved_count,
        show_remaining=active == "Discover",
    )

    show_actions = False

    if active == "Discover":
        show_actions = _render_discover_tab(client)
    elif active == "Saved":
        _render_saved_tab(client, interactions)
    else:
        _render_search_tab(client)

    if show_actions and active == "Discover":
        queue = st.session_state["queue"]
        idx = st.session_state["queue_index"]
        if idx < len(queue):
            _render_sticky_actions(client, queue[idx])


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
    if render_landing():
        return

    client = get_anon_client()
    _discovery_page(client)


main()
