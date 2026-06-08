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
from brand import PRODUCT_NAME
from card_ui import render_stock_card
from discovery_queue import build_queue
from landing import render_landing
from markets import (
    HERO_MARKET_CODE,
    discover_pool_summary,
    eligible_breakdown_lines,
    eligible_counts_by_market,
)
from settings import get_supabase_anon_key, get_supabase_url
from styles import inject_global_css
from supabase_client import get_anon_client

load_dotenv()

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
        "saved_selected_key": None,
        "search_selected": None,
        "active_page": "Discover",
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def _load_cards(client) -> list[dict]:
    try:
        response = (
            client.table("mart_stock_cards")
            .select("*")
            .eq("is_card_eligible", True)
            .execute()
        )
    except Exception as exc:  # noqa: BLE001
        st.error(f"Could not load cards from Supabase: {exc}")
        return []
    return response.data or []


def _refresh_queue(client, *, interactions: list[dict] | None = None) -> None:
    cards = _load_cards(client)
    if interactions is None:
        interactions = get_interactions()
    counts = eligible_counts_by_market(cards)
    st.session_state["eligible_counts"] = counts
    st.session_state["queue"] = build_queue(
        cards,
        interactions,
        market_index=st.session_state["market_index"],
        sector_shown=st.session_state["sector_shown"],
        start_market=HERO_MARKET_CODE,
    )
    st.session_state["queue_index"] = 0


def _start_over(client) -> None:
    st.session_state["queue_index"] = 0
    st.session_state["market_index"] = 0
    st.session_state["sector_shown"] = {}
    _refresh_queue(client, interactions=get_interactions())


def _saved_count(interactions: list[dict]) -> int:
    return sum(1 for row in interactions if row.get("action") == "save")


def _saved_cards(client, interactions: list[dict]) -> list[dict]:
    saved_keys = {
        (i["market_code"], i["ticker"]) for i in interactions if i.get("action") == "save"
    }
    cards = _load_cards(client)
    saved = [c for c in cards if (c["market_code"], c["ticker"]) in saved_keys]
    saved.sort(key=lambda c: (c.get("company_name") or c.get("ticker") or "").lower())
    return saved


def _card_key(card: dict) -> tuple[str, str]:
    return (card["market_code"], card["ticker"])


def _render_header(
    *,
    remaining: int,
    saved_count: int,
    client,
    pool_summary: str | None = None,
) -> None:
    bar_col, menu_col = st.columns([6, 1])
    with bar_col:
        stats_class = "ss-header-stats"
        if not pool_summary:
            stats_class += " ss-header-stats--solo"
        pool_line = ""
        if pool_summary:
            pool_line = f'<div class="ss-header-pool">{html.escape(pool_summary)}</div>'
        st.markdown(
            f"""
<div class="ss-brand">{PRODUCT_NAME}</div>
<div class="{stats_class}">{remaining} left · {saved_count} saved</div>
{pool_line}
""",
            unsafe_allow_html=True,
        )
    with menu_col:
        with st.popover("⋯"):
            if st.button("Start over", key="menu_start_over", use_container_width=True):
                _start_over(client)
                st.rerun()
            if st.button("Clear saved", key="menu_clear_saved", use_container_width=True):
                clear_interactions()
                st.session_state["saved_selected_key"] = None
                st.rerun()


def _render_bottom_nav(saved_count: int) -> None:
    saved_label = f"Saved ({saved_count})" if saved_count else "Saved"
    active = st.session_state.get("active_page", "Discover")
    default_nav = saved_label if active == "Saved" else active

    st.markdown('<div class="ss-bottom-nav-marker"></div>', unsafe_allow_html=True)
    page = st.segmented_control(
        "Navigation",
        options=["Discover", saved_label, "Search"],
        default=default_nav,
        label_visibility="collapsed",
        key="bottom_nav",
    )
    if page:
        st.session_state["active_page"] = "Saved" if page.startswith("Saved") else page


