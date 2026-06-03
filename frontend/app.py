"""Stock Swipe — card discovery app (Streamlit + Supabase)."""

from __future__ import annotations

import os
import sys
import uuid
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from frontend.card_copy import (
    BENCHMARK_METRICS,
    METRIC_HELP,
    METRIC_LABELS,
    benchmark_line,
    format_metric_value,
)
from frontend.queue import build_queue
from frontend.supabase_client import client_for_session, get_anon_client

load_dotenv()

st.set_page_config(page_title="Stock Swipe", page_icon="📊", layout="centered")


def _init_state() -> None:
    defaults = {
        "session": None,
        "user": None,
        "queue": [],
        "queue_index": 0,
        "market_index": 0,
        "sector_shown": {},
        "session_id": str(uuid.uuid4()),
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


def _load_interactions(client, user_id: str) -> list[dict]:
    response = (
        client.table("user_interactions")
        .select("market_code, ticker, action, created_at")
        .eq("user_id", user_id)
        .order("created_at", desc=True)
        .execute()
    )
    return response.data or []


def _record_action(client, user_id: str, card: dict, action: str) -> None:
    client.table("user_interactions").insert(
        {
            "user_id": user_id,
            "market_code": card["market_code"],
            "ticker": card["ticker"],
            "action": action,
            "session_id": st.session_state["session_id"],
        }
    ).execute()


def _refresh_queue(client) -> None:
    cards = _load_cards(client)
    interactions = _load_interactions(client, st.session_state["user"].id)
    st.session_state["queue"] = build_queue(
        cards,
        interactions,
        market_index=st.session_state["market_index"],
        sector_shown=st.session_state["sector_shown"],
    )
    st.session_state["queue_index"] = 0


def _login_form() -> None:
    st.subheader("Sign in")
    email = st.text_input("Email")
    password = st.text_input("Password", type="password")
    col1, col2 = st.columns(2)
    client = get_anon_client()

    if col1.button("Sign in", use_container_width=True):
        try:
            auth = client.auth.sign_in_with_password({"email": email, "password": password})
            st.session_state["session"] = auth.session
            st.session_state["user"] = auth.user
            st.rerun()
        except Exception as exc:  # noqa: BLE001
            st.error(f"Sign in failed: {exc}")

    if col2.button("Create account", use_container_width=True):
        try:
            auth = client.auth.sign_up({"email": email, "password": password})
            if auth.session:
                st.session_state["session"] = auth.session
                st.session_state["user"] = auth.user
                st.rerun()
            st.info("Check your email to confirm the account, then sign in.")
        except Exception as exc:  # noqa: BLE001
            st.error(f"Sign up failed: {exc}")


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

    for metric, label in METRIC_LABELS.items():
        st.metric(label, format_metric_value(metric, card.get(metric)))
        st.caption(METRIC_HELP[metric])
        for m_key, median_key, direction in BENCHMARK_METRICS:
            if m_key == metric:
                line = benchmark_line(card, metric, median_key, direction)
                if line:
                    st.caption(line)
                break

    yahoo_ticker = card.get("ticker", "")
    st.link_button(
        "View on Yahoo Finance",
        f"https://finance.yahoo.com/quote/{yahoo_ticker}",
        use_container_width=True,
    )


def _discovery_page(client) -> None:
    user = st.session_state["user"]
    st.sidebar.write(f"Signed in as {user.email}")
    if st.sidebar.button("Sign out"):
        client.auth.sign_out()
        st.session_state.clear()
        st.rerun()

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
        _render_card(card)

        col_save, col_skip = st.columns(2)
        if col_save.button("Save", use_container_width=True):
            _record_action(client, user.id, card, "save")
            st.session_state["queue_index"] = idx + 1
            _refresh_queue(client)
            st.rerun()

        if col_skip.button("Not interested right now", use_container_width=True):
            _record_action(client, user.id, card, "skip")
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
        interactions = _load_interactions(client, user.id)
        saved_keys = {
            (i["market_code"], i["ticker"])
            for i in interactions
            if i["action"] == "save"
        }
        cards = _load_cards(client)
        saved_cards = [c for c in cards if (c["market_code"], c["ticker"]) in saved_keys]
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

    if not os.environ.get("SUPABASE_URL") or not os.environ.get("SUPABASE_ANON_KEY"):
        st.error("Missing SUPABASE_URL or SUPABASE_ANON_KEY. Add them to `.env` or Streamlit secrets.")
        return

    if st.session_state["session"] is None:
        _login_form()
        return

    client = client_for_session(st.session_state["session"])
    _discovery_page(client)


if __name__ == "__main__":
    main()
