"""Stock card layout — HTML-first, dark editorial."""

from __future__ import annotations

import html

import streamlit as st

from card_copy import (
    BENCHMARK_METRICS,
    DEEP_DIVE_METRICS,
    METRIC_HELP,
    METRIC_LABELS,
    METRIC_LEARN,
    VISIBLE_METRICS,
    benchmark_line,
    format_metric_value,
    freshness_line,
)


def _benchmark_for_metric(card: dict, metric: str) -> str | None:
    for m_key, median_key, direction in BENCHMARK_METRICS:
        if m_key == metric:
            return benchmark_line(card, metric, median_key, direction)
    return None


def _esc(value: object) -> str:
    return html.escape("" if value is None else str(value))


def _format_market_code(market_code: str | None) -> str:
    if not market_code:
        return "Unknown market"
    return market_code.replace("_", " ").upper()


def _metric_row_html(card: dict, metric: str, *, show_learn: bool) -> str:
    label = METRIC_LABELS[metric]
    value = format_metric_value(metric, card.get(metric))
    hint = METRIC_HELP[metric]
    bench = _benchmark_for_metric(card, metric)
    bench_html = (
        f'<p class="ss-metric-bench">{_esc(bench)}</p>' if bench else ""
    )
    learn_html = ""
    if show_learn:
        learn_html = (
            f'<details class="ss-metric-learn">'
            f"<summary>?</summary><p>{_esc(METRIC_LEARN[metric])}</p></details>"
        )
    return (
        f'<article class="ss-metric">'
        f'<div class="ss-metric-head">'
        f'<span class="ss-metric-label">{_esc(label)}</span>{learn_html}'
        f"</div>"
        f'<p class="ss-metric-value">{_esc(value)}</p>'
        f'<p class="ss-metric-hint">{_esc(hint)}</p>'
        f"{bench_html}"
        f"</article>"
    )


def build_card_html(
    card: dict,
    *,
    card_index: int | None = None,
    queue_total: int | None = None,
) -> str:
    company = card.get("company_name") or card.get("ticker") or "Unknown company"
    ticker = card.get("ticker") or "—"
    market = _format_market_code(card.get("market_code"))
    sector = card.get("sector") or "Unknown sector"
    peers = card.get("sector_peer_count")

    queue_chip = ""
    if card_index is not None and queue_total is not None and queue_total > 0:
        queue_chip = f'<span class="ss-queue-chip">{card_index} / {queue_total}</span>'

    if peers and peers >= 8:
        sector_line = f"{_esc(sector)} · {peers} peers"
    else:
        sector_line = _esc(sector)
        if peers is not None and peers < 8:
            sector_line += ' · <span class="ss-muted">small peer group</span>'

    hero_rows = "".join(
        _metric_row_html(card, metric, show_learn=True) for metric in VISIBLE_METRICS
    )
    deep_rows = "".join(
        _metric_row_html(card, metric, show_learn=False) for metric in DEEP_DIVE_METRICS
    )

    fresh = freshness_line(card)
    fresh_html = f'<p class="ss-freshness">{_esc(fresh)}</p>' if fresh else ""

    yahoo_ticker = _esc(card.get("ticker", ""))
    yahoo_url = f"https://finance.yahoo.com/quote/{yahoo_ticker}"

    return (
        f'<section class="ss-card">'
        f'<header class="ss-card-header">'
        f'<div class="ss-card-meta-row">{queue_chip}'
        f'<span class="ss-ticker">{_esc(ticker)}</span>'
        f'<span class="ss-market">{_esc(market)}</span></div>'
        f'<h1 class="ss-company">{_esc(company)}</h1>'
        f'<p class="ss-sector">{sector_line}</p>'
        f"</header>"
        f'<div class="ss-metrics-grid">{hero_rows}</div>'
        f'<details class="ss-deep-dive"><summary>Debt &amp; cash flow</summary>'
        f'<div class="ss-metrics-stack">{deep_rows}</div></details>'
        f'<footer class="ss-card-footer">{fresh_html}'
        f'<a class="ss-yahoo-link" href="{yahoo_url}" target="_blank" '
        f'rel="noopener noreferrer">Yahoo Finance ↗</a></footer>'
        f"</section>"
    )


def render_stock_card(
    card: dict,
    *,
    card_index: int | None = None,
    queue_total: int | None = None,
) -> None:
    """Render a compact HTML stock card."""
    st.markdown(
        build_card_html(card, card_index=card_index, queue_total=queue_total),
        unsafe_allow_html=True,
    )
