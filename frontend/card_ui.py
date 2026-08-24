"""Stock card layout — scannable HTML, numbers-first."""

from __future__ import annotations

import html

import streamlit as st

from card_copy import (
    BENCHMARK_METRICS,
    MEDIAN_PRIMER,
    METRIC_ANALOGY,
    METRIC_LABELS,
    VERDICT_BADGE_LABEL,
    VERDICT_EMOJI,
    ai_read,
    benchmark_compare_available,
    benchmark_compare_unavailable_learn,
    benchmark_indicator_label,
    benchmark_range,
    business_summary_full,
    business_summary_is_truncated,
    business_summary_preview,
    format_metric_value,
    freshness_line,
    health_verdict_token,
    metric_analogy,
    metric_gloss,
    metric_label,
    metric_learn_text,
    metric_perspective_label,
    metrics_for_card,
    sector_gloss_line,
    sector_headline,
)
from disclosure_html import disclosure_html
from markets import market_display_name
from live_quote import yahoo_finance_url
from metric_school import render_metric_playgrounds


def _range_point_html(row_class: str, left: str, text: str) -> str:
    """One min/median/max entry, center-aligned on its real bar position via a shared
    CSS class (transform: translateX(-50%)) — only the dynamic `left` is inline."""
    return f'<span class="{row_class}" style="left:{left}">{text}</span>'


def _metric_range_html(card: dict, metric: str) -> str:
    """Monochrome range mark: numbers row (min/median/max values) above the bar, the bar
    itself (two segments with a gap at the median, plus this company's marker), then a
    word-labels row ("min"/"median"/"max") below — all three points center-aligned on
    their real position using the identical rule, so min/median/max read as one
    consistent reference framework and the marker is the only thing that moves within
    it. Replaces the old inline "Higher/Lower than sector median" text on the card face —
    see docs/ui/card_metric_cell.md."""
    for m_key, median_key, _direction in BENCHMARK_METRICS:
        if m_key != metric:
            continue
        rng = benchmark_range(card, metric, median_key)
        if rng is None:
            return ""
        currency = card.get("currency")
        min_label = _esc(format_metric_value(metric, rng["min"], currency))
        max_label = _esc(format_metric_value(metric, rng["max"], currency))
        median_label = _esc(format_metric_value(metric, rng["median"], currency))
        median_pct = rng["median_pct"]
        value_pct = rng["position_pct"]
        # min/max sit exactly at the track's own edges (0%/100%) -- nothing to collide
        # with there but the container's own padding. median can fall anywhere between
        # them, so its *label* position (not the bar's own gap, which stays exact) is
        # floored 3rem from either edge to keep it clear of the min/max text.
        median_left = f"clamp(3rem, {median_pct}%, calc(100% - 3rem))"
        numbers_row = (
            _range_point_html("ss-metric-range-number", "0%", min_label)
            + _range_point_html("ss-metric-range-number", median_left, median_label)
            + _range_point_html("ss-metric-range-number", "100%", max_label)
        )
        words_row = (
            _range_point_html("ss-metric-range-word", "0%", "min")
            + _range_point_html("ss-metric-range-word", median_left, "median")
            + _range_point_html("ss-metric-range-word", "100%", "max")
        )
        return (
            f'<div class="ss-metric-range">'
            f'<div class="ss-metric-range-numbers">{numbers_row}</div>'
            f'<div class="ss-metric-range-track">'
            f'<div class="ss-metric-range-bar ss-metric-range-bar-start" '
            f'style="width:calc({median_pct}% - 2px)"></div>'
            f'<div class="ss-metric-range-bar ss-metric-range-bar-end" '
            f'style="left:calc({median_pct}% + 2px)"></div>'
            f'<div class="ss-metric-range-marker" style="left:{value_pct}%"></div>'
            f"</div>"
            f'<div class="ss-metric-range-words">{words_row}</div>'
            f"</div>"
        )
    return ""


def _metric_range_unavailable_html() -> str:
    """Stand-in for _metric_range_html() when it returns "" (never benchmarked, or
    this card's sector is below the peer threshold) -- without it, the card jumps
    straight from value to gloss with no visual cue that the gap is deliberate,
    which reads as a missing/broken element rather than an absence of data."""
    return '<p class="ss-metric-range-unavailable">No sector comparison for this metric.</p>'


