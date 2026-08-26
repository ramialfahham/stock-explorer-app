"""Global Streamlit styling — dark editorial v2.1."""

from __future__ import annotations

import streamlit as st


def inject_global_css() -> None:
    st.markdown(
        """
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:ital,opsz,wght@0,9..40,400;0,9..40,500;0,9..40,600;0,9..40,700;1,9..40,400&family=Fraunces:opsz,wght@9..144,600;9..144,700&display=swap');

:root {
    --ss-bg: #0a0a0b;
    --ss-surface: #141416;
    --ss-text: #f4f4f5;
    --ss-muted: #a1a1aa;
    --ss-caption: #94949e;
    --ss-accent: #c9a962;
    --ss-border: #27272a;
    --ss-track: #38383d;
    --ss-value: 1.5rem;
    --ss-title: 1rem;
    --ss-label: 0.75rem;
    --ss-caption-size: 0.72rem;
    --ss-bottom-nav-h: 3.25rem;
    --ss-action-bar-h: 3.25rem;

    /* Design system tokens (Slice 6a) — see docs/ui/design_system.md */
    --ss-space-1: 0.35rem;
    --ss-space-2: 0.55rem;
    --ss-space-3: 0.75rem;
    --ss-space-4: 0.85rem;
    --ss-radius-control: 0.5rem;
    --ss-radius-surface: 0.75rem;
    --ss-row-title: 0.85rem;
}

html, body, [class*="css"] {
    font-family: "DM Sans", sans-serif !important;
}

#MainMenu, footer, header[data-testid="stHeader"], .stDeployButton {
    visibility: hidden !important;
    height: 0 !important;
    min-height: 0 !important;
    display: none !important;
}
section[data-testid="stSidebar"] {
    display: none !important;
}

/* Design system: every button gets a consistent corner radius by default (Slice 6a) and,
   since Slice 6b, the accent/surface color skin app-wide too (see the global
   button[kind="primary"/"secondary"] rules below). See docs/ui/design_system.md. */
[data-testid="stButton"] button {
    border-radius: var(--ss-radius-control);
}

[data-testid="stAppViewContainer"] {
    background: var(--ss-bg);
    overflow-x: clip;
}
[data-testid="stAppViewContainer"] .main {
    overflow-x: clip;
}
.block-container {
    padding: 0.4rem var(--ss-space-4) calc(var(--ss-action-bar-h) + 0.5rem);
    max-width: 480px;
    margin-left: auto !important;
    margin-right: auto !important;
    width: 100%;
    box-sizing: border-box;
}
/* Header — title + tagline only */
.ss-brand-header {
    min-width: 0;
}
.ss-brand {
    font-family: "Fraunces", Georgia, "Times New Roman", serif;
    font-size: 1.35rem;
    font-weight: 600;
    color: var(--ss-text);
    letter-spacing: -0.03em;
    padding-top: 0;
    line-height: 1.15;
    margin: 0;
}
.ss-brand-tagline {
    font-size: 0.74rem;
    color: var(--ss-muted);
    margin: 0.28rem 0 0.45rem;
    line-height: 1.35;
    max-width: none;
}
.ss-header-stats {
    font-size: var(--ss-caption-size);
    color: var(--ss-caption);
    margin: 0.35rem 0 0.45rem;
    padding-bottom: 0.45rem;
    border-bottom: 1px solid var(--ss-border);
}
.ss-header-stats--solo {
    margin: 0.35rem 0 0.45rem;
    padding-bottom: 0.45rem;
    border-bottom: 1px solid var(--ss-border);
}
.ss-header-pool {
    font-size: var(--ss-caption-size);
    color: var(--ss-muted);
    margin: 0 0 0.45rem;
    padding-bottom: 0.45rem;
    border-bottom: 1px solid var(--ss-border);
    line-height: 1.35;
}

.ss-market-breakdown {
    margin: 0 0 0.65rem;
    font-size: var(--ss-caption-size);
    color: var(--ss-caption);
}
.ss-market-breakdown summary {
    cursor: pointer;
    color: var(--ss-accent);
    margin-bottom: 0.25rem;
}
.ss-market-breakdown-body {
    margin: 0;
    line-height: 1.45;
    color: var(--ss-muted);
}

/* Card */
.ss-card {
    background: var(--ss-surface);
    border: 1px solid var(--ss-border);
    border-radius: var(--ss-radius-surface);
    padding: 0.7rem 0.8rem 0.6rem;
}
.ss-card-identity .ss-meta-line {
    font-size: var(--ss-caption-size);
    color: var(--ss-caption);
    margin: 0 0 0.35rem;
    line-height: 1.3;
}
.ss-identity {
    margin: 0 0 0.65rem;
    line-height: 1.3;
}
.ss-company {
    font-size: var(--ss-title);
    font-weight: 600;
    color: var(--ss-text);
}
.ss-ticker {
    font-size: var(--ss-title);
    font-weight: 700;
    color: var(--ss-accent);
}

.ss-sector-context {
    margin: 0;
    padding-bottom: 0;
    border-bottom: none;
}
.ss-sector-context .ss-sector-headline {
    font-size: var(--ss-caption-size);
    font-weight: 600;
    color: var(--ss-text);
    margin: 0 0 0.12rem;
    line-height: 1.3;
}
.ss-sector-context .ss-sector-gloss {
    font-size: var(--ss-caption-size);
    color: var(--ss-caption);
    margin: 0;
    line-height: 1.35;
}

/* Scoped under .ss-card-identity, same wrapper as .ss-meta-line above (both render inside
   build_card_html()'s `identity` section) -- see the .ss-metric .ss-metric-gloss comment
   below for why a bare class isn't enough. */
.ss-card-identity .ss-company-summary {
    font-size: 0.78rem;
    color: var(--ss-text);
    margin: 0 0 0.55rem;
    line-height: 1.45;
}

/* Scoped under .ss-disclosure-wrap (not a bare class) -- see the .ss-metric .ss-metric-gloss
   comment below for why: a bare single-class <p> selector silently loses font-size (and any
   non-zero margin-top/left/right) to a Streamlit emotion-cache `<ancestor> p` reset at higher
   specificity. .ss-disclosure-wrap is the one, always-present wrapper disclosure_html()
   renders around this content, also covering .ss-company-summary-full below (same wrapper,
   different caller -- disclosure_html()'s full_body_html argument). .ss-company-summary
   (no "-full") is a DIFFERENT class for a different case -- _company_summary_html()'s two
   early-return branches that bypass disclosure_html() entirely for a short, non-truncated
   description -- and is scoped separately under .ss-card-identity instead, below. */
.ss-disclosure-wrap .ss-disclosure-preview {
    font-size: 0.78rem;
    color: var(--ss-text);
    margin: 0 0 0.28rem;
    line-height: 1.45;
}

.ss-disclosure-wrap:has(.ss-disclosure[open]) .ss-disclosure-preview {
    display: none;
}

.ss-disclosure {
    margin: 0;
}

.ss-disclosure summary.ss-disclosure-toggle {
    cursor: pointer;
    list-style: none;
    margin: 0 0 0.35rem;
    width: fit-content;
}

.ss-disclosure summary.ss-disclosure-toggle::-webkit-details-marker {
    display: none;
}

.ss-disclosure-more,
.ss-disclosure-less {
    font-size: 0.72rem;
    font-weight: 600;
    color: var(--ss-accent);
    text-decoration: underline;
    line-height: 1.3;
}

.ss-disclosure:not([open]) .ss-disclosure-less {
    display: none;
}

.ss-disclosure[open] .ss-disclosure-more {
    display: none;
}

.ss-disclosure[open] summary.ss-disclosure-toggle {
    margin-bottom: 0.35rem;
}

.ss-disclosure-wrap .ss-company-summary-full {
    margin: 0;
    font-size: 0.78rem;
    color: var(--ss-text);
    line-height: 1.45;
}

/* Verdict badge + AI read (Slice 6c) — Scan-tier signal, always visible. */
/* The two card-face content blocks are visually distinct on purpose: the assessment is
   model-written prose, the description is the company's own words. Before this they ran
   together as one wall of text and a reader could not tell which was which. The panel
   sits on --ss-bg inside the card's --ss-surface, one step darker, so the separation
   survives without adding a new colour to the palette. */
.ss-health-block {
    /* Deliberately tight. Two new labels plus this panel's own padding cost real vertical
       space on the card face, and docs/working_agreement.md's UX gate wants the first
       metric value above the fold at 480px wide. Every value here was trimmed to the
       smallest that still reads as a separate panel; do not pad this out without
       re-running that check. */
    margin: 0 0 var(--ss-space-2);
    padding: var(--ss-space-1) var(--ss-space-2) var(--ss-space-2);
    background: var(--ss-bg);
    border: 1px solid var(--ss-border);
    border-radius: var(--ss-radius-surface);
}
.ss-company-block {
    margin: 0 0 0.55rem;
}
/* Both block labels. Scoped under .ss-card-identity -- their always-present wrapper (see
   build_card_html()'s `identity` section) -- and NOT written as a bare `.ss-block-label`
   <p> selector, which would silently lose font-size and any non-zero margin to a
   Streamlit emotion-cache `<ancestor> p` reset at higher specificity. That exact bug has
   shipped six times in this file across three MRs; see the .ss-metric .ss-metric-gloss
   comment below for the full explanation. Same small-uppercase accent treatment as
   .ss-metric-group-heading, so the card has one labelling language rather than two. */
.ss-card-identity .ss-block-label {
    font-size: var(--ss-caption-size);
    font-weight: 600;
    color: var(--ss-accent);
    text-transform: uppercase;
    letter-spacing: 0.06em;
    margin: 0 0 0.2rem;
    line-height: 1.2;
}
/* Both scoped under .ss-health-block (their always-present wrapper, see _health_block_html())
   -- see the .ss-metric .ss-metric-gloss comment below for why a bare class isn't enough. */
.ss-health-block .ss-verdict-badge {
    display: inline-flex;
    align-items: center;
    gap: 0.3rem;
    font-size: var(--ss-label);
    font-weight: 600;
    color: var(--ss-text);
    /* --ss-surface, not --ss-bg: the panel around it is now --ss-bg, and a chip cannot
       sit on its own background colour and still read as a chip. */
    background: var(--ss-surface);
    border: 1px solid var(--ss-border);
    border-radius: var(--ss-radius-control);
    padding: var(--ss-space-1) var(--ss-space-2);
    margin: 0 0 0.3rem;
}
.ss-health-block .ss-ai-read {
    font-size: 0.78rem;
    color: var(--ss-text);
    margin: 0 0 0.28rem;
    line-height: 1.45;
}

.ss-learn-section + .ss-learn-section {
    margin-top: 0.55rem;
    padding-top: 0.55rem;
    border-top: 1px solid var(--ss-border);
}
.ss-learn-section .ss-learn-heading {
    font-size: var(--ss-caption-size);
    font-weight: 600;
    color: var(--ss-text);
    margin: 0 0 0.3rem;
    line-height: 1.3;
}

.ss-card-metrics {
    margin-top: 0.5rem;
}

.ss-metric-sources {
    font-size: var(--ss-caption-size);
    color: var(--ss-caption);
    margin: 0.35rem 0 0.45rem;
    line-height: 1.35;
}

/* Scoped under .ss-learn-section, their always-present wrapper -- see the
   .ss-metric .ss-metric-gloss comment below for why. (.ss-benchmark-note has no current
   caller -- scoped anyway so it doesn't reintroduce this bug if it's ever used again.) */
.ss-learn-section .ss-median-primer,
.ss-learn-section .ss-benchmark-note {
    font-size: var(--ss-caption-size);
    color: var(--ss-caption);
    margin: 0 0 0.45rem;
    line-height: 1.35;
}

.ss-benchmark-compare {
    margin: 0.35rem 0 0;
    font-size: var(--ss-caption-size);
    color: var(--ss-caption);
}
.ss-benchmark-compare summary {
    cursor: pointer;
    color: var(--ss-accent);
    margin-bottom: 0.25rem;
}
.ss-benchmark-list {
    margin: 0.35rem 0 0;
    padding-left: 1rem;
    line-height: 1.4;
}
.ss-benchmark-metric {
    color: var(--ss-text);
    font-weight: 600;
}

/* !important, not parent-scoped: rendered directly inside a bare st.columns() column with
   no wrapping ancestor class -- see the .ss-metric .ss-metric-gloss comment below for the
   underlying Streamlit specificity issue this and !important both work around. */
.ss-filter-summary {
    font-size: var(--ss-caption-size) !important;
    color: var(--ss-muted);
    margin: 0;
    line-height: 1.35;
    text-align: right;
}

.ss-benchmark-unavailable {
    margin: 0;
    line-height: 1.4;
    color: var(--ss-caption);
}

.ss-metrics-grid {
    display: grid;
    gap: 0.95rem;
}
.ss-metrics-stack {
    grid-template-columns: 1fr;
    margin-bottom: 0.45rem;
}
.ss-metrics-stack .ss-metric {
    padding: 0.35rem 0;
}

/* Metric label chip (Slice 6c) — applied uniformly, no hero/secondary split exists.
   Scoped under .ss-metric like .ss-metric-gloss below it — see that rule's comment. */
.ss-metric .ss-metric-label {
    display: inline-block;
    font-size: var(--ss-label);
    font-weight: 600;
    color: var(--ss-text);
    background: var(--ss-bg);
    border: 1px solid var(--ss-border);
    border-radius: var(--ss-radius-control);
    padding: var(--ss-space-1) var(--ss-space-2);
    margin: 0 0 0.3rem;
    line-height: 1.3;
}
.ss-metric-value-row {
    display: flex;
    align-items: baseline;
    gap: 0.35rem;
    margin: 0;
}
.ss-metric-value {
    font-size: var(--ss-value);
    font-weight: 700;
    font-variant-numeric: tabular-nums;
    color: var(--ss-text);
    line-height: 1.1;
}
.ss-bench-indicator {
    font-size: var(--ss-caption-size);
    font-weight: 600;
    color: var(--ss-caption);
    line-height: 1.2;
}

/* Metric range mark (card face) — numbers row above the bar, the bar itself (gap at
   the median, marker = this company), a word-labels row below. min/median/max are all
   center-aligned on their real position with the same rule — see
   docs/ui/card_metric_cell.md. */
.ss-metric-range {
    margin: 0.5rem 0 0;
    padding: 0 1.2rem;
}
.ss-metric-range-numbers,
.ss-metric-range-words {
    position: relative;
    height: 0.8125rem;
}
.ss-metric-range-number,
.ss-metric-range-word {
    position: absolute;
    top: 0;
    line-height: 1;
    white-space: nowrap;
    transform: translateX(-50%);
}
.ss-metric-range-number {
    max-width: 5rem;
    overflow: hidden;
    text-overflow: ellipsis;
    font-size: var(--ss-caption-size);
    font-variant-numeric: tabular-nums;
    color: var(--ss-caption);
}
.ss-metric-range-word {
    font-size: var(--ss-caption-size);
    color: var(--ss-caption);
}
.ss-metric-range-track {
    position: relative;
    height: 0.6875rem;
    margin: 0.2rem 0;
}
.ss-metric-range-bar {
    position: absolute;
    top: 0.15625rem;
    height: 0.375rem;
    background: var(--ss-track);
}
.ss-metric-range-bar-start {
    left: 0;
    border-radius: 0.2rem 0 0 0.2rem;
}
.ss-metric-range-bar-end {
    right: 0;
    border-radius: 0 0.2rem 0.2rem 0;
}
.ss-metric-range-marker {
    position: absolute;
    top: 0;
    width: 0.1875rem;
    height: 0.6875rem;
    background: var(--ss-accent);
    border-radius: 0.1rem;
    transform: translateX(-50%);
}
/* font-size and margin both live only in the two scoped rules below, not here -- a
   Streamlit emotion-cache rule resets both properties on any bare `<p class="single">`
   at higher specificity than a single class, silently overriding either one if set
   here instead. font-weight/color/text-transform/letter-spacing are untouched by that
   reset, so they're safe on the bare class. */
.ss-metric-group-heading {
    font-weight: 600;
    color: var(--ss-accent);
    text-transform: uppercase;
    letter-spacing: 0.06em;
}
/* Card face lays metrics out on a CSS grid with its own `gap` between every item, so a
   heading's own margins would stack on top of that gap instead of replacing it: pull
   back above for a deliberate section break, negative below so the heading reads as
   attached to its group rather than floating equidistant between both neighbors. */
.ss-metrics-stack .ss-metric-group-heading {
    font-size: 0.68rem;
    margin: 0.45rem 0 -0.65rem;
}
.ss-metrics-stack .ss-metric-group-heading:first-child {
    margin-top: 0;
}
/* Learn panel is plain block flow (no grid `gap`), so its margins are the real values
   directly, not grid-gap-offset like the card face above. */
.ss-metric-learn-list .ss-metric-group-heading {
    font-size: 0.68rem;
    margin: 0.9rem 0 0.35rem;
}
.ss-metric-learn-list .ss-metric-group-heading:first-child {
    margin-top: 0;
}
/* .ss-metric > p (not a bare class selector): Streamlit's own emotion-cache stylesheet
   carries a `<ancestor-class> p { margin-top: 0; ... }` reset at (0,1,1) specificity,
   which silently wins over a same-weight single-class rule regardless of source order.
   Scoping under the parent keeps these at (0,2,0) so the margin actually applies. */
/* Deliberately a step LARGER and LIGHTER than the range mark's own min/median/max
   labels below it (--ss-caption-size / --ss-caption). This is the line that explains the
   metric; those are axis furniture. At the same size and colour the explanation read as
   a footnote to the bar rather than the point of the cell. 0.78rem matches the card's
   other body copy (.ss-ai-read, .ss-company-summary). */
.ss-metric .ss-metric-gloss {
    font-size: 0.78rem;
    color: var(--ss-muted);
    margin: 0.5rem 0 0;
    line-height: 1.35;
}
.ss-metric .ss-metric-range-unavailable {
    margin: 0.5rem 0 0;
    font-size: var(--ss-caption-size);
    font-style: italic;
    color: var(--ss-muted);
}

/* Explain all */
.ss-explain-all {
    margin: 0.35rem 0 0.45rem;
}
.ss-explain-all summary {
    cursor: pointer;
    font-size: var(--ss-caption-size);
    font-weight: 600;
    color: var(--ss-muted);
    list-style: none;
}
.ss-explain-all summary::before {
    content: "▸ ";
    color: var(--ss-accent);
}
.ss-explain-all[open] summary::before {
    content: "▾ ";
}
.ss-explain-all summary::-webkit-details-marker {
    display: none;
}
.ss-explain-list {
    margin: 0.45rem 0 0;
    padding: 0;
}
.ss-explain-list dt {
    font-size: var(--ss-caption-size);
    font-weight: 700;
    color: var(--ss-text);
    margin-top: 0.35rem;
}
.ss-explain-list dd {
    font-size: var(--ss-caption-size);
    color: var(--ss-muted);
    margin: 0.1rem 0 0;
    line-height: 1.4;
}
.ss-metric-learn-list {
    margin: 0.35rem 0 0;
}
.ss-metric-learn-item {
    border-top: 1px solid var(--ss-border);
    padding: 0.35rem 0;
}
.ss-metric-learn-item .ss-metric-learn-heading {
    font-size: var(--ss-caption-size);
    font-weight: 700;
    color: var(--ss-text);
    margin: 0 0 0.2rem;
}
.ss-metric-learn-item .ss-metric-analogy {
    font-size: var(--ss-caption-size);
    color: var(--ss-caption);
    margin: 0.35rem 0 0.2rem;
    line-height: 1.4;
}
.ss-metric-learn-item .ss-metric-learn-body {
    font-size: var(--ss-caption-size);
    color: var(--ss-muted);
    margin: 0;
    line-height: 1.45;
}

.ss-card-footer {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 0.5rem;
    padding-top: 0.4rem;
    border-top: 1px solid var(--ss-border);
}
/* Found alongside the .ss-freshness fix below and sharing its exact root cause (same
   review pass caught it): .ss-card-footer-shell's own next sibling is nothing (it's alone
   inside its stMarkdownContainer) -- the real sibling relationship is one level up, between
   the shell's stElementContainer and the following stLayoutWrapper, same as .ss-freshness.
   Confirmed live this plain `+ div[data-testid="stHorizontalBlock"]` selector matched zero
   elements, so this footer separator (border/spacing above Yahoo Finance link) has never
   actually rendered. */
[data-testid="stElementContainer"]:has(.ss-card-footer-shell) + [data-testid="stLayoutWrapper"] {
    margin-top: -0.35rem;
    padding-top: 0.45rem;
    border-top: 1px solid var(--ss-border);
}
/* :has() is already used this way for the icon-button trigger further down this file. */
[data-testid="stElementContainer"]:has(.ss-card-footer-shell) + [data-testid="stLayoutWrapper"] .ss-freshness {
    font-size: var(--ss-caption-size);
    color: var(--ss-caption);
    margin: 0;
    line-height: 1.35;
}
/* Pre-existing rule (predates Slice 6b) — testid corrected from "stLinkButton" to the real
   rendered value, "stBaseLinkButton-secondary", but the sibling-combinator prefix was the
   same broken assumption as the two rules above (.ss-card-footer-shell has no next sibling
   of its own -- the real relationship is one level up, stElementContainer -> stLayoutWrapper,
   same as .ss-freshness and the footer separator). Confirmed live: this compact footer
   sizing has never actually applied until this fix. */
[data-testid="stElementContainer"]:has(.ss-card-footer-shell) + [data-testid="stLayoutWrapper"] a[data-testid="stBaseLinkButton-secondary"] {
    font-size: var(--ss-caption-size) !important;
    min-height: 2rem !important;
    padding: 0.25rem 0.5rem !important;
    text-decoration: none !important;
}

/* Saved list */
/* !important, not parent-scoped: same reasoning as .ss-filter-summary above (bare
   st.markdown() call, no wrapping ancestor class). */
.ss-saved-list-fresh {
    font-size: var(--ss-caption-size) !important;
    color: var(--ss-caption);
    margin: 0 0 0.65rem;
}
/* Row primitive (Slice 6a) — shared by Saved list and Search results.
   See docs/ui/design_system.md. Left-aligned HTML row + invisible full-row tap target. */
:has(.ss-row-group) div[data-testid="stVerticalBlock"]:has(.ss-row) {
    position: relative;
    margin: 0 0 0.45rem;
}
:has(.ss-row-group) .ss-row {
    background: var(--ss-surface);
    border: 1px solid var(--ss-border);
    border-radius: var(--ss-radius-surface);
    padding: var(--ss-space-2) var(--ss-space-4);
    text-align: left;
    pointer-events: none;
}
:has(.ss-row-group) div[data-testid="stVerticalBlock"]:has(> [data-testid="stElementContainer"] .ss-row):hover .ss-row {
    border-color: var(--ss-accent);
}
:has(.ss-row-group) div[data-testid="stVerticalBlock"]:has(.ss-row) [data-testid="stMarkdown"] {
    margin: 0;
}
:has(.ss-row-group) div[data-testid="stVerticalBlock"]:has(.ss-row) [data-testid="stButton"] {
    position: absolute;
    inset: 0;
    z-index: 1;
    margin: 0;
    min-height: 3.1rem;
}
:has(.ss-row-group) div[data-testid="stVerticalBlock"]:has(.ss-row) [data-testid="stButton"] > button {
    width: 100% !important;
    height: 100% !important;
    min-height: 3.1rem !important;
    margin: 0 !important;
    padding: 0 !important;
    opacity: 0 !important;
    border: none !important;
    background: transparent !important;
    box-shadow: none !important;
}
.ss-saved-fresh {
    font-size: var(--ss-caption-size);
    color: var(--ss-caption);
    margin: 0.12rem 0 0;
}

/* !important on both font-size AND margin, not parent-scoped: same reasoning as
   .ss-filter-summary above, but this one also sets a non-zero margin-top -- unlike its
   siblings (which only ever set margin-bottom), that top value is the one Streamlit's
   ancestor `p` rule actually zeroes, not just font-size. Confirmed live: without
   !important, margin-top silently computed to 0 instead of the declared value. */
.ss-saved-news-heading {
    font-size: var(--ss-caption-size) !important;
    font-weight: 600;
    color: var(--ss-muted);
    text-transform: uppercase;
    letter-spacing: 0.06em;
    margin: var(--ss-space-3) 0 0.4rem !important;
}

.ss-saved-news-list {
    margin: 0 0 0.35rem;
}

.ss-saved-news-item {
    margin: 0 0 0.55rem;
    padding-bottom: 0.45rem;
    border-bottom: 1px solid var(--ss-border);
}

.ss-saved-news-item:last-child {
    border-bottom: none;
    padding-bottom: 0;
}

/* Both scoped under .ss-saved-news-item, their always-present wrapper (headline_item_html())
   -- see the .ss-metric .ss-metric-gloss comment below for why. */
.ss-saved-news-item .ss-saved-news-line,
.ss-saved-news-item .ss-disclosure-full {
    font-size: 0.78rem;
    color: var(--ss-text);
    margin: 0;
    line-height: 1.45;
}

.ss-saved-news-line a,
.ss-disclosure-full a {
    color: var(--ss-text);
    text-decoration: underline;
    text-underline-offset: 2px;
}

.ss-saved-news-pub {
    color: var(--ss-caption);
    font-size: var(--ss-caption-size);
}

.ss-row .ss-row-title {
    font-size: var(--ss-row-title);
    font-weight: 600;
    color: var(--ss-text);
    margin: 0;
}
.ss-row .ss-row-sub {
    font-size: var(--ss-caption-size);
    color: var(--ss-caption);
    margin: 0.08rem 0 0;
}

/* Landing (first visit) */
.ss-landing {
    padding: 1.5rem 0 1rem;
}
/* All three scoped under .ss-landing, their always-present wrapper (render_landing()) --
   see the .ss-metric .ss-metric-gloss comment below for why. */
.ss-landing .ss-landing-eyebrow {
    font-size: var(--ss-caption-size);
    font-weight: 600;
    color: var(--ss-accent);
    text-transform: uppercase;
    letter-spacing: 0.08em;
    margin: 0 0 0.5rem;
}
.ss-landing-title {
    font-family: "Fraunces", Georgia, "Times New Roman", serif;
    font-size: 1.75rem;
    font-weight: 700;
    color: var(--ss-text);
    letter-spacing: -0.03em;
    margin: 0 0 0.55rem;
    line-height: 1.15;
}
.ss-landing .ss-landing-tagline {
    font-size: 0.95rem;
    color: var(--ss-muted);
    line-height: 1.45;
    margin: 0 0 1.1rem;
}
.ss-landing-points {
    font-size: 0.85rem;
    color: var(--ss-muted);
    line-height: 1.5;
    margin: 0 0 1rem;
    padding-left: 1.1rem;
}
.ss-landing-points li {
    margin-bottom: 0.45rem;
}
.ss-landing .ss-landing-disclaimer {
    font-size: var(--ss-caption-size);
    color: var(--ss-caption);
    margin: 0 0 1.25rem;
}

/* Overflow menu panel */
.ss-menu-panel {
    margin: 0 0 0.65rem;
}
/* All three scoped under .ss-menu-panel, their always-present wrapper (menu_context_html())
   -- see the .ss-metric .ss-metric-gloss comment below for why. */
.ss-menu-panel .ss-menu-label {
    font-size: 0.68rem;
    font-weight: 600;
    color: var(--ss-muted);
    text-transform: uppercase;
    letter-spacing: 0.06em;
    margin: 0 0 0.2rem;
}
.ss-menu-panel .ss-menu-label + .ss-menu-body {
    margin-top: 0;
}
.ss-menu-panel .ss-menu-label:not(:first-child) {
    margin-top: 0.55rem;
}
.ss-menu-panel .ss-menu-body {
    font-size: var(--ss-caption-size);
    color: var(--ss-text);
    line-height: 1.4;
    margin: 0;
}
.ss-menu-panel .ss-menu-tip {
    font-size: var(--ss-caption-size);
    color: var(--ss-muted);
    line-height: 1.45;
    margin: 0;
    font-style: italic;
}
.ss-menu-actions-divider {
    border-top: 1px solid var(--ss-border);
    margin: 0.45rem 0 0.55rem;
}

/* Fixed action bar (Save / Skip). .ss-action-shell's own next sibling is nothing -- same
   broken assumption as .ss-card-footer-shell above (confirmed live: this rule matched zero
   elements, so Save/Skip has never actually been pinned to the viewport bottom; reaching it
   required scrolling through the whole card). Real relationship is one level up,
   stElementContainer -> stLayoutWrapper, same corrected pattern as the footer fixes. */
[data-testid="stElementContainer"]:has(.ss-action-shell) + [data-testid="stLayoutWrapper"] {
    position: fixed;
    left: 50%;
    transform: translateX(-50%);
    bottom: 0;
    width: min(480px, calc(100% - 1.7rem));
    z-index: 998;
    margin: 0 !important;
    padding: 0.35rem 0;
    background: linear-gradient(to top, var(--ss-bg) 80%, transparent);
}
/* Button color skin (Slice 6b) — global, not scoped to one surface. See
   docs/ui/design_system.md. Radius alone was globalized in 6a; color/background stayed
   scoped to just this action bar until 6b closed that gap app-wide. */
button[kind="primary"] {
    background: var(--ss-accent) !important;
    color: var(--ss-bg) !important;
    border: none !important;
    font-weight: 700 !important;
}
button[kind="secondary"] {
    background: var(--ss-surface) !important;
    color: var(--ss-muted) !important;
    border: 1px solid var(--ss-border) !important;
}
/* st.link_button renders as <a data-testid="stBaseLinkButton-{kind}">, not <button kind="...">,
   so the two rules above never reach it — cover all three kinds Streamlit's link_button
   supports (primary/secondary/tertiary) so a future variant never silently ships unstyled,
   even though only "secondary" has a live consumer today (the card footer's "Yahoo Finance"
   link). Selectors check the real testid, not the "stLinkButton" name the pre-existing
   footer-scoped rule below assumed — see its comment. This app has no separate visual tier
   for "tertiary" anywhere else, so it shares secondary's surface skin rather than inventing
   a third color; "primary" gets the same accent skin as button[kind="primary"] above. */
a[data-testid="stBaseLinkButton-primary"] {
    background: var(--ss-accent) !important;
    color: var(--ss-bg) !important;
    border: none !important;
    border-radius: var(--ss-radius-control) !important;
    font-weight: 700 !important;
}
a[data-testid="stBaseLinkButton-secondary"],
a[data-testid="stBaseLinkButton-tertiary"] {
    background: var(--ss-surface) !important;
    color: var(--ss-muted) !important;
    border: 1px solid var(--ss-border) !important;
    border-radius: var(--ss-radius-control) !important;
}

/* Nav row: Discover / Saved / Search + overflow menu (single line on mobile). Same broken
   sibling assumption as .ss-card-footer-shell/.ss-action-shell above (confirmed live: this
   prefix matched zero elements) -- fixed the same way. Less visibly broken than the action
   bar only by coincidence: st.container(horizontal=True) already renders flex/row natively,
   so the top-level intent happened to hold anyway; the gap/width/segmented-control sub-rules
   below did not (confirmed live: 16px gap instead of the intended --ss-space-1, and the
   segmented control at ~50% width instead of 100%). Descends one level further than the
   footer/action-bar fixes (`... [data-testid="stHorizontalBlock"]`, not just
   `[data-testid="stLayoutWrapper"]`) because these are flex-CONTAINER properties
   (align-items/flex-direction/gap) -- they only do anything on the actual `display:flex`
   element, confirmed live to be stLayoutWrapper's direct child, not stLayoutWrapper itself. */
[data-testid="stElementContainer"]:has(.ss-nav-row-marker) + [data-testid="stLayoutWrapper"] [data-testid="stHorizontalBlock"] {
    align-items: center !important;
    flex-direction: row !important;
    flex-wrap: nowrap !important;
    width: 100% !important;
    max-width: 100% !important;
    margin: 0 0 0.45rem !important;
    gap: var(--ss-space-1) !important;
}
[data-testid="stElementContainer"]:has(.ss-nav-row-marker) + [data-testid="stLayoutWrapper"] [data-testid="stHorizontalBlock"] > div:first-child,
[data-testid="stElementContainer"]:has(.ss-nav-row-marker) + [data-testid="stLayoutWrapper"] [data-testid="stHorizontalBlock"] [data-testid="column"]:first-child {
    min-width: 0 !important;
    flex: 1 1 auto !important;
    width: auto !important;
}
[data-testid="stElementContainer"]:has(.ss-nav-row-marker) + [data-testid="stLayoutWrapper"] [data-testid="stHorizontalBlock"] > div:last-child,
[data-testid="stElementContainer"]:has(.ss-nav-row-marker) + [data-testid="stLayoutWrapper"] [data-testid="stHorizontalBlock"] [data-testid="column"]:last-child {
    flex: 0 0 auto !important;
    width: auto !important;
    min-width: 0 !important;
    display: flex;
    align-items: stretch;
}
/* Second, separate bug in these two rules beyond the sibling-prefix one above: st.segmented_control()
   does not render a `data-testid="stSegmentedControl"` element at all -- confirmed live, the
   real wrapper carries `stButtonGroup` (same class of mistake as the stLinkButton/
   stBaseLinkButton-secondary correction above; each button itself is
   `stBaseButton-segmented_controlActive`/`...Inactive`, not checked here). */
[data-testid="stElementContainer"]:has(.ss-nav-row-marker) + [data-testid="stLayoutWrapper"] [data-testid="stHorizontalBlock"] [data-testid="stButtonGroup"] {
    width: 100%;
}
[data-testid="stElementContainer"]:has(.ss-nav-row-marker) + [data-testid="stLayoutWrapper"] [data-testid="stHorizontalBlock"] [data-testid="stButtonGroup"] button {
    font-size: 0.78rem !important;
    font-weight: 600 !important;
    min-height: 2.35rem !important;
}
/* Native widget theming (Slice 6b) — st.popover and st.expander rendered fully unstyled
   before this; both now match the app's surface/border language instead of default
   Streamlit chrome. See docs/ui/design_system.md. */
[data-testid="stPopoverButton"] {
    background: var(--ss-surface) !important;
    border: 1px solid var(--ss-border) !important;
    border-radius: var(--ss-radius-control) !important;
}
[data-testid="stExpander"] {
    background: var(--ss-surface) !important;
    border: 1px solid var(--ss-border) !important;
    border-radius: var(--ss-radius-surface) !important;
}
/* Icon-button variant (Slice 6a): keyed to an explicit marker, not DOM position — the
   prior :last-child selector would silently jump to the wrong button if the nav row is
   ever reordered. Reusable by any future icon-only popover trigger via the same marker.
   Streamlit wraps st.markdown in stElementContainer and st.popover in stLayoutWrapper —
   both direct children of the same stHorizontalBlock, hence :has() rather than a plain +
   on the marker itself (the marker is nested one level inside its own wrapper). Redeclares
   background/border/radius from the base popover-trigger rule above plus its own square
   sizing — same harmless redundant-match pattern used elsewhere in this file. */
[data-testid="stElementContainer"]:has(.ss-icon-btn-marker) + [data-testid="stLayoutWrapper"] [data-testid="stPopoverButton"] {
    font-size: 1.05rem !important;
    padding: 0 !important;
    min-height: 2.35rem !important;
    height: 2.35rem !important;
    width: 2.35rem !important;
    background: var(--ss-surface) !important;
    border: 1px solid var(--ss-border) !important;
    border-radius: var(--ss-radius-control) !important;
    color: var(--ss-muted) !important;
    box-shadow: none !important;
    display: inline-flex !important;
    align-items: center !important;
    justify-content: center !important;
    margin: 0 !important;
}
@media (max-width: 640px) {
    [data-testid="stElementContainer"]:has(.ss-nav-row-marker) + [data-testid="stLayoutWrapper"] [data-testid="stHorizontalBlock"] {
        flex-direction: row !important;
        flex-wrap: nowrap !important;
    }
    [data-testid="stElementContainer"]:has(.ss-nav-row-marker) + [data-testid="stLayoutWrapper"] [data-testid="stHorizontalBlock"] [data-testid="column"] {
        width: auto !important;
    }
    [data-testid="stElementContainer"]:has(.ss-nav-row-marker) + [data-testid="stLayoutWrapper"] [data-testid="stHorizontalBlock"] [data-testid="column"]:first-child {
        flex: 1 1 0 !important;
    }
    [data-testid="stElementContainer"]:has(.ss-nav-row-marker) + [data-testid="stLayoutWrapper"] [data-testid="stHorizontalBlock"] [data-testid="column"]:last-child {
        flex: 0 0 auto !important;
    }
}

[data-testid="stTextInput"] input {
    background: var(--ss-surface) !important;
    border-color: var(--ss-border) !important;
    color: var(--ss-text) !important;
}
[data-testid="stAlert"] {
    font-size: 0.82rem;
    padding: 0.55rem 0.75rem;
}
</style>
""",
        unsafe_allow_html=True,
    )
