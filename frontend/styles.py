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
    --ss-value: 1.5rem;
    --ss-title: 1rem;
    --ss-label: 0.75rem;
    --ss-caption-size: 0.72rem;
    --ss-bottom-nav-h: 3.25rem;
    --ss-action-bar-h: 3.25rem;
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

[data-testid="stAppViewContainer"] {
    background: var(--ss-bg);
}
.block-container {
    padding: 0.4rem 0.85rem calc(var(--ss-bottom-nav-h) + var(--ss-action-bar-h) + 0.5rem);
    max-width: 480px;
}
.block-container.ss-no-actions {
    padding-bottom: calc(var(--ss-bottom-nav-h) + 0.5rem);
}

/* Header */
.ss-brand {
    font-family: "Fraunces", Georgia, "Times New Roman", serif;
    font-size: 1.45rem;
    font-weight: 600;
    color: var(--ss-text);
    letter-spacing: -0.03em;
    padding-top: 0.1rem;
    line-height: 1.15;
}
.ss-brand-tagline {
    font-size: 0.74rem;
    color: var(--ss-muted);
    margin: 0.15rem 0 0;
    line-height: 1.35;
    max-width: 22rem;
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
    border-radius: 12px;
    padding: 0.7rem 0.8rem 0.6rem;
}
.ss-meta-line {
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
.ss-sector-headline {
    font-size: var(--ss-caption-size);
    font-weight: 600;
    color: var(--ss-text);
    margin: 0 0 0.12rem;
    line-height: 1.3;
}
.ss-sector-gloss {
    font-size: var(--ss-caption-size);
    color: var(--ss-caption);
    margin: 0;
    line-height: 1.35;
}

.ss-company-summary {
    font-size: var(--ss-caption-size);
    color: var(--ss-caption);
    margin: 0 0 0.55rem;
    line-height: 1.4;
    display: -webkit-box;
    -webkit-line-clamp: 2;
    -webkit-box-orient: vertical;
    overflow: hidden;
}

.ss-company-about {
    margin: 0 0 0.55rem;
    font-size: var(--ss-caption-size);
    color: var(--ss-caption);
}

.ss-company-about summary {
    cursor: pointer;
    color: var(--ss-accent);
    margin-bottom: 0.35rem;
}

.ss-company-summary-full {
    margin: 0;
    line-height: 1.45;
    white-space: pre-wrap;
}

.ss-company-summary--empty {
    display: none;
}

.ss-learn-panel {
    margin: 0.5rem 0;
    font-size: var(--ss-caption-size);
    color: var(--ss-caption);
}
.ss-learn-panel summary {
    cursor: pointer;
    color: var(--ss-accent);
    font-weight: 600;
    font-size: var(--ss-caption-size);
    list-style: none;
}
.ss-learn-panel summary::before {
    content: "▸ ";
}
.ss-learn-panel[open] summary::before {
    content: "▾ ";
}
.ss-learn-panel summary::-webkit-details-marker {
    display: none;
}
.ss-learn-panel-body {
    margin-top: 0.35rem;
    padding: 0.55rem 0.65rem;
    background: var(--ss-surface);
    border: 1px solid var(--ss-border);
    border-radius: 10px;
}
.ss-learn-section + .ss-learn-section {
    margin-top: 0.55rem;
    padding-top: 0.55rem;
    border-top: 1px solid var(--ss-border);
}
.ss-learn-heading {
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

.ss-median-primer,
.ss-benchmark-note {
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

.ss-metrics-grid {
    display: grid;
    gap: 0.85rem;
}
.ss-metrics-hero {
    grid-template-columns: repeat(3, minmax(0, 1fr));
    margin-bottom: 0.65rem;
}
.ss-metrics-hero .ss-metric {
    padding: 0.35rem 0.25rem;
}
.ss-metrics-balance {
    grid-template-columns: repeat(2, minmax(0, 1fr));
    padding-top: 0.65rem;
    border-top: 1px solid var(--ss-border);
    margin-bottom: 0.45rem;
}
.ss-metrics-balance .ss-metric {
    padding: 0.25rem 0.15rem;
}
@media (max-width: 480px) {
    .ss-metrics-hero {
        grid-template-columns: 1fr;
        gap: 0.95rem;
    }
}

.ss-metric-label {
    font-size: var(--ss-label);
    font-weight: 600;
    color: var(--ss-muted);
    margin: 0 0 0.15rem;
    line-height: 1.2;
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
    font-size: 0.9em;
    font-weight: 600;
    color: var(--ss-caption);
    line-height: 1;
}
.ss-bench-vs {
    font-size: var(--ss-caption-size);
    color: var(--ss-caption);
}
.ss-metric-gloss {
    font-size: var(--ss-caption-size);
    color: var(--ss-caption);
    margin: 0.1rem 0 0;
    line-height: 1.25;
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
.ss-metric-learn-item summary {
    font-size: var(--ss-caption-size);
    font-weight: 700;
    color: var(--ss-text);
    cursor: pointer;
    list-style: none;
}
.ss-metric-learn-item summary::-webkit-details-marker {
    display: none;
}
.ss-metric-analogy {
    font-size: var(--ss-caption-size);
    font-weight: 600;
    color: var(--ss-accent);
    margin: 0.35rem 0 0.2rem;
    line-height: 1.4;
}
.ss-metric-gloss-inline {
    font-size: var(--ss-caption-size);
    color: var(--ss-muted);
    margin: 0 0 0.25rem;
    line-height: 1.35;
}
.ss-metric-learn-body {
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
.ss-card-footer-shell + div[data-testid="stHorizontalBlock"] {
    margin-top: -0.35rem;
    padding-top: 0.45rem;
    border-top: 1px solid var(--ss-border);
}
.ss-card-footer-shell + div[data-testid="stHorizontalBlock"] .ss-freshness {
    font-size: var(--ss-caption-size);
    color: var(--ss-caption);
    margin: 0;
    line-height: 1.35;
}
.ss-card-footer-shell + div[data-testid="stHorizontalBlock"] button {
    font-size: var(--ss-caption-size) !important;
    min-height: 2rem !important;
    padding: 0.25rem 0.5rem !important;
}
.ss-card-footer-shell + div[data-testid="stHorizontalBlock"] [data-testid="stCaptionContainer"] p {
    font-size: 0.68rem;
    color: var(--ss-caption);
}
.ss-freshness {
    font-size: var(--ss-caption-size);
    color: var(--ss-caption);
}
.ss-yahoo-link {
    font-size: var(--ss-caption-size);
    font-weight: 600;
    color: var(--ss-caption);
    text-decoration: none;
}
.ss-yahoo-link:hover {
    color: var(--ss-accent);
}

/* Saved learning list */
.ss-saved-list-heading {
    font-size: var(--ss-caption-size);
    font-weight: 600;
    color: var(--ss-muted);
    text-transform: uppercase;
    letter-spacing: 0.06em;
    margin: 0 0 0.5rem;
}
.ss-saved-row {
    margin: 0 0 0.35rem;
    padding: 0.45rem 0;
    border-bottom: 1px solid var(--ss-border);
}
.ss-saved-fresh {
    font-size: var(--ss-caption-size);
    color: var(--ss-caption);
    margin: 0.12rem 0 0;
}

/* Saved compare-two (vertical 5×2) */
.ss-compare-two-heading,
.ss-saved-news-heading {
    font-size: var(--ss-caption-size);
    font-weight: 600;
    color: var(--ss-muted);
    text-transform: uppercase;
    letter-spacing: 0.06em;
    margin: 0.75rem 0 0.4rem;
}
.ss-compare-two-wrap {
    margin: 0 0 0.85rem;
}
.ss-compare-two {
    width: 100%;
    border-collapse: collapse;
    font-size: 0.78rem;
    table-layout: fixed;
}
.ss-compare-two th,
.ss-compare-two td {
    border: 1px solid var(--ss-border);
    padding: 0.4rem 0.45rem;
    vertical-align: top;
    word-break: break-word;
}
.ss-compare-corner {
    background: var(--ss-surface);
    width: 28%;
}
.ss-compare-col {
    background: var(--ss-surface);
    text-align: left;
}
.ss-compare-ticker {
    display: block;
    font-weight: 700;
    color: var(--ss-accent);
}
.ss-compare-name {
    display: block;
    font-size: 0.72rem;
    color: var(--ss-caption);
    margin-top: 0.1rem;
}
.ss-compare-metric {
    font-weight: 600;
    color: var(--ss-muted);
    background: var(--ss-surface);
}
.ss-compare-value {
    font-variant-numeric: tabular-nums;
    font-weight: 600;
    color: var(--ss-text);
    text-align: right;
}

.ss-saved-name {
    font-size: 0.85rem;
    font-weight: 600;
    color: var(--ss-text);
    margin: 0;
}
.ss-saved-ticker {
    color: var(--ss-accent);
}
.ss-saved-sector {
    font-size: var(--ss-caption-size);
    color: var(--ss-caption);
    margin: 0.08rem 0 0;
}

.ss-browse-heading {
    font-size: var(--ss-caption-size);
    font-weight: 600;
    color: var(--ss-muted);
    margin: 0 0 0.35rem;
}
.ss-browse-name {
    font-size: 0.85rem;
    font-weight: 600;
    color: var(--ss-text);
    margin: 0;
}
.ss-browse-ticker {
    color: var(--ss-accent);
}
.ss-browse-sub {
    font-size: var(--ss-caption-size);
    color: var(--ss-caption);
    margin: 0.08rem 0 0;
}

/* Landing (first visit) */
.ss-landing {
    padding: 1.5rem 0 1rem;
}
.ss-landing-eyebrow {
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
.ss-landing-tagline {
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
.ss-landing-disclaimer {
    font-size: var(--ss-caption-size);
    color: var(--ss-caption);
    margin: 0 0 1.25rem;
}

/* Overflow menu panel */
.ss-menu-panel {
    margin: 0 0 0.65rem;
}
.ss-menu-label {
    font-size: 0.68rem;
    font-weight: 600;
    color: var(--ss-muted);
    text-transform: uppercase;
    letter-spacing: 0.06em;
    margin: 0 0 0.2rem;
}
.ss-menu-label + .ss-menu-body {
    margin-top: 0;
}
.ss-menu-label:not(:first-child) {
    margin-top: 0.55rem;
}
.ss-menu-body {
    font-size: var(--ss-caption-size);
    color: var(--ss-text);
    line-height: 1.4;
    margin: 0;
}
.ss-menu-tip {
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

/* Overflow menu trigger */
.ss-menu-popover button {
    font-size: 1.1rem !important;
    padding: 0.1rem 0.45rem !important;
    min-height: 0 !important;
    background: transparent !important;
    border: none !important;
    color: var(--ss-muted) !important;
    box-shadow: none !important;
}

/* Fixed action bar (Save / Skip) */
.ss-action-shell + div[data-testid="stHorizontalBlock"] {
    position: fixed;
    left: 50%;
    transform: translateX(-50%);
    bottom: var(--ss-bottom-nav-h);
    width: min(480px, calc(100% - 1.7rem));
    z-index: 998;
    margin: 0 !important;
    padding: 0.35rem 0;
    background: linear-gradient(to top, var(--ss-bg) 80%, transparent);
}
.ss-action-shell + div[data-testid="stHorizontalBlock"] button[kind="primary"] {
    background: var(--ss-accent) !important;
    color: var(--ss-bg) !important;
    border: none !important;
    font-weight: 700 !important;
}
.ss-action-shell + div[data-testid="stHorizontalBlock"] button[kind="secondary"] {
    background: var(--ss-surface) !important;
    color: var(--ss-muted) !important;
    border: 1px solid var(--ss-border) !important;
}

/* Fixed bottom nav */
.ss-bottom-nav-marker + div[data-testid="stSegmentedControl"] {
    position: fixed;
    left: 50%;
    transform: translateX(-50%);
    bottom: 0;
    width: min(480px, 100%);
    z-index: 999;
    margin: 0 !important;
    padding: 0.35rem 0.85rem calc(0.35rem + env(safe-area-inset-bottom));
    background: var(--ss-bg);
    border-top: 1px solid var(--ss-border);
}
.ss-bottom-nav-marker + div[data-testid="stSegmentedControl"] button {
    font-size: 0.78rem !important;
    font-weight: 600 !important;
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