def _benchmark_compare_body(card: dict) -> str:
    if not benchmark_compare_available(card):
        return ""

    bench_items: list[str] = []
    for metric in metrics_for_card(card):
        for m_key, median_key, _direction in BENCHMARK_METRICS:
            if m_key != metric:
                continue
            label = benchmark_indicator_label(card, metric, median_key)
            if label:
                bench_items.append(
                    f"<li>"
                    f'<span class="ss-benchmark-metric">{_esc(metric_label(metric, card))}</span> '
                    f'<span class="ss-bench-indicator">{_esc(label)}</span>'
                    f"</li>"
                )
            break

    if not bench_items:
        return ""

    bench_list = f'<ul class="ss-benchmark-list">{"".join(bench_items)}</ul>'
    return f'<p class="ss-median-primer">{_esc(MEDIAN_PRIMER)}</p>{bench_list}'


def _metric_learn_block_html(card: dict, metric: str) -> str:
    value = card.get(metric)
    full_body = f'<p class="ss-metric-learn-body">{_esc(metric_learn_text(metric, value, card))}</p>'
    toggle = disclosure_html(
        "",
        full_body,
        more_label="Read more",
        less_label="Show less",
    )
    return (
        f'<div class="ss-metric-learn-item">'
        f'<p class="ss-metric-learn-heading">{_esc(metric_label(metric, card))}</p>'
        f'<p class="ss-metric-analogy">{_esc(metric_analogy(metric, value, card))}</p>'
        f"{toggle}"
        f"</div>"
    )


def _metric_learn_blocks(card: dict) -> str:
    return _metric_stack_with_groups(card, _metric_learn_block_html)


def _metric_definitions_body(card: dict) -> str:
    return f'<div class="ss-metric-learn-list">{_metric_learn_blocks(card)}</div>'


def _esc(value: object) -> str:
    return html.escape("" if value is None else str(value))


def _format_market_code(market_code: str | None) -> str:
    return market_display_name(market_code)


def build_learn_panel_body_html(card: dict) -> str:
    """Inner HTML for the one learn expander: benchmark compare, then flattened metric
    definitions (each with its own Read more/Show less). No outer toggle — that's the
    st.expander itself now.

    Company description does NOT render here — it has its own inline toggle on the card
    face (`_company_summary_html`), right where a reader would expect to click it, instead
    of living at the bottom of a panel titled for explaining numbers."""
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
        f"{compare_section}"
        f'<div class="ss-learn-section">'
        f'<p class="ss-learn-heading">What each metric means</p>'
        f"{_metric_definitions_body(card)}"
        f"</div>"
    )


def _company_summary_html(card: dict) -> str:
    """Card-face preview. When truncated, gets its own inline Read more/Show less right
    where a reader would click it — not a separate section at the bottom of the learn
    panel. Short descriptions render plain, nothing more to reveal."""
    preview = business_summary_preview(card)
    if not preview:
        return ""
    if not business_summary_is_truncated(card):
        return f'<p class="ss-company-summary">{_esc(preview)}</p>'
    full = business_summary_full(card)
    if not full:
        return f'<p class="ss-company-summary">{_esc(preview)}</p>'
    return disclosure_html(
        _esc(preview),
        f'<p class="ss-company-summary-full">{_esc(full)}</p>',
        more_label="Read more",
        less_label="Show less",
    )


def _health_block_html(card: dict) -> str:
    """Verdict badge + AI read, or "" when no card_assessments row matched this card —
    never a placeholder. Both always visible when present, no click needed."""
    token = health_verdict_token(card)
    if not token:
        return ""
    badge = (
        f'<p class="ss-verdict-badge">'
        f'<span class="ss-verdict-emoji">{_esc(VERDICT_EMOJI[token])}</span>'
        f'<span class="ss-verdict-label">{_esc(VERDICT_BADGE_LABEL[token])}</span>'
        f"</p>"
    )
    read = ai_read(card)
    read_html = f'<p class="ss-ai-read">{_esc(read)}</p>' if read else ""
    return f'<div class="ss-health-block">{badge}{read_html}</div>'


