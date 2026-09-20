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
    """Which markets this panel claims to cover, derived from the cards in the deck.

    Not from the registry and not from `MARKET_DISPLAY_NAMES`. A market is onboarded on one
    branch and first exports cards on the next production run, so those two answers disagree for
    as long as a run is pending, and this is the panel whose whole job is data trust. Written out
    as a literal it went stale in the other direction: it still said "US, UK, Japan, Australia,
    Germany" while nine markets were registered. Empty when there are no cards: saying nothing
    beats claiming coverage that cannot be substantiated.
    """
    if not counts:
        return ""
    return "Markets: " + ", ".join(market_display_name(c) for c in markets_in_deck_order(counts))


def render_about_panel(
    *, cards: list[dict[str, Any]], counts: dict[str, int], descriptions_missing: bool
) -> None:
    """The `About` popover's body -- what the app and its AI read do, then where the data
    comes from. Content only, no nested `st.expander`: this used to be a second click inside
    the popover (tap `⋯`, then tap to expand "About"), which was one click too many for the
    only thing left in the menu. `Clear saved` lives on the Saved tab itself
    (`_render_saved_scope_stats` in `app.py`), next to the count it acts on. Per-market card
    counts (once shown here as "1050 card-ready · 500 in S&P 500" plus a breakdown line)
    were dropped: internal pipeline detail, not something a reader needs to know, and
    redundant with the plain-language `markets_line` right above it."""
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
