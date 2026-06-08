"""Interactive metric playgrounds and micro-checks (Kennzahlen-Schule pattern)."""

from __future__ import annotations

from typing import Any

import streamlit as st

from card_copy import METRIC_LABELS, format_metric_value


def _key(prefix: str, card: dict[str, Any], suffix: str) -> str:
    market = card.get("market_code") or "unknown"
    ticker = card.get("ticker") or "unknown"
    return f"{prefix}_{market}_{ticker}_{suffix}"


def _render_forward_pe_playground(card: dict[str, Any], *, prefix: str) -> None:
    st.markdown(f"**{METRIC_LABELS['forward_pe']}**")
    default_pe = card.get("forward_pe")
    default_price = 100.0
    default_eps = default_price / default_pe if default_pe and default_pe > 0 else 5.0

    price = st.number_input(
        "Hypothetical share price ($)",
        min_value=1.0,
        value=float(default_price),
        step=1.0,
        key=_key(prefix, card, "play_pe_price"),
    )
    eps = st.number_input(
        "Expected earnings per share next year ($)",
        min_value=0.1,
        value=float(round(default_eps, 2)),
        step=0.1,
        key=_key(prefix, card, "play_pe_eps"),
    )
    if eps > 0:
        simulated = price / eps
        st.info(f"Simulated forward P/E: **{simulated:.1f}**")


def _render_net_debt_playground(card: dict[str, Any], *, prefix: str) -> None:
    st.markdown(f"**{METRIC_LABELS['net_debt_to_ebitda']}**")
    ratio = card.get("net_debt_to_ebitda")
    default_ebitda = 10.0
    default_debt = float(ratio * default_ebitda) if ratio is not None else 25.0

    net_debt = st.number_input(
        "Hypothetical net debt ($B)",
        min_value=0.0,
        value=float(round(default_debt, 2)),
        step=1.0,
        key=_key(prefix, card, "play_debt"),
    )
    ebitda = st.number_input(
        "Hypothetical EBITDA ($B)",
        min_value=0.1,
        value=float(default_ebitda),
        step=0.5,
        key=_key(prefix, card, "play_ebitda"),
    )
    if ebitda > 0:
        simulated = net_debt / ebitda
        st.info(f"Simulated net debt / EBITDA: **{simulated:.2f}**")


def _render_revenue_growth_playground(card: dict[str, Any], *, prefix: str) -> None:
    st.markdown(f"**{METRIC_LABELS['revenue_growth_yoy_pct']}**")
    growth = card.get("revenue_growth_yoy_pct")
    prior = 100.0
    if growth is not None:
        current = prior * (1 + growth / 100.0)
    else:
        current = 110.0

    revenue_prior = st.number_input(
        "Revenue one year ago ($B)",
        min_value=1.0,
        value=float(prior),
        step=1.0,
        key=_key(prefix, card, "play_rev_prior"),
    )
    revenue_current = st.number_input(
        "Revenue today ($B)",
        min_value=0.0,
        value=float(round(current, 2)),
        step=1.0,
        key=_key(prefix, card, "play_rev_current"),
    )
    if revenue_prior > 0:
        simulated = ((revenue_current - revenue_prior) / revenue_prior) * 100.0
        st.info(f"Simulated YoY growth: **{simulated:.1f}%**")


def _render_ebit_margin_playground(card: dict[str, Any], *, prefix: str) -> None:
    st.markdown(f"**{METRIC_LABELS['ebit_margin_pct']}**")
    margin = card.get("ebit_margin_pct")
    revenue = 100.0
    operating = revenue * margin / 100.0 if margin is not None else 15.0

    rev = st.number_input(
        "Revenue ($B)",
        min_value=1.0,
        value=float(revenue),
        step=1.0,
        key=_key(prefix, card, "play_ebit_rev"),
    )
    op = st.number_input(
        "Operating profit ($B)",
        min_value=0.0,
        value=float(round(operating, 2)),
        step=0.5,
        key=_key(prefix, card, "play_ebit_op"),
    )
    if rev > 0:
        simulated = (op / rev) * 100.0
        st.info(f"Simulated operating margin: **{simulated:.1f}%**")


