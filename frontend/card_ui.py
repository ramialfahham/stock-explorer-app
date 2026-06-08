"""Stock card layout — scannable HTML, numbers-first."""

from __future__ import annotations

import html

import streamlit as st

from card_copy import (
    BENCHMARK_METRICS,
    BUSINESS_SUMMARY_PREVIEW_CHARS,
    DEEP_DIVE_METRICS,
    METRIC_GLOSS,
    METRIC_LABELS,
    METRIC_LEARN,
    VISIBLE_METRICS,
    benchmark_line,
    benchmark_unavailable_line,
    business_summary_full,
    business_summary_preview,
    format_metric_value,
    freshness_line,
    median_primer_line,
    sector_gloss_line,
    sector_headline,
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
        return "—"
    return market_code.replace("_", " ").upper()


def _benchmark_context_html(card: dict) -> str:
    unavailable = benchmark_unavailable_line(card)
    if unavailable:
        return f'<p class="ss-benchmark-note">{_esc(unavailable)}</p>'
    primer = median_primer_line(card)
    if primer:
        return f'<p class="ss-median-primer">{_esc(primer)}</p>'
    return ""


def _company_summary_html(card: dict) -> str:
    preview = business_summary_preview(card)
    if not preview:
        return ""
    full = business_summary_full(card)
    if not full:
        return ""
    if len(full) <= BUSINESS_SUMMARY_PREVIEW_CHARS:
        return f'<p class="ss-company-summary">{_esc(preview)}</p>'
    return (
        f'<p class="ss-company-summary">{_esc(preview)}</p>'
        f'<details class="ss-company-about">'
        f"<summary>About this company</summary>"
        f'<p class="ss-company-summary-full">{_esc(full)}</p>'
        f"</details>"
    )


def _metric_cell_html(card: dict, metric: str) -> str:
    label = METRIC_LABELS[metric]
    value = format_metric_value(metric, card.get(metric))
    gloss = METRIC_GLOSS[metric]
    bench = _benchmark_for_metric(card, metric)
    gloss_html = f'<p class="ss-metric-gloss">{_esc(gloss)}</p>'
    bench_html = f'<p class="ss-metric-bench">{_esc(bench)}</p>' if bench else ""
    return (
        f'<div class="ss-metric">'
        f'<p class="ss-metric-label">{_esc(label)}</p>'
        f'<p class="ss-metric-value">{_esc(value)}</p>'
        f"{gloss_html}"
        f"{bench_html}"
        f"</div>"
    )


def _explain_all_html() -> str:
    blocks = []
    for metric in VISIBLE_METRICS + DEEP_DIVE_METRICS:
        blocks.append(
            f"<dt>{_esc(METRIC_LABELS[metric])}</dt>"
            f"<dd>{_esc(METRIC_LEARN[metric])}</dd>"
        )
    return (
        f'<details class="ss-explain-all">'
        f"<summary>What do these metrics mean?</summary>"
        f'<dl class="ss-explain-list">{"".join(blocks)}</dl>'
        f"</details>"
    )


def build_card_html(
    card: dict,
    *,
    card_index: int | None = None,
    queue_total: int | None = None,
) -> str:
    company = card.get("company_name") or card.get("ticker") or "Unknown"
    ticker = card.get("ticker") or "—"
    market = _format_market_code(card.get("market_code"))

    progress = ""
    if card_index is not None and queue_total is not None and queue_total > 0:
        progress = f"{card_index}/{queue_total}"

    meta_parts = [p for p in (progress, market) if p]
    meta_line = " · ".join(meta_parts)

    sector_head = sector_headline(card)
    sector_gloss = sector_gloss_line(card.get("sector"))

    hero = "".join(_metric_cell_html(card, m) for m in VISIBLE_METRICS)
    balance = "".join(_metric_cell_html(card, m) for m in DEEP_DIVE_METRICS)

    fresh = freshness_line(card)
    fresh_html = f'<span class="ss-freshness">{_esc(fresh)}</span>' if fresh else ""

    yahoo_ticker = _esc(card.get("ticker", ""))
    yahoo_url = f"https://finance.yahoo.com/quote/{yahoo_ticker}"

    return (
        f'<section class="ss-card">'
        f'<p class="ss-meta-line">{_esc(meta_line)}</p>'
        f'<p class="ss-identity">'
        f'<span class="ss-company">{_esc(company)}</span> '
        f'<span class="ss-ticker">{_esc(ticker)}</span></p>'
        f'<div class="ss-sector-context">'
        f'<p class="ss-sector-headline">{_esc(sector_head)}</p>'
        f'<p class="ss-sector-gloss">{_esc(sector_gloss)}</p>'
        f"</div>"
        f"{_company_summary_html(card)}"
        f"{_benchmark_context_html(card)}"
        f'<div class="ss-metrics-grid ss-metrics-hero">{hero}</div>'
        f'<div class="ss-metrics-grid ss-metrics-balance">{balance}</div>'
        f"{_explain_all_html()}"
        f'<footer class="ss-card-footer">{fresh_html}'
        f'<a class="ss-yahoo-link" href="{yahoo_url}" target="_blank" '
        f'rel="noopener noreferrer">Yahoo ↗</a></footer>'
        f"</section>"
    )


def render_stock_card(
    card: dict,
    *,
    card_index: int | None = None,
    queue_total: int | None = None,
) -> None:
    st.markdown(
        build_card_html(card, card_index=card_index, queue_total=queue_total),
        unsafe_allow_html=True,
    )
