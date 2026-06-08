"""Vertical compare-two table for Saved tab (mobile-friendly)."""

from __future__ import annotations

import html
from typing import Any

import streamlit as st

from card_copy import ALL_METRICS, METRIC_LABELS, format_metric_value


def _esc(value: object) -> str:
    return html.escape("" if value is None else str(value))


def _column_header(card: dict[str, Any]) -> str:
    ticker = _esc(card.get("ticker") or "—")
    name = _esc(card.get("company_name") or card.get("ticker") or "Unknown")
    return (
        f'<th scope="col" class="ss-compare-col">'
        f'<span class="ss-compare-ticker">{ticker}</span>'
        f'<span class="ss-compare-name">{name}</span>'
        f"</th>"
    )


def build_compare_two_html(left: dict[str, Any], right: dict[str, Any]) -> str:
    """Build 5 metric rows × 2 company columns — no horizontal N-scroll."""
    rows: list[str] = []
    for metric in ALL_METRICS:
        rows.append(
            "<tr>"
            f'<th scope="row" class="ss-compare-metric">{_esc(METRIC_LABELS[metric])}</th>'
            f'<td class="ss-compare-value">{_esc(format_metric_value(metric, left.get(metric)))}</td>'
            f'<td class="ss-compare-value">{_esc(format_metric_value(metric, right.get(metric)))}</td>'
            "</tr>"
        )
    return (
        '<div class="ss-compare-two-wrap">'
        '<table class="ss-compare-two">'
        "<thead><tr>"
        '<th scope="col" class="ss-compare-corner">Metric</th>'
        f"{_column_header(left)}{_column_header(right)}"
        "</tr></thead>"
        f"<tbody>{''.join(rows)}</tbody>"
        "</table>"
        "</div>"
    )


def render_compare_two(left: dict[str, Any], right: dict[str, Any]) -> None:
    st.markdown(
        '<p class="ss-compare-two-heading">Compare two saved companies</p>'
        f"{build_compare_two_html(left, right)}",
        unsafe_allow_html=True,
    )


def compare_partner_options(
    saved_cards: list[dict[str, Any]],
    focus_card: dict[str, Any],
) -> list[tuple[str, str]]:
    focus_key = f"{focus_card['market_code']}::{focus_card['ticker']}"
    options: list[tuple[str, str]] = []
    for card in saved_cards:
        key = f"{card['market_code']}::{card['ticker']}"
        if key == focus_key:
            continue
        label = card.get("company_name") or card.get("ticker") or key
        ticker = card.get("ticker") or "—"
        options.append((f"{label} ({ticker})", key))
    return options
