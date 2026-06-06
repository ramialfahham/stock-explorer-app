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


def _saved_cards(client, interactions: list[dict]) -> list[dict]:
    saved_keys = {
        (i["market_code"], i["ticker"]) for i in interactions if i.get("action") == "save"
    }
    cards = _load_cards(client)
    return [c for c in cards if (c["market_code"], c["ticker"]) in saved_keys]


def _render_sidebar() -> None:
    st.sidebar.markdown("### Stock Swipe")
    st.sidebar.caption("Learn and discover companies — not investment advice.")
    st.sidebar.markdown(
        "Save and skip stay on **this device only**. They are not synced across browsers."
    )
    st.sidebar.caption(
        "Fundamentals refresh weekly. Card prices are not real-time — use Yahoo Finance for a live quote."
    )
    if st.sidebar.button("Clear saved on this device"):
        clear_interactions()


def _discovery_page(client) -> None:
    _render_sidebar()

    interactions = ensure_interactions_loaded()
    if storage_sync_pending():
        _refresh_queue(client, interactions=interactions)

    tab_discover, tab_saved, tab_search = st.tabs(["Discover", "Saved", "Search"])

    with tab_discover:
        if st.button("Refresh queue"):
            _refresh_queue(client, interactions=get_interactions())
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
            st.success("You have seen all eligible cards in this queue. Refresh to start again.")
            return

        card = queue[idx]
        render_stock_card(card, card_index=idx + 1, queue_total=len(queue))

        col_save, col_skip = st.columns(2)
        if col_save.button("Save", use_container_width=True):
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

    with tab_saved:
        saved_cards = _saved_cards(client, get_interactions())
        if not saved_cards:
            st.write("No saved companies yet.")
        for card in saved_cards:
            with st.expander(f"{card.get('company_name')} ({card.get('ticker')})"):
                render_stock_card(card)

    with tab_search:
        query = st.text_input("Search by ticker or company name").strip().lower()
        if query:
            cards = _load_cards(client)
            matches = [
                c
                for c in cards
                if query in (c.get("ticker") or "").lower()
                or query in (c.get("company_name") or "").lower()
            ]
            if not matches:
                st.write("No eligible matches.")
            for card in matches[:20]:
                with st.expander(f"{card.get('company_name')} ({card.get('ticker')})"):
                    render_stock_card(card)


def main() -> None:
    _init_state()
    inject_global_css()
    st.title("Discover")

    if not get_supabase_url() or not get_supabase_anon_key():
        st.error(
            "Missing SUPABASE_URL or SUPABASE_ANON_KEY. "
            "Add them under Streamlit app Settings → Secrets (see .streamlit/secrets.toml.example)."
        )
        return

    client = get_anon_client()
    _discovery_page(client)


main()