def _metric_stack_with_groups(card: dict, cell_fn) -> str:
    """Render metrics_for_card(card) through cell_fn, inserting a lens group heading
    whenever the perspective changes. metrics_for_card() already sorts every metric by
    lens (see card_copy.py's _LENS_ORDER) — this makes that grouping visible instead of
    silently only affecting order. Shared by the card face and the learn panel so both
    group the same way."""
    blocks: list[str] = []
    current_group: str | None = None
    for metric in metrics_for_card(card):
        group = metric_perspective_label(metric)
        if group != current_group:
            blocks.append(f'<p class="ss-metric-group-heading">{_esc(group)}</p>')
            current_group = group
        blocks.append(cell_fn(card, metric))
    return "".join(blocks)


def _metric_cell_html(card: dict, metric: str) -> str:
    label = metric_label(metric, card)
    value = format_metric_value(metric, card.get(metric), card.get("currency"))
    gloss = metric_gloss(metric, card.get(metric), card)
    range_html = _metric_range_html(card, metric) or _metric_range_unavailable_html()
    gloss_html = f'<p class="ss-metric-gloss">{_esc(gloss)}</p>'
    value_row = (
        f'<p class="ss-metric-value-row">'
        f'<span class="ss-metric-value">{_esc(value)}</span>'
        f"</p>"
    )
    return (
        f'<div class="ss-metric">'
        f'<p class="ss-metric-label">{_esc(label)}</p>'
        f"{value_row}"
        f"{range_html}"
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

    metrics_html = _metric_stack_with_groups(card, _metric_cell_html)

    identity = (
        f'<section class="ss-card ss-card-identity">'
        f'<p class="ss-meta-line">{_esc(meta_line)}</p>'
        f'<p class="ss-identity">'
        f'<span class="ss-company">{_esc(company)}</span> '
        f'<span class="ss-ticker">{_esc(ticker)}</span></p>'
        f"{_health_block_html(card)}"
        f"{_company_summary_html(card)}"
        f'<div class="ss-sector-context">'
        f'<p class="ss-sector-headline">{_esc(sector_head)}</p>'
        f'<p class="ss-sector-gloss">{_esc(sector_gloss)}</p>'
        f"</div>"
        f"</section>"
    )
    metrics = (
        f'<section class="ss-card ss-card-metrics">'
        f'<div class="ss-metrics-grid ss-metrics-stack">{metrics_html}</div>'
        f"</section>"
    )
    return identity + metrics


def render_learn_panel(card: dict, *, widget_key_prefix: str = "card") -> None:
    """The one learn panel: benchmark compare, then per-metric definitions (each behind its
    own Read more/Show less), then the interactive practice widgets — all in a single
    st.expander. Company description does NOT render here — see
    `_company_summary_html`'s own inline toggle on the card face."""
    with st.expander("Understand these numbers", expanded=False):
        body = build_learn_panel_body_html(card)
        if body:
            st.markdown(body, unsafe_allow_html=True)
        render_metric_playgrounds(card, widget_key_prefix=widget_key_prefix)


def render_card_footer(card: dict, *, widget_key_prefix: str = "card") -> None:
    fresh = freshness_line(card)
    yahoo_url = yahoo_finance_url(card)

    st.markdown('<div class="ss-card-footer-shell"></div>', unsafe_allow_html=True)
    fresh_col, link_col = st.columns([2, 1])

    with fresh_col:
        if fresh:
            st.markdown(
                f'<p class="ss-freshness">{_esc(fresh)}</p>',
                unsafe_allow_html=True,
            )

    with link_col:
        st.link_button(
            "Yahoo Finance",
            yahoo_url,
            use_container_width=True,
        )


def render_stock_card(
    card: dict,
    *,
    scope_meta: str | None = None,
    widget_key_prefix: str = "card",
    show_learn_panel: bool = True,
) -> None:
    st.markdown(
        build_card_html(card, scope_meta=scope_meta),
        unsafe_allow_html=True,
    )
    if show_learn_panel:
        render_learn_panel(card, widget_key_prefix=widget_key_prefix)
    render_card_footer(card, widget_key_prefix=widget_key_prefix)
