"""Overflow (⋯) menu — session help, trust, and settings."""

from __future__ import annotations

import html
from collections.abc import Callable
from datetime import date
from typing import Any

import streamlit as st

from browser_storage import clear_interactions, request_landing
from card_copy import format_snapshot_date
from explore_filters import ALL_MARKETS, ALL_SECTORS, cards_lack_business_summary
from markets import (
    discover_pool_summary,
    eligible_breakdown_lines,
    latest_snapshot_label,
    market_display_name,
    markets_in_deck_order,
)

MENU_DATA_SOURCE = "Sourced from Yahoo Finance via our pipeline, refreshed every two weeks."
MENU_METRICS_LINE = "Fundamentals per company, no substitutes"

_DISCOVER_TIP = (
    "Save keeps a company on this device to revisit later. Not now just means moving on "
    "for now; the list doesn't change."
)
_SAVED_TIP = "Open a company to practice numbers or load recent headlines."
_SEARCH_TIP = "Only companies with a complete set of fundamentals appear here."


def markets_line(counts: dict[str, int]) -> str:
    """Which markets this panel claims to cover, derived from the cards in the deck.

    Not from the registry and not from `MARKET_DISPLAY_NAMES`. A market is onboarded on one
    branch and first exports cards on the next production run, so those two answers disagree for
    as long as a run is pending, and this is the panel whose whole job is data trust. Written out
    as a literal it went stale in the other direction: it still said "US, UK, Japan, Australia,
    Germany" while nine markets were registered.

    Deriving from `counts` also keeps this line and the per-market breakdown rendered below it
    consistent: same dict, and the same `markets_in_deck_order`, so they cannot disagree on which
    markets or in what order. Empty when there are no cards, which is what the breakdown and the
    pool summary already do in that state: saying nothing beats claiming coverage that cannot be
    substantiated.
    """
    if not counts:
        return ""
    return "Markets: " + ", ".join(market_display_name(c) for c in markets_in_deck_order(counts))


def _esc(value: object) -> str:
    return html.escape("" if value is None else str(value))


def discover_scope_line(
    *,
    market: str,
    sector: str,
) -> str:
    market_label = (
        "All markets" if market == ALL_MARKETS else market_display_name(market)
    )
    sector_label = "All sectors" if sector == ALL_SECTORS else sector
    return f"Exploring: {market_label} · {sector_label}"


def right_now_line(*, active_tab: str, saved_count: int) -> str:
    tab = active_tab.strip()
    if tab == "Saved":
        noun = "company" if saved_count == 1 else "companies"
        return f"{saved_count} saved {noun} on this device"
    if tab == "Search":
        return "Find any company with a complete fundamentals snapshot"
    market = st.session_state.get("explore_market", ALL_MARKETS)
    sector = st.session_state.get("explore_sector", ALL_SECTORS)
    return discover_scope_line(market=market, sector=sector)


def quick_tip_line(*, active_tab: str) -> str:
    tab = active_tab.strip()
    if tab == "Saved":
        return _SAVED_TIP
    if tab == "Search":
        return _SEARCH_TIP
    return _DISCOVER_TIP


def menu_context_html(*, active_tab: str, saved_count: int) -> str:
    right_now = right_now_line(active_tab=active_tab, saved_count=saved_count)
    tip = quick_tip_line(active_tab=active_tab)
    return (
        '<div class="ss-menu-panel">'
        f'<p class="ss-menu-label">Right now</p>'
        f'<p class="ss-menu-body">{_esc(right_now)}</p>'
        f'<p class="ss-menu-label">Tip</p>'
        f'<p class="ss-menu-tip">{_esc(tip)}</p>'
        "</div>"
    )


def _render_about_data(*, cards: list[dict[str, Any]], counts: dict[str, int]) -> None:
    with st.expander("About the data", expanded=False):
        snapshot = latest_snapshot_label(cards)
        if snapshot:
            st.markdown(
                f"Fundamentals refresh every two weeks · data as of **{snapshot}**",
            )
        else:
            st.markdown("Fundamentals refresh every two weeks.")
        st.markdown(MENU_METRICS_LINE)
        markets = markets_line(counts)
        if markets:
            st.markdown(markets)
        st.markdown(MENU_DATA_SOURCE)
        if counts:
            pool_summary = discover_pool_summary(counts)
            if pool_summary:
                st.caption(pool_summary)
            lines = eligible_breakdown_lines(counts)
            if lines:
                breakdown = " · ".join(lines)
                st.caption(breakdown)
        if cards_lack_business_summary(cards):
            st.caption(
                "Company descriptions are missing from this export — run the "
                "pipeline after migration 004 and re-export mart_stock_cards."
            )


def render_overflow_menu(
    *,
    active_tab: str,
    saved_count: int,
    cards: list[dict[str, Any]],
    eligible_counts: dict[str, int],
    on_clear_saved: Callable[[], None],
) -> None:
    """Render popover body: context, actions, and optional data expander."""
    st.markdown(
        menu_context_html(active_tab=active_tab, saved_count=saved_count),
        unsafe_allow_html=True,
    )
    if st.button(
        "How Stock Explorer works",
        key="menu_how_it_works",
        type="primary",
        use_container_width=True,
    ):
        request_landing()
        st.rerun()
    st.markdown('<div class="ss-menu-actions-divider"></div>', unsafe_allow_html=True)
    if st.button("Clear saved", key="menu_clear_saved", use_container_width=True):
        clear_interactions()
        on_clear_saved()
        st.rerun()
    _render_about_data(cards=cards, counts=eligible_counts)
