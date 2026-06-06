"""Stock Swipe — card discovery app (Streamlit + Supabase)."""

from __future__ import annotations

import streamlit as st
from dotenv import load_dotenv

from browser_storage import append_interaction, clear_interactions, ensure_interactions_loaded
from card_copy import (
    BENCHMARK_METRICS,
    DEEP_DIVE_METRICS,
    METRIC_HELP,
    METRIC_LABELS,
    VISIBLE_METRICS,
    benchmark_line,
    format_metric_value,
)
from discovery_queue import build_queue
from settings import get_supabase_anon_key, get_supabase_url
from supabase_client import get_anon_client

load_dotenv()

st.set_page_config(page_title="Stock Swipe", page_icon="📊", layout="centered")


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
    response = (
        client.table("mart_stock_cards")
        .select("*")
        .eq("is_card_eligible", True)
        .execute()
    )
    return response.data or []


def _refresh_queue(client) -> None:
    cards = _load_cards(client)
    interactions = ensure_interactions_loaded()
    st.session_state["queue"] = build_queue(
        cards,
        interactions,
        market_index=st.session_state["market_index"],
        sector_shown=st.session_state["sector_shown"],
    )
    st.session_state["queue_index"] = 0


def _render_metric_block(card: dict, metric: str, label: str) -> None:
    st.metric(label, format_metric_value(metric, card.get(metric)))
    st.caption(METRIC_HELP[metric])
    for m_key, median_key, direction in BENCHMARK_METRICS:
        if m_key == metric:
            line = benchmark_line(card, metric, median_key, direction)
            if line:
                st.caption(line)
            break


def _render_card(card: dict) -> None:
    st.caption(f"Market: {card.get('market_code', '').replace('_', ' ').upper()}")
    st.title(card.get("company_name") or card.get("ticker"))
    sector = card.get("sector") or "Unknown sector"
    peers = card.get("sector_peer_count")
    if peers and peers >= 8:
        st.write(f"{sector} ({peers} companies)")
    else:
        st.write(sector)
        if peers is not None and peers < 8:
            st.caption("Comparison unavailable (small sector)")

    for metric in VISIBLE_METRICS:
        _render_metric_block(card, metric, METRIC_LABELS[metric])

    with st.expander("More metrics (scroll)"):
        for metric in DEEP_DIVE_METRICS:
            _render_metric_block(card, metric, METRIC_LABELS[metric])

    yahoo_ticker = card.get("ticker", "")
    st.link_button(
        "View on Yahoo Finance",
        f"https://finance.yahoo.com/quote/{yahoo_ticker}",
        use_container_width=True,
    )


def _saved_cards(client, interactions: list[dict]) -> list[dict]:
    saved_keys = {
        (i["market_code"], i["ticker"]) for i in interactions if i.get("action") == "save"
    }
    cards = _load_cards(client)
    return [c for c in cards if (c["market_code"], c["ticker"]) in saved_keys]


def _discovery_page(client) -> None:
    st.sidebar.caption("Save and skip are stored on this device only — not synced across browsers.")
    if st.sidebar.button("Clear saved on this device"):
        clear_interactions()

    tab_discover, tab_saved, tab_search = st.tabs(["Discover", "Saved", "Search"])

    with tab_discover:
        if st.button("Refresh queue"):
            _refresh_queue(client)
        queue = st.session_state["queue"]
        if not queue:
            _refresh_queue(client)
            queue = st.session_state["queue"]

        if not queue:
            st.info("No card-eligible stocks in Supabase yet. Run the data pipeline first.")
            return

        idx = st.session_state["queue_index"]
        if idx >= len(queue):
            st.success("You have seen all eligible cards in this queue. Refresh to start again.")
            return

        card = queue[idx]
        st.caption(f"Card {idx + 1} of {len(queue)} in this queue")
        _render_card(card)

        col_save, col_skip = st.columns(2)
        if col_save.button("Save", use_container_width=True):
            append_interaction(card, "save")
            st.session_state["queue_index"] = idx + 1
            _refresh_queue(client)
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
            _refresh_queue(client)
            st.rerun()

    with tab_saved:
        interactions = ensure_interactions_loaded()
        saved_cards = _saved_cards(client, interactions)
        if not saved_cards:
            st.write("No saved companies yet.")
        for card in saved_cards:
            with st.expander(f"{card.get('company_name')} ({card.get('ticker')})"):
                _render_card(card)

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
                    _render_card(card)


def main() -> None:
    _init_state()
    st.title("Stock Swipe")
    st.caption("Learn and discover companies — not investment advice.")
    st.caption(
        "Fundamentals refresh weekly. Prices on cards are not real-time; "
        "use Yahoo Finance for a live quote."
    )

    if not get_supabase_url() or not get_supabase_anon_key():
        st.error(
            "Missing SUPABASE_URL or SUPABASE_ANON_KEY. "
            "Add them under Streamlit app Settings → Secrets (see .streamlit/secrets.toml.example)."
        )
        return

    client = get_anon_client()
    _discovery_page(client)


main()
