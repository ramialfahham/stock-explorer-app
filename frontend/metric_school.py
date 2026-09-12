"""Interactive metric playgrounds (Kennzahlen-Schule pattern)."""

from __future__ import annotations

from typing import Any

import streamlit as st

from card_copy import currency_symbol, metric_label, metrics_for_card


def _key(prefix: str, card: dict[str, Any], suffix: str) -> str:
    market = card.get("market_code") or "unknown"
    ticker = card.get("ticker") or "unknown"
    return f"{prefix}_{market}_{ticker}_{suffix}"


def _money(name: str, card: dict[str, Any]) -> str:
    """An input label in the card's currency: "Revenue (£B)"; "(CHF B)" for a code with
    no symbol; "(B)" when the card has no currency."""
    symbol = currency_symbol(card.get("currency"))
    gap = " " if symbol[-1:].isalpha() else ""
    return f"{name} ({symbol}{gap}B)"


def _clamp(value: float, *, min_value: float, max_value: float | None = None) -> float:
    """Keep playground seeds inside st.number_input bounds."""
    if max_value is not None:
        value = min(max_value, value)
    return max(min_value, value)


def seed_net_debt_playground(card: dict[str, Any]) -> tuple[float, float]:
    ratio = card.get("net_debt_to_ebitda")
    default_ebitda = 10.0
    default_debt = float(ratio * default_ebitda) if ratio is not None else 25.0
    return (
        _clamp(round(default_debt, 2), min_value=-500.0, max_value=500.0),
        _clamp(default_ebitda, min_value=0.1),
    )


def seed_revenue_growth_playground(card: dict[str, Any]) -> tuple[float, float]:
    growth = card.get("revenue_growth_yoy_pct")
    prior = 100.0
    if growth is not None:
        current = prior * (1 + growth / 100.0)
    else:
        current = 110.0
    return (
        _clamp(prior, min_value=1.0),
        _clamp(round(current, 2), min_value=0.0),
    )


def seed_ebit_margin_playground(card: dict[str, Any]) -> tuple[float, float]:
    margin = card.get("ebit_margin_pct")
    revenue = 100.0
    operating = revenue * margin / 100.0 if margin is not None else 15.0
    return (
        _clamp(revenue, min_value=1.0),
        _clamp(round(operating, 2), min_value=-500.0, max_value=500.0),
    )


def seed_fcf_margin_playground(card: dict[str, Any]) -> tuple[float, float]:
    margin = card.get("fcf_margin_pct")
    revenue = 100.0
    fcf = revenue * margin / 100.0 if margin is not None else 8.0
    return (
        _clamp(revenue, min_value=1.0),
        _clamp(round(fcf, 2), min_value=-500.0, max_value=500.0),
    )


def _render_net_debt_playground(card: dict[str, Any], *, prefix: str) -> None:
    st.markdown(f"**{metric_label('net_debt_to_ebitda', card)}**")
    ratio = card.get("net_debt_to_ebitda")
    default_debt, default_ebitda = seed_net_debt_playground(card)
    if ratio is not None and ratio < 0:
        st.caption("Negative net debt means cash on hand exceeds debt (net cash position).")

    net_debt = st.number_input(
        _money("Hypothetical net debt", card),
        min_value=-500.0,
        max_value=500.0,
        value=float(default_debt),
        step=1.0,
        key=_key(prefix, card, "play_debt"),
    )
    ebitda = st.number_input(
        _money("Hypothetical EBITDA", card),
        min_value=0.1,
        value=float(default_ebitda),
        step=0.5,
        key=_key(prefix, card, "play_ebitda"),
    )
    if ebitda > 0:
        simulated = net_debt / ebitda
        st.info(f"Simulated net debt / EBITDA: **{simulated:.2f}**")


def _render_revenue_growth_playground(card: dict[str, Any], *, prefix: str) -> None:
    st.markdown(f"**{metric_label('revenue_growth_yoy_pct', card)}**")
    revenue_prior, revenue_current = seed_revenue_growth_playground(card)

    revenue_prior = st.number_input(
        _money("Revenue one year ago", card),
        min_value=1.0,
        value=float(revenue_prior),
        step=1.0,
        key=_key(prefix, card, "play_rev_prior"),
    )
    revenue_current = st.number_input(
        _money("Revenue today", card),
        min_value=0.0,
        value=float(revenue_current),
        step=1.0,
        key=_key(prefix, card, "play_rev_current"),
    )
    if revenue_prior > 0:
        simulated = ((revenue_current - revenue_prior) / revenue_prior) * 100.0
        st.info(f"Simulated YoY growth: **{simulated:.1f}%**")


def _render_ebit_margin_playground(card: dict[str, Any], *, prefix: str) -> None:
    st.markdown(f"**{metric_label('ebit_margin_pct', card)}**")
    revenue, operating = seed_ebit_margin_playground(card)

    rev = st.number_input(
        _money("Revenue", card),
        min_value=1.0,
        value=float(revenue),
        step=1.0,
        key=_key(prefix, card, "play_ebit_rev"),
    )
    op = st.number_input(
        _money("Operating profit", card),
        min_value=-500.0,
        max_value=500.0,
        value=float(operating),
        step=0.5,
        key=_key(prefix, card, "play_ebit_op"),
    )
    if rev > 0:
        simulated = (op / rev) * 100.0
        st.info(f"Simulated operating margin: **{simulated:.1f}%**")


def _render_fcf_margin_playground(card: dict[str, Any], *, prefix: str) -> None:
    st.markdown(f"**{metric_label('fcf_margin_pct', card)}**")
    revenue, fcf = seed_fcf_margin_playground(card)

    rev = st.number_input(
        _money("Revenue", card),
        min_value=1.0,
        value=float(revenue),
        step=1.0,
        key=_key(prefix, card, "play_fcf_rev"),
    )
    cash = st.number_input(
        _money("Free cash flow", card),
        min_value=-500.0,
        max_value=500.0,
        value=float(fcf),
        step=0.5,
        key=_key(prefix, card, "play_fcf_cash"),
    )
    if rev > 0:
        simulated = (cash / rev) * 100.0
        st.info(f"Simulated FCF margin: **{simulated:.1f}%**")


# Which metrics have a playground. Order comes from metrics_for_card(), not this dict, so
# the tabs follow the face and a metric never appears below a card that omits it.
_PLAYGROUNDS = {
    "ebit_margin_pct": _render_ebit_margin_playground,
    "revenue_growth_yoy_pct": _render_revenue_growth_playground,
    "net_debt_to_ebitda": _render_net_debt_playground,
    "fcf_margin_pct": _render_fcf_margin_playground,
}


def playgrounds_for_card(card: dict[str, Any]) -> tuple[str, ...]:
    """The metrics that get a playground on this card: those with one, in face order, and
    only when the face shows them (applies to the company type and has a value)."""
    return tuple(m for m in metrics_for_card(card) if m in _PLAYGROUNDS)


def render_metric_playgrounds(card: dict[str, Any], *, widget_key_prefix: str = "card") -> None:
    """Hypothetical number playgrounds -- safe sandbox, no live API calls. The arithmetic
    here teaches the catalogue's `calculation` sentence on numbers the user types; no card
    value comes from it."""
    metrics = playgrounds_for_card(card)
    if not metrics:
        return
    tabs = st.tabs([metric_label(m, card) for m in metrics])
    for tab, metric in zip(tabs, metrics):
        with tab:
            _PLAYGROUNDS[metric](card, prefix=widget_key_prefix)
