"""Stock Swipe — card discovery app (Streamlit + Supabase)."""

from __future__ import annotations

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

st.set_page_config(page_title="Stock Swipe", page_icon="📊", layout="wide")


def _init_state() -> None:
    defaults = {
        "queue": [],
        "queue_index": 0,
        "market_index": 0,
        "sector_shown": {},
        "saved_selected_key": None,
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


def _render_sidebar(*, queue_len: int, queue_index: int, saved_count: int, client) -> None:
    st.sidebar.markdown("### Stock Swipe")
    st.sidebar.caption("Browse fundamentals. Save what you want to revisit.")
    st.sidebar.markdown(
        "Saves and skips stay on **this device only** — not synced across browsers."
    )
    st.sidebar.caption("Not investment advice. Fundamentals refresh weekly.")

    st.sidebar.divider()
    st.sidebar.markdown("**This session**")
    remaining = max(queue_len - queue_index, 0)
    st.sidebar.markdown(f"- **{remaining}** cards left in queue")
    st.sidebar.markdown(f"- **{saved_count}** saved companies")

    if st.sidebar.button("Start over", use_container_width=True):
        _start_over(client)
        st.rerun()

    st.sidebar.divider()
    if st.sidebar.button("Clear saved on this device", use_container_width=True):
        clear_interactions()
        st.session_state["saved_selected_key"] = None


def _render_discover_tab(client) -> None:
    queue = st.session_state["queue"]
    if not queue:
        _refresh_queue(client, interactions=get_interactions())
        queue = st.session_state["queue"]

    if not queue:
        st.info("No card-eligible stocks in Supabase yet. Run the data pipeline first.")
        return

    if render_welcome():
        return

    idx = st.session_state["queue_index"]
    if idx >= len(queue):
        st.success("You have seen every card in this queue.")
        st.caption("Start over to shuffle through companies again with a fresh order.")
        if st.button("Start over", type="primary", use_container_width=True):
            _start_over(client)
            st.rerun()
        return

    card = queue[idx]
    render_stock_card(card, card_index=idx + 1, queue_total=len(queue))

    col_save, col_skip = st.columns(2)
    if col_save.button("Save", type="primary", use_container_width=True):
        append_interaction(card, "save")
        st.session_state["queue_index"] = idx + 1
        _refresh_queue(client, interactions=get_interactions())
        st.rerun()

    if col_skip.button("Not interested right now", use_container_width=True):
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


def _render_saved_tab(client, interactions: list[dict]) -> None:
    saved_cards = _saved_cards(client, interactions)
    st.caption(f"{len(saved_cards)} saved on this device")

    if not saved_cards:
        st.info(
            "Nothing saved yet. Open **Discover**, read a card, and tap **Save** "
            "to build your watchlist here."
        )
        return

    for card in saved_cards:
        key = _card_key(card)
        label = card.get("company_name") or card.get("ticker")
        ticker = card.get("ticker") or "—"
        sector = card.get("sector") or "Unknown sector"
        row_label, row_action = st.columns([5, 1])
        with row_label:
            st.markdown(f"**{label}** · `{ticker}`")
            st.caption(sector)
        with row_action:
            if st.button("Open", key=f"saved_open_{key[0]}_{key[1]}", use_container_width=True):
                st.session_state["saved_selected_key"] = key
                st.rerun()
        st.divider()

    selected_key = st.session_state.get("saved_selected_key")
    if selected_key:
        selected = next((c for c in saved_cards if _card_key(c) == selected_key), None)
        if selected:
            st.markdown("#### Selected company")
            render_stock_card(selected)


def _render_search_tab(client) -> None:
    st.caption("Find any card-eligible company — including ones you skipped in Discover.")
    query = st.text_input(
        "Search",
        placeholder="Try AAPL, Apple, or Life360",
        label_visibility="collapsed",
    ).strip()
    if not query:
        st.markdown(
            "Type a **ticker** or **company name** to open its card. "
            "Only companies with complete fundamentals appear here."
        )
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
        st.warning(f"No card-eligible matches for “{query}”. Try a shorter name or ticker symbol.")
        return

    st.caption(f"{len(matches)} match{'es' if len(matches) != 1 else ''} — showing up to 20")
    for card in matches[:20]:
        with st.expander(f"{card.get('company_name')} ({card.get('ticker')})"):
            render_stock_card(card)


def _discovery_page(client) -> None:
    interactions = ensure_interactions_loaded()
    if storage_sync_pending():
        _refresh_queue(client, interactions=interactions)

    queue = st.session_state["queue"]
    if not queue:
        _refresh_queue(client, interactions=get_interactions())
        queue = st.session_state["queue"]

    saved_count = _saved_count(get_interactions())
    _render_sidebar(
        queue_len=len(queue),
        queue_index=st.session_state["queue_index"],
        saved_count=saved_count,
        client=client,
    )

    saved_label = f"Saved ({saved_count})" if saved_count else "Saved"
    tab_discover, tab_saved, tab_search = st.tabs(["Discover", saved_label, "Search"])

    with tab_discover:
        _render_discover_tab(client)

    with tab_saved:
        _render_saved_tab(client, get_interactions())

    with tab_search:
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
