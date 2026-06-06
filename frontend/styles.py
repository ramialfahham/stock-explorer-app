"""Global Streamlit styling — dark editorial v2.1."""

from __future__ import annotations

import streamlit as st


def inject_global_css() -> None:
    st.markdown(
        """
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:ital,opsz,wght@0,9..40,400;0,9..40,500;0,9..40,600;0,9..40,700;1,9..40,400&display=swap');

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
    font-size: 0.85rem;
    font-weight: 700;
    color: var(--ss-text);
    letter-spacing: -0.02em;
    padding-top: 0.15rem;
}
.ss-header-stats {
    font-size: var(--ss-caption-size);
    color: var(--ss-caption);
    margin: 0.08rem 0 0.45rem;
    padding-bottom: 0.45rem;
    border-bottom: 1px solid var(--ss-border);
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
    margin: 0 0 0.65rem;
    padding-bottom: 0.55rem;
    border-bottom: 1px solid var(--ss-border);
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

.ss-metrics-grid {
    display: grid;
    gap: 0.5rem;
}
.ss-metrics-hero {
    grid-template-columns: repeat(3, minmax(0, 1fr));
    margin-bottom: 0.55rem;
}
.ss-metrics-balance {
    grid-template-columns: repeat(2, minmax(0, 1fr));
    padding-top: 0.55rem;
    border-top: 1px solid var(--ss-border);
    margin-bottom: 0.45rem;
}
@media (max-width: 380px) {
    .ss-metrics-hero {
        grid-template-columns: 1fr;
    }
}

.ss-metric-label {
    font-size: var(--ss-label);
    font-weight: 600;
    color: var(--ss-muted);
    margin: 0 0 0.15rem;
    line-height: 1.2;
}
.ss-metric-value {
    font-size: var(--ss-value);
    font-weight: 700;
    font-variant-numeric: tabular-nums;
    color: var(--ss-text);
    margin: 0;
    line-height: 1.1;
}
.ss-metric-bench {
    font-size: var(--ss-caption-size);
    color: var(--ss-caption);
    margin: 0.12rem 0 0;
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

.ss-card-footer {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 0.5rem;
    padding-top: 0.4rem;
    border-top: 1px solid var(--ss-border);
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

/* Saved list */
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

/* Overflow menu button */
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
