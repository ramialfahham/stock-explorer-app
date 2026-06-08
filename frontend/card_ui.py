"""Stock card layout — scannable HTML, numbers-first."""

from __future__ import annotations

import html

import streamlit as st

from card_copy import (
    BENCHMARK_METRICS,
    BUSINESS_SUMMARY_PREVIEW_CHARS,
    DEEP_DIVE_METRICS,
    MEDIAN_PRIMER,
    METRIC_GLOSS,
    METRIC_LABELS,
    METRIC_LEARN,
    VISIBLE_METRICS,
    benchmark_compare_available,
    benchmark_line,
    business_summary_full,
    business_summary_preview,
    format_metric_value,
    freshness_line,
    sector_gloss_line,
    sector_headline,
)
from markets import market_display_name
from live_quote import (
    LiveQuoteError,
    fetch_live_quote,
    get_cached_quote,
    live_quote_button_label,
    yahoo_finance_url,
)


def _benchmark_for_metric(card: dict, metric: str) -> str | None:
    for m_key, median_key, direction in BENCHMARK_METRICS:
        if m_key == metric:
            return benchmark_line(card, metric, median_key, direction)
    return None


def _esc(value: object) -> str:
    return html.escape("" if value is None else str(value))


def _format_market_code(market_code: str | None) -> str:
    return market_display_name(market_code)


def _benchmark_compare_body(card: dict) -> str:
    if not benchmark_compare_available(card):
        return ""

    bench_items: list[str] = []
    for metric in VISIBLE_METRICS + DEEP_DIVE_METRICS:
        for m_key, median_key, direction in BENCHMARK_METRICS:
            if m_key != metric:
                continue
            bench = benchmark_line(card, metric, median_key, direction)
            if bench:
                bench_items.append(
                    f"<li><span class=\"ss-benchmark-metric\">{_esc(METRIC_LABELS[metric])}</span> "
                    f"— {_esc(bench)}</li>"
                )
            break

    if not bench_items:
        return ""

    bench_list = f'<ul class="ss-benchmark-list">{"".join(bench_items)}</ul>'
    return f'<p class="ss-median-primer">{_esc(MEDIAN_PRIMER)}</p>{bench_list}'


def _metric_definitions_body() -> str:
    blocks = []
    for metric in VISIBLE_METRICS + DEEP_DIVE_METRICS:
        blocks.append(
            f"<dt>{_esc(METRIC_LABELS[metric])}</dt>"
            f"<dd>{_esc(METRIC_LEARN[metric])}</dd>"
        )
    return f'<dl class="ss-explain-list">{"".join(blocks)}</dl>'


def _learn_panel_html(card: dict) -> str:
    compare = _benchmark_compare_body(card)
    compare_section = ""
    if compare:
        compare_section = (
            f'<div class="ss-learn-section">'
            f'<p class="ss-learn-heading">How we compare to similar companies</p>'
            f"{compare}"
            f"</div>"
        )
    return (
        f'<details class="ss-learn-panel">'
        f"<summary>Understand these numbers</summary>"
        f'<div class="ss-learn-panel-body">'
        f"{compare_section}"
        f'<div class="ss-learn-section">'
        f'<p class="ss-learn-heading">What each metric means</p>'
        f"{_metric_definitions_body()}"
        f"</div>"
        f"</div>"
        f"</details>"
    )


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


def build_card_html(
    card: dict,
    *,
    scope_meta: str | None = None,
) -> str:
    company = card.get("company_name") or card.get("ticker") or "Unknown"
    ticker = card.get("ticker") or "—"
    if scope_meta:
        meta_line = scope_meta
    else:
        meta_line = _format_market_code(card.get("market_code"))

    sector_head = sector_headline(card)
    sector_gloss = sector_gloss_line(card.get("sector"))

    hero = "".join(_metric_cell_html(card, m) for m in VISIBLE_METRICS)
    balance = "".join(_metric_cell_html(card, m) for m in DEEP_DIVE_METRICS)

    identity = (
        f'<section class="ss-card ss-card-identity">'
        f'<p class="ss-meta-line">{_esc(meta_line)}</p>'
        f'<p class="ss-identity">'
        f'<span class="ss-company">{_esc(company)}</span> '
        f'<span class="ss-ticker">{_esc(ticker)}</span></p>'
        f"{_company_summary_html(card)}"
        f'<div class="ss-sector-context">'
        f'<p class="ss-sector-headline">{_esc(sector_head)}</p>'
        f'<p class="ss-sector-gloss">{_esc(sector_gloss)}</p>'
        f"</div>"
        f"</section>"
    )
    learn = _learn_panel_html(card)
    metrics = (
        f'<section class="ss-card ss-card-metrics">'
        f'<div class="ss-metrics-grid ss-metrics-hero">{hero}</div>'
        f'<div class="ss-metrics-grid ss-metrics-balance">{balance}</div>'
        f"</section>"
    )
    return identity + learn + metrics


def render_card_footer(card: dict, *, widget_key_prefix: str = "card") -> None:
    fresh = freshness_line(card)
    yahoo_url = yahoo_finance_url(card)
    market_code = card.get("market_code") or "unknown"
    ticker = card.get("ticker") or "unknown"
    button_key = f"{widget_key_prefix}_live_quote_{market_code}_{ticker}"

    st.markdown('<div class="ss-card-footer-shell"></div>', unsafe_allow_html=True)
    fresh_col, quote_col, link_col = st.columns([1.1, 1.2, 0.9])

    with fresh_col:
        if fresh:
            st.markdown(
                f'<p class="ss-freshness">{_esc(fresh)}</p>',
                unsafe_allow_html=True,
            )

    with quote_col:
        if st.button(
            live_quote_button_label(card),
            key=button_key,
            use_container_width=True,
        ):
            fetch_live_quote(card)
            st.rerun()
        cached = get_cached_quote(card)
        if isinstance(cached, LiveQuoteError):
            st.caption(cached.message)

    with link_col:
        st.link_button(
            "Yahoo ↗",
            yahoo_url,
            use_container_width=True,
        )


def render_stock_card(
    card: dict,
    *,
    scope_meta: str | None = None,
    widget_key_prefix: str = "card",
) -> None:
    st.markdown(
        build_card_html(card, scope_meta=scope_meta),
        unsafe_allow_html=True,
    )
    render_card_footer(card, widget_key_prefix=widget_key_prefix)