def _render_fcf_margin_playground(card: dict[str, Any], *, prefix: str) -> None:
    st.markdown(f"**{METRIC_LABELS['fcf_margin_pct']}**")
    margin = card.get("fcf_margin_pct")
    revenue = 100.0
    fcf = revenue * margin / 100.0 if margin is not None else 8.0

    rev = st.number_input(
        "Revenue ($B)",
        min_value=1.0,
        value=float(revenue),
        step=1.0,
        key=_key(prefix, card, "play_fcf_rev"),
    )
    cash = st.number_input(
        "Free cash flow ($B)",
        value=float(round(fcf, 2)),
        step=0.5,
        key=_key(prefix, card, "play_fcf_cash"),
    )
    if rev > 0:
        simulated = (cash / rev) * 100.0
        st.info(f"Simulated FCF margin: **{simulated:.1f}%**")


def render_metric_playgrounds(card: dict[str, Any], *, widget_key_prefix: str = "card") -> None:
    """Hypothetical number playgrounds — safe sandbox, no live API calls."""
    tabs = st.tabs(
        [
            "P/E",
            "Margin",
            "Growth",
            "Debt",
            "FCF",
        ]
    )
    with tabs[0]:
        _render_forward_pe_playground(card, prefix=widget_key_prefix)
    with tabs[1]:
        _render_ebit_margin_playground(card, prefix=widget_key_prefix)
    with tabs[2]:
        _render_revenue_growth_playground(card, prefix=widget_key_prefix)
    with tabs[3]:
        _render_net_debt_playground(card, prefix=widget_key_prefix)
    with tabs[4]:
        _render_fcf_margin_playground(card, prefix=widget_key_prefix)


def render_metric_micro_checks(card: dict[str, Any], *, widget_key_prefix: str = "card") -> None:
    """Reflective micro-checks tied to this company's exported values."""
    st.markdown("**Quick check** — interpret the numbers on this card (not investment advice).")

    pe_value = card.get("forward_pe")
    if pe_value is not None:
        st.markdown(
            f"**{METRIC_LABELS['forward_pe']}** on this card is "
            f"**{format_metric_value('forward_pe', pe_value)}**. What does that mainly describe?"
        )
        pe_choice = st.radio(
            "Forward P/E question",
            options=[
                "How many years of expected earnings are priced into one share",
                "How much debt the company owes",
                "How fast revenue grew vs last year",
            ],
            index=None,
            key=_key(widget_key_prefix, card, "check_pe"),
            label_visibility="collapsed",
        )
        if pe_choice:
            if pe_choice.startswith("How many years"):
                st.success("Right — forward P/E is a valuation lens, not debt or growth.")
            else:
                st.info(
                    "Forward P/E compares price to expected next-year earnings per share. "
                    "Debt and growth use different metrics on this card."
                )

    debt_value = card.get("net_debt_to_ebitda")
    if debt_value is not None:
        st.markdown(
            f"**{METRIC_LABELS['net_debt_to_ebitda']}** here is "
            f"**{format_metric_value('net_debt_to_ebitda', debt_value)}**. "
            "What is this ratio mainly about?"
        )
        debt_choice = st.radio(
            "Net debt / EBITDA question",
            options=[
                "Roughly how many years of operating profit to repay net debt",
                "Operating profit as a share of sales",
                "Free cash left from each sales dollar",
            ],
            index=None,
            key=_key(widget_key_prefix, card, "check_debt"),
            label_visibility="collapsed",
        )
        if debt_choice:
            if debt_choice.startswith("Roughly"):
                st.success("Right — it is a solvency / leverage lens, not margin or FCF.")
            else:
                st.info(
                    "Net debt / EBITDA divides net debt by operating cash generation (EBITDA). "
                    "Margins and FCF use different lines on the income and cash flow statements."
                )
