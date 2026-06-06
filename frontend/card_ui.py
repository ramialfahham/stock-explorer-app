"""Stock card layout for Discover, Saved, and Search."""

from __future__ import annotations

import streamlit as st

from card_copy import (
    BENCHMARK_METRICS,
    DEEP_DIVE_METRICS,
    METRIC_HELP,
    METRIC_LABELS,
    VISIBLE_METRICS,
    benchmark_line,
    format_metric_value,
)


def _benchmark_for_metric(card: dict, metric: str) -> str | None:
    for m_key, median_key, direction in BENCHMARK_METRICS:
        if m_key == metric:
            return benchmark_line(card, metric, median_key, direction)
    return None


def _render_metric_cell(card: dict, metric: str) -> None:
    label = METRIC_LABELS[metric]
    st.metric(label, format_metric_value(metric, card.get(metric)))
    st.caption(METRIC_HELP[metric])
    line = _benchmark_for_metric(card, metric)
    if line:
        st.caption(line)


def _format_market_code(market_code: str | None) -> str:
    if not market_code:
        return "Unknown market"
    return market_code.replace("_", " ").upper()


def _render_identity_row(card: dict) -> None:
    company = card.get("company_name") or card.get("ticker") or "Unknown company"
    ticker = card.get("ticker") or "—"
    market = _format_market_code(card.get("market_code"))
    sector = card.get("sector") or "Unknown sector"
    peers = card.get("sector_peer_count")

    name_col, meta_col = st.columns([3, 1])
    with name_col:
        st.markdown(f'<p class="card-company">{company}</p>', unsafe_allow_html=True)
        if peers and peers >= 8:
            st.markdown(f'<p class="card-sector">{sector} · {peers} peers</p>', unsafe_allow_html=True)
        else:
            st.markdown(f'<p class="card-sector">{sector}</p>', unsafe_allow_html=True)
            if peers is not None and peers < 8:
                st.caption("Sector comparison unavailable (small peer group)")
    with meta_col:
        st.markdown(f'<p class="card-ticker">{ticker}</p>', unsafe_allow_html=True)
        st.markdown(f'<p class="card-market">{market}</p>', unsafe_allow_html=True)


def _render_progress(card_index: int, queue_total: int) -> None:
    st.markdown(
        f'<p class="card-progress-label">Card {card_index} of {queue_total}</p>',
        unsafe_allow_html=True,
    )
    st.progress(min(card_index / queue_total, 1.0))


def render_stock_card(
    card: dict,
    *,
    card_index: int | None = None,
    queue_total: int | None = None,
) -> None:
    """Render a bordered stock card with identity row, metrics grid, and deep dive."""
    with st.container(border=True):
        if card_index is not None and queue_total is not None and queue_total > 0:
            _render_progress(card_index, queue_total)

        _render_identity_row(card)

        metric_cols = st.columns(len(VISIBLE_METRICS))
        for col, metric in zip(metric_cols, VISIBLE_METRICS, strict=True):
            with col:
                _render_metric_cell(card, metric)

        with st.expander("More metrics"):
            deep_cols = st.columns(len(DEEP_DIVE_METRICS))
            for col, metric in zip(deep_cols, DEEP_DIVE_METRICS, strict=True):
                with col:
                    _render_metric_cell(card, metric)

        yahoo_ticker = card.get("ticker", "")
        st.link_button(
            "View on Yahoo Finance",
            f"https://finance.yahoo.com/quote/{yahoo_ticker}",
            use_container_width=True,
        )
