"""Stock card layout — scannable HTML, numbers-first."""

from __future__ import annotations

import html

import streamlit as st

from card_copy import (
    ALL_METRICS,
    BENCHMARK_METRICS,
    MEDIAN_PRIMER,
    METRIC_ANALOGY,
    METRIC_LABELS,
    benchmark_compare_available,
    benchmark_compare_unavailable_learn,
    benchmark_indicator,
    benchmark_indicator_label,
    business_summary_full,
    business_summary_is_truncated,
    business_summary_preview,
    format_metric_value,
    freshness_line,
    metric_analogy,
    metric_gloss,
    metric_label,
    metric_learn_text,
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
from metric_school import render_metric_micro_checks, render_metric_playgrounds


def _bench_indicator_html(card: dict, metric: str) -> str:
    for m_key, median_key, _direction in BENCHMARK_METRICS:
        if m_key != metric:
            continue
        indicator = benchmark_indicator(card, metric, median_key)
        if not indicator:
            return ""
        label = benchmark_indicator_label(card, metric, median_key) or ""
        return (
            f'<span class="ss-bench-indicator" title="{_esc(label)}" '
            f'aria-label="{_esc(label)}">{_esc(indicator)}</span>'
        )
    return ""


def _benchmark_compare_body(card: dict) -> str:
    if not benchmark_compare_available(card):
        return ""

    bench_items: list[str] = []
    for metric in ALL_METRICS:
        for m_key, median_key, _direction in BENCHMARK_METRICS:
            if m_key != metric:
                continue
            indicator = benchmark_indicator(card, metric, median_key)
            if indicator:
                label = benchmark_indicator_label(card, metric, median_key) or ""
                bench_items.append(
                    f"<li>"
                    f'<span class="ss-benchmark-metric">{_esc(metric_label(metric, card))}</span> '
                    f'<span class="ss-bench-indicator" title="{_esc(label)}" '
                    f'aria-label="{_esc(label)}">{_esc(indicator)}</span> '
                    f'<span class="ss-bench-vs">vs median</span>'
                    f"</li>"
                )
            break

    if not bench_items:
        return ""

    bench_list = f'<ul class="ss-benchmark-list">{"".join(bench_items)}</ul>'
    return f'<p class="ss-median-primer">{_esc(MEDIAN_PRIMER)}</p>{bench_list}'


def _metric_learn_blocks(card: dict) -> str:
    blocks: list[str] = []
    for metric in ALL_METRICS:
        value = card.get(metric)
        blocks.append(
            f'<details class="ss-metric-learn-item">'
            f"<summary>{_esc(metric_label(metric, card))}</summary>"
            f'<p class="ss-metric-analogy">{_esc(metric_analogy(metric, value, card))}</p>'
            f'<p class="ss-metric-gloss-inline">{_esc(metric_gloss(metric, value, card))}</p>'
            f'<p class="ss-metric-learn-body">{_esc(metric_learn_text(metric, value, card))}</p>'
            f"</details>"
        )
    return "".join(blocks)


def _metric_definitions_body(card: dict) -> str:
    return f'<div class="ss-metric-learn-list">{_metric_learn_blocks(card)}</div>'


def _esc(value: object) -> str:
    return html.escape("" if value is None else str(value))


def _format_market_code(market_code: str | None) -> str:
    return market_display_name(market_code)


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
    elif unavailable := benchmark_compare_unavailable_learn(card):
        compare_section = (
            f'<div class="ss-learn-section">'
            f'<p class="ss-learn-heading">How we compare to similar companies</p>'
            f'<p class="ss-benchmark-unavailable">{_esc(unavailable)}</p>'
            f"</div>"
        )
    return (
        f'<details class="ss-learn-panel">'
        f"<summary>Understand these numbers</summary>"
        f'<div class="ss-learn-panel-body">'
        f"{compare_section}"
        f'<div class="ss-learn-section">'
        f'<p class="ss-learn-heading">What each metric means</p>'
        f"{_metric_definitions_body(card)}"
        f"</div>"
        f"</div>"
        f"</details>"
    )


def _company_summary_html(card: dict) -> str:
    full = business_summary_full(card)
    if not full:
        return ""
    preview = business_summary_preview(card)
    if not preview:
        return ""
    if not business_summary_is_truncated(card):
        return f'<p class="ss-company-summary">{_esc(full)}</p>'
    return (
        f'<details class="ss-company-about">'
        f'<summary class="ss-company-summary-toggle">'
        f'<span class="ss-company-summary-preview">{_esc(preview)}</span>'
        f'<span class="ss-company-summary-action">'
        f'<span class="ss-company-summary-more">Read full description</span>'
        f'<span class="ss-company-summary-less">Show less</span>'
        f"</span>"
        f"</summary>"
        f'<p class="ss-company-summary-full">{_esc(full)}</p>'
        f"</details>"
    )


def _metric_cell_html(card: dict, metric: str) -> str:
    label = metric_label(metric, card)
    value = format_metric_value(metric, card.get(metric))
    gloss = metric_gloss(metric, card.get(metric), card)
    indicator = _bench_indicator_html(card, metric)
    gloss_html = f'<p class="ss-metric-gloss">{_esc(gloss)}</p>'
    value_row = (
        f'<p class="ss-metric-value-row">'
        f'<span class="ss-metric-value">{_esc(value)}</span>'
        f"{indicator}"
        f"</p>"
    )
    return (
        f'<div class="ss-metric">'
        f'<p class="ss-metric-label">{_esc(label)}</p>'
        f"{value_row}"
        f"{gloss_html}"
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

    metrics_html = "".join(_metric_cell_html(card, m) for m in ALL_METRICS)

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
        f'<div class="ss-metrics-grid ss-metrics-stack">{metrics_html}</div>'
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
    show_metric_school: bool = True,
) -> None:
    st.markdown(
        build_card_html(card, scope_meta=scope_meta),
        unsafe_allow_html=True,
    )
    if show_metric_school:
        with st.expander("Practice with hypothetical numbers", expanded=False):
            render_metric_playgrounds(card, widget_key_prefix=widget_key_prefix)
        with st.expander("Quick check — test your understanding", expanded=False):
            render_metric_micro_checks(card, widget_key_prefix=widget_key_prefix)
    render_card_footer(card, widget_key_prefix=widget_key_prefix)
