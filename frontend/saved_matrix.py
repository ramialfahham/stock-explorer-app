"""Saved tab — compact 5-metric comparison matrix."""

from __future__ import annotations

import html
from typing import Any

import streamlit as st

from card_copy import ALL_METRICS, METRIC_LABELS, format_metric_value
from markets import market_display_name

_NAME_MAX_LEN = 20


def _esc(value: object) -> str:
    return html.escape("" if value is None else str(value))


def _short_name(name: str) -> str:
    if len(name) <= _NAME_MAX_LEN:
        return name
    return name[: _NAME_MAX_LEN - 1].rstrip() + "…"


def _column_header(card: dict[str, Any]) -> str:
    ticker = _esc(card.get("ticker") or "—")
    raw_name = card.get("company_name") or card.get("ticker") or "Unknown"
    name = _esc(_short_name(str(raw_name)))
    market = _esc(market_display_name(card.get("market_code")))
    return (
        f'<th scope="col" class="ss-matrix-col">'
        f'<span class="ss-matrix-ticker">{ticker}</span>'
        f'<span class="ss-matrix-name">{name}</span>'
        f'<span class="ss-matrix-market">{market}</span>'
        f"</th>"
    )


def build_saved_matrix_html(cards: list[dict[str, Any]]) -> str:
    """Build metrics × saved companies comparison table."""
    if not cards:
        return ""

    col_headers = "".join(_column_header(card) for card in cards)
    metric_rows: list[str] = []
    for metric in ALL_METRICS:
        cells = "".join(
            f'<td class="ss-matrix-value">{_esc(format_metric_value(metric, card.get(metric)))}</td>'
            for card in cards
        )
        metric_rows.append(
            "<tr>"
            f'<th scope="row" class="ss-matrix-metric">{_esc(METRIC_LABELS[metric])}</th>'
            f"{cells}"
            "</tr>"
        )

    return (
        '<div class="ss-saved-matrix-wrap">'
        '<table class="ss-saved-matrix">'
        "<thead><tr>"
        '<th scope="col" class="ss-matrix-corner"></th>'
        f"{col_headers}"
        "</tr></thead>"
        f"<tbody>{''.join(metric_rows)}</tbody>"
        "</table>"
        "</div>"
    )


def render_saved_matrix(cards: list[dict[str, Any]]) -> None:
    """Render the comparison grid for saved companies."""
    st.markdown(
        f'<p class="ss-saved-matrix-intro">Compare your saved companies across five fundamentals.</p>'
        f"{build_saved_matrix_html(cards)}",
        unsafe_allow_html=True,
    )


def saved_card_options(cards: list[dict[str, Any]]) -> list[tuple[str, str]]:
    """Return (label, option_key) pairs for full-card picker."""
    options: list[tuple[str, str]] = []
    for card in cards:
        ticker = card.get("ticker") or "—"
        name = card.get("company_name") or ticker
        market = market_display_name(card.get("market_code"))
        key = f"{card['market_code']}::{card['ticker']}"
        options.append((f"{name} ({ticker}) · {market}", key))
    return options
