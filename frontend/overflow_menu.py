"""About popover -- app info, one click, no nested disclosure."""

from __future__ import annotations

from typing import Any

import streamlit as st

from markets import latest_snapshot_label, market_display_name, markets_in_deck_order

MENU_ABOUT_INTRO = (
    "Stock Explorer shows a company's numbers: margins, debt, growth, cash, returns, "
    "measured against its industry. Each card also carries a short AI-written summary, "
    "generated from those same numbers, so every line in it can be checked against the "
    "figures right above it."
)
MENU_METRICS_LINE = "Fundamentals per company, no substitutes"


def markets_line(counts: dict[str, int]) -> str:
    """Which markets this panel claims to cover, derived from the cards in the deck -- not
    from the registry and not from `MARKET_DISPLAY_NAMES`. A market is onboarded on one
    branch and first exports cards on the next production run, so those two answers can
    disagree while a run is pending, and this is the panel whose whole job is data trust.
    Empty when there are no cards: saying nothing beats claiming coverage that cannot be
    substantiated.
    """
    if not counts:
        return ""
    return "Markets: " + ", ".join(market_display_name(c) for c in markets_in_deck_order(counts))


def render_about_panel(
    *, cards: list[dict[str, Any]], counts: dict[str, int], descriptions_missing: bool
) -> None:
    """The `About` popover's body -- what the app and its AI read do, then where the data
    comes from. Content only, no nested `st.expander`, so opening the popover is the only
    tap this menu needs. `Clear saved` lives on the Saved tab itself
    (`_render_saved_scope_stats` in `app.py`), next to the count it acts on."""
    st.markdown(MENU_ABOUT_INTRO)
    snapshot = latest_snapshot_label(cards)
    if snapshot:
        st.markdown(f"Sourced from Yahoo Finance, refreshed every two weeks. Data as of **{snapshot}**.")
    else:
        st.markdown("Sourced from Yahoo Finance, refreshed every two weeks.")
    st.markdown(MENU_METRICS_LINE)
    markets = markets_line(counts)
    if markets:
        st.markdown(markets)
    if descriptions_missing:
        st.caption(
            "Company descriptions are missing from this export -- run the "
            "pipeline after migration 004 and re-export mart_stock_cards."
        )
