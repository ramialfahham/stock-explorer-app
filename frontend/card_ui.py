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
    metrics_for_card,
    sector_gloss_line,
    sector_headline,
)
from disclosure_html import disclosure_html
from markets import market_display_name
from live_quote import yahoo_finance_url
from metric_school import render_metric_playgrounds


def _metric_range_html(card: dict, metric: str) -> str:
    """Monochrome range mark: this company's value positioned between its sector's min
    and max, median labeled at its own position. Replaces the old inline "Higher/Lower
    than sector median" text on the card face — see docs/ui/card_metric_cell.md."""
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
        return (
            f'<div class="ss-metric-range">'
            f'<span class="ss-metric-range-min">min {min_label}</span>'
            f'<div class="ss-metric-range-track">'
            f'<span class="ss-metric-range-median-label" '
            f'style="left:clamp(3rem, {median_pct}%, calc(100% - 3rem))">'
            f"median {median_label}</span>"
            f'<div class="ss-metric-range-bar ss-metric-range-bar-start" '
            f'style="width:calc({median_pct}% - 2px)"></div>'
            f'<div class="ss-metric-range-bar ss-metric-range-bar-end" '
            f'style="left:calc({median_pct}% + 2px)"></div>'
            f'<div class="ss-metric-range-marker" style="left:{value_pct}%"></div>'
            f"</div>"
            f'<span class="ss-metric-range-max">max {max_label}</span>'
            f"</div>"
        )
    return ""


def _direction_cue(card: dict, metric: str) -> str:
    """'. Lower is better.' gloss suffix, shown only alongside the range mark and only
    for metrics where a rightward marker is bad news, not good. A plain bar-and-marker
    otherwise reads as "further right = better" the way a loading bar or battery does —
    true for the 3 higher_better metrics, which need no cue since that already matches
    the convention.

    Applies uniformly to every metric the catalogue classifies `direction: lower_better`
    (today: forward_pe and net_debt_to_ebitda) — no metric-specific exception. This is a
    ceteris-paribus statement about the metric's own axis (a lower P/E is more
    attractively priced for the same growth/quality profile), not a health judgment, and
    it doesn't conflict with assessment_rules.py excluding P/E from the health verdict —
    that's about not letting P/E alone drive an automated composite score, a different and
    higher-stakes claim than just naming which way this one axis points. The caveat that
    P/E should be read alongside growth belongs in the metric's own deep-dive explanation
    (analogy/learn text in "Understand these numbers"), not a hedge stuffed into this
    short gloss line — a vague pointer like "read alongside growth" gives no actual
    guidance at a glance (owner feedback, after an earlier draft tried exactly that).

    The catalogue facts behind this are pinned by
    test_direction_cue_catalogue_assumptions_still_hold() in tests/frontend/test_card_ui.py.

    Suppressed when net_debt_to_ebitda's own value-aware "Net cash" gloss is already
    showing — that branch already states the favorable read directly; restating the axis
    on top of it is redundant, not informative.

    Tied to the same availability check as the range mark itself: no mark to
    disambiguate, no cue.
    """
    for m_key, median_key, direction in BENCHMARK_METRICS:
        if m_key != metric or direction != "lower":
            continue
        if metric == "net_debt_to_ebitda" and card.get(metric) is not None and card[metric] < 0:
            return ""
        if benchmark_range(card, metric, median_key) is None:
            return ""
        return ". Lower is better."
    return ""


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


def _metric_learn_blocks(card: dict) -> str:
    blocks: list[str] = []
    for metric in metrics_for_card(card):
        value = card.get(metric)
        full_body = f'<p class="ss-metric-learn-body">{_esc(metric_learn_text(metric, value, card))}</p>'
        toggle = disclosure_html(
            "",
            full_body,
            more_label="Read more",
            less_label="Show less",
        )
        blocks.append(
            f'<div class="ss-metric-learn-item">'
            f'<p class="ss-metric-learn-heading">{_esc(metric_label(metric, card))}</p>'
            f'<p class="ss-metric-analogy">{_esc(metric_analogy(metric, value, card))}</p>'
            f"{toggle}"
            f"</div>"
        )
    return "".join(blocks)


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


def _metric_cell_html(card: dict, metric: str) -> str:
    label = metric_label(metric, card)
    value = format_metric_value(metric, card.get(metric), card.get("currency"))
    gloss = metric_gloss(metric, card.get(metric), card) + _direction_cue(card, metric)
    range_html = _metric_range_html(card, metric)
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

    metrics_html = "".join(_metric_cell_html(card, m) for m in metrics_for_card(card))

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