def _render_sticky_actions(client, card: dict, idx: int) -> None:
    st.markdown('<div class="ss-action-shell"></div>', unsafe_allow_html=True)
    col_save, col_skip = st.columns(2)
    if col_save.button("Save", type="primary", use_container_width=True, key="discover_save"):
        append_interaction(card, "save")
        st.session_state["queue_index"] = idx + 1
        _refresh_queue(client, interactions=get_interactions())
        st.rerun()

    if col_skip.button("Skip", use_container_width=True, key="discover_skip"):
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


def _render_discover_context() -> None:
    counts = st.session_state.get("eligible_counts") or {}
    if not counts:
        return
    lines = eligible_breakdown_lines(counts)
    breakdown = "<br>".join(html.escape(line) for line in lines)
    st.markdown(
        f'<details class="ss-market-breakdown">'
        f"<summary>Companies by market</summary>"
        f'<p class="ss-market-breakdown-body">{breakdown}</p>'
        f"</details>",
        unsafe_allow_html=True,
    )


def _render_discover_tab(client) -> bool:
    """Render discover content. Returns True if Save/Skip should show."""
    queue = st.session_state["queue"]
    if not queue:
        _refresh_queue(client, interactions=get_interactions())
        queue = st.session_state["queue"]

    if not queue:
        st.info("No card-eligible stocks yet.")
        return False

    _render_discover_context()

    idx = st.session_state["queue_index"]
    if idx >= len(queue):
        st.info("Queue complete.")
        if st.button("Start over", type="primary", use_container_width=True, key="discover_start_over"):
            _start_over(client)
            st.rerun()
        return False

    card = queue[idx]
    render_stock_card(
        card,
        card_index=idx + 1,
        queue_total=len(queue),
        widget_key_prefix="discover",
    )
    return True


def _render_saved_tab(client, interactions: list[dict]) -> None:
    saved_cards = _saved_cards(client, interactions)

    if not saved_cards:
        st.info("Nothing saved yet — tap Save in Discover.")
        return

    for card in saved_cards:
        key = _card_key(card)
        label = html.escape(card.get("company_name") or card.get("ticker") or "Unknown")
        ticker = html.escape(card.get("ticker") or "—")
        sector = html.escape(card.get("sector") or "Unknown sector")
        row_text, row_action = st.columns([4, 1])
        with row_text:
            st.markdown(
                f'<p class="ss-saved-name">{label} · '
                f'<span class="ss-saved-ticker">{ticker}</span></p>'
                f'<p class="ss-saved-sector">{sector}</p>',
                unsafe_allow_html=True,
            )
        with row_action:
            if st.button("Open", key=f"saved_open_{key[0]}_{key[1]}", use_container_width=True):
                st.session_state["saved_selected_key"] = key
                st.rerun()

    selected_key = st.session_state.get("saved_selected_key")
    if selected_key:
        selected = next((c for c in saved_cards if _card_key(c) == selected_key), None)
        if selected:
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
    cards = _load_cards(client)
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
        _refresh_queue(client, interactions=interactions)

    queue = st.session_state["queue"]
    if not queue:
        _refresh_queue(client, interactions=get_interactions())
        queue = st.session_state["queue"]

    saved_count = _saved_count(get_interactions())
    remaining = max(len(queue) - st.session_state["queue_index"], 0)

    _render_bottom_nav(saved_count)
    active = st.session_state.get("active_page", "Discover")
    counts = st.session_state.get("eligible_counts") or {}
    pool_summary = discover_pool_summary(counts) if active == "Discover" else None

    _render_header(
        remaining=remaining,
        saved_count=saved_count,
        client=client,
        pool_summary=pool_summary,
    )

    show_actions = False

    if active == "Discover":
        show_actions = _render_discover_tab(client)
    elif active == "Saved":
        _render_saved_tab(client, get_interactions())
    else:
        _render_search_tab(client)

    if show_actions and active == "Discover":
        idx = st.session_state["queue_index"]
        queue = st.session_state["queue"]
        if idx < len(queue):
            _render_sticky_actions(client, queue[idx], idx)


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
