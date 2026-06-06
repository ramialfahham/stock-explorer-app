"""Stock Swipe — card discovery app (Streamlit + Supabase)."""

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
from card_ui import render_stock_card
from discovery_queue import build_queue
from onboarding import render_welcome
from settings import get_supabase_anon_key, get_supabase_url
from styles import inject_global_css
from supabase_client import get_anon_client

load_dotenv()

st.set_page_config(
    page_title="Stock Swipe",
    page_icon="📊",
    layout="wide",
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
        interactions = ensure_interactions_loaded()
    st.session_state["queue"] = build_queue(
        cards,
        interactions,
        market_index=st.session_state["market_index"],
        sector_shown=st.session_state["sector_shown"],
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


def _render_topbar(*, remaining: int, saved_count: int) -> None:
    st.markdown(
        f"""
<div class="ss-topbar">
  <span class="ss-brand">Stock Swipe</span>
  <span class="ss-chips">
    <span class="ss-chip">{remaining} left</span>
    <span class="ss-chip">{saved_count} saved</span>
  </span>
</div>
""",
        unsafe_allow_html=True,
    )


def _render_utility_actions(client) -> None:
    st.markdown('<div class="ss-utility-row-marker"></div>', unsafe_allow_html=True)
    col_start, col_clear, _ = st.columns([1, 1, 2])
    with col_start:
        if st.button("Start over", key="utility_start_over"):
            _start_over(client)
            st.rerun()
    with col_clear:
        if st.button("Clear saved", key="utility_clear_saved"):
            clear_interactions()
            st.session_state["saved_selected_key"] = None
            st.rerun()


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


def _render_discover_tab(client) -> None:
    queue = st.session_state["queue"]
    if not queue:
        _refresh_queue(client, interactions=get_interactions())
        queue = st.session_state["queue"]

    if not queue:
        st.info("No card-eligible stocks yet. Run the data pipeline first.")
        return

    if render_welcome():
        return

    idx = st.session_state["queue_index"]
    if idx >= len(queue):
        st.info("You have seen every card in this queue.")
        if st.button("Start over", type="primary", use_container_width=True, key="discover_start_over"):
            _start_over(client)
            st.rerun()
        return

    card = queue[idx]
    render_stock_card(card, card_index=idx + 1, queue_total=len(queue))
    _render_sticky_actions(client, card, idx)


def _render_saved_tab(client, interactions: list[dict]) -> None:
    saved_cards = _saved_cards(client, interactions)

    if not saved_cards:
        st.info("Nothing saved yet — tap Save on a company in Discover.")
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
            render_stock_card(selected)


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
            render_stock_card(match)


def _discovery_page(client) -> None:
    interactions = ensure_interactions_loaded()
    if storage_sync_pending():
        _refresh_queue(client, interactions=interactions)

    queue = st.session_state["queue"]
    if not queue:
        _refresh_queue(client, interactions=get_interactions())
        queue = st.session_state["queue"]

    saved_count = _saved_count(get_interactions())
    remaining = max(len(queue) - st.session_state["queue_index"], 0)
    _render_topbar(remaining=remaining, saved_count=saved_count)
    _render_utility_actions(client)

    saved_label = f"Saved ({saved_count})" if saved_count else "Saved"
    active = st.session_state.get("active_page", "Discover")
    default_nav = saved_label if active == "Saved" else active
    page = st.segmented_control(
        "Navigation",
        options=["Discover", saved_label, "Search"],
        default=default_nav,
        label_visibility="collapsed",
        key="main_nav",
    )
    if page:
        st.session_state["active_page"] = "Saved" if page.startswith("Saved") else page

    active = st.session_state["active_page"]
    if active == "Discover":
        _render_discover_tab(client)
    elif active == "Saved":
        _render_saved_tab(client, get_interactions())
    else:
        _render_search_tab(client)


def main() -> None:
    _init_state()
    inject_global_css()

    if not get_supabase_url() or not get_supabase_anon_key():
        st.error(
            "Missing SUPABASE_URL or SUPABASE_ANON_KEY. "
            "Add them under Streamlit app Settings → Secrets (see .streamlit/secrets.toml.example)."
        )
        return

    client = get_anon_client()
    _discovery_page(client)


main()
