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
)

MENU_DATA_SOURCE = "Sourced from Yahoo Finance via our weekly pipeline."
MENU_MARKETS_LINE = "Markets: US, UK, Japan, Australia, Germany"
MENU_METRICS_LINE = "Five metrics per company — no substitutes"

_DISCOVER_TIP = (
    "Save keeps a company on this device. Not now skips for later — "
    "you can still find it in Search."
)
_SAVED_TIP = "Open a company to practice numbers or load recent headlines."
_SEARCH_TIP = "Only companies with all five fundamentals appear here."


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
        return "Find any company with a complete five-metric snapshot"
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
                f"Fundamentals refresh weekly · data as of **{snapshot}**",
            )
        else:
            st.markdown("Fundamentals refresh weekly.")
        st.markdown(MENU_METRICS_LINE)
        st.markdown(MENU_MARKETS_LINE)
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
                "Company descriptions are missing from this export — run the weekly "
                "pipeline after migration 004 and re-export mart_stock_cards."
            )


def render_overflow_menu(
    *,
    active_tab: str,
    saved_count: int,
    cards: list[dict[str, Any]],
    eligible_counts: dict[str, int],
    on_start_over: Callable[[], None],
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
    if st.button("Start over", key="menu_start_over", use_container_width=True):
        on_start_over()
        st.rerun()
    if st.button("Clear saved", key="menu_clear_saved", use_container_width=True):
        clear_interactions()
        on_clear_saved()
        st.rerun()
    _render_about_data(cards=cards, counts=eligible_counts)
