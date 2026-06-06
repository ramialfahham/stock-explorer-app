"""Global Streamlit styling — dark editorial shell."""

from __future__ import annotations

import streamlit as st


def inject_global_css() -> None:
    st.markdown(
        """
<style>
/* Hide Streamlit chrome */
#MainMenu, footer, header[data-testid="stHeader"] {
    visibility: hidden;
    height: 0;
    min-height: 0;
}
section[data-testid="stSidebar"] {
    display: none !important;
}
.stDeployButton {
    display: none;
}

/* App shell */
[data-testid="stAppViewContainer"] {
    background: #0a0a0b;
}
.block-container {
    padding: 0.5rem 1rem 6rem;
    max-width: 480px;
}

/* Top bar */
.ss-topbar {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 0.35rem 0 0.75rem;
    border-bottom: 1px solid #27272a;
    margin-bottom: 0.75rem;
}
.ss-brand {
    font-size: 0.95rem;
    font-weight: 700;
    letter-spacing: -0.02em;
    color: #f4f4f5;
}
.ss-chips {
    display: flex;
    gap: 0.4rem;
}
.ss-chip {
    font-size: 0.7rem;
    font-weight: 600;
    letter-spacing: 0.02em;
    text-transform: uppercase;
    color: #a1a1aa;
    background: #141416;
    border: 1px solid #27272a;
    border-radius: 999px;
    padding: 0.2rem 0.55rem;
}

/* Utility row */
.ss-utility-row-marker + div[data-testid="stHorizontalBlock"] button {
    font-size: 0.75rem !important;
    padding: 0.1rem 0 !important;
    min-height: 0 !important;
    background: transparent !important;
    border: none !important;
    color: #71717a !important;
    box-shadow: none !important;
}
.ss-utility-row-marker + div[data-testid="stHorizontalBlock"] button:hover {
    color: #c9a962 !important;
}

/* Segmented nav */
div[data-testid="stSegmentedControl"] {
    margin-bottom: 0.75rem;
}
div[data-testid="stSegmentedControl"] button {
    font-size: 0.8rem !important;
    font-weight: 600 !important;
}

/* Card */
.ss-card {
    background: #141416;
    border: 1px solid #27272a;
    border-radius: 14px;
    padding: 0.85rem 0.95rem 0.75rem;
}
.ss-card-header {
    margin-bottom: 0.65rem;
}
.ss-card-meta-row {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    flex-wrap: wrap;
    margin-bottom: 0.35rem;
}
.ss-queue-chip {
    font-size: 0.65rem;
    font-weight: 700;
    letter-spacing: 0.04em;
    text-transform: uppercase;
    color: #71717a;
}
.ss-ticker {
    font-size: 0.8rem;
    font-weight: 700;
    color: #c9a962;
}
.ss-market {
    font-size: 0.65rem;
    font-weight: 600;
    letter-spacing: 0.04em;
    text-transform: uppercase;
    color: #71717a;
    margin-left: auto;
}
.ss-company {
    font-size: 1.35rem;
    font-weight: 700;
    line-height: 1.15;
    letter-spacing: -0.02em;
    color: #f4f4f5;
    margin: 0;
}
.ss-sector {
    font-size: 0.8rem;
    color: #a1a1aa;
    margin: 0.25rem 0 0;
    line-height: 1.35;
}
.ss-muted {
    color: #71717a;
}

/* Metrics grid — 3 columns on wider screens, stack on narrow */
.ss-metrics-grid {
    display: grid;
    grid-template-columns: repeat(3, minmax(0, 1fr));
    gap: 0.55rem;
    margin-bottom: 0.55rem;
}
@media (max-width: 420px) {
    .ss-metrics-grid {
        grid-template-columns: 1fr;
    }
}
.ss-metrics-stack {
    display: flex;
    flex-direction: column;
    gap: 0.55rem;
    padding-top: 0.35rem;
}
.ss-metric {
    min-width: 0;
}
.ss-metric-head {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 0.25rem;
    margin-bottom: 0.1rem;
}
.ss-metric-label {
    font-size: 0.62rem;
    font-weight: 700;
    letter-spacing: 0.05em;
    text-transform: uppercase;
    color: #71717a;
}
.ss-metric-value {
    font-size: 1.15rem;
    font-weight: 700;
    line-height: 1.1;
    color: #f4f4f5;
    margin: 0;
}
.ss-metric-hint {
    font-size: 0.68rem;
    line-height: 1.3;
    color: #71717a;
    margin: 0.15rem 0 0;
}
.ss-metric-bench {
    font-size: 0.65rem;
    line-height: 1.25;
    color: #52525b;
    margin: 0.15rem 0 0;
}
.ss-metric-learn {
    margin: 0;
}
.ss-metric-learn summary {
    list-style: none;
    cursor: pointer;
    font-size: 0.65rem;
    font-weight: 700;
    color: #52525b;
    width: 1rem;
    text-align: center;
    line-height: 1;
}
.ss-metric-learn summary::-webkit-details-marker {
    display: none;
}
.ss-metric-learn[open] summary {
    color: #a1a1aa;
}
.ss-metric-learn p {
    font-size: 0.68rem;
    line-height: 1.35;
    color: #a1a1aa;
    margin: 0.25rem 0 0;
}

/* Deep dive */
.ss-deep-dive {
    border-top: 1px solid #27272a;
    padding-top: 0.45rem;
    margin-top: 0.15rem;
}
.ss-deep-dive summary {
    cursor: pointer;
    font-size: 0.72rem;
    font-weight: 600;
    letter-spacing: 0.02em;
    color: #a1a1aa;
    list-style: none;
}
.ss-deep-dive summary::-webkit-details-marker {
    display: none;
}

/* Card footer */
.ss-card-footer {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 0.5rem;
    margin-top: 0.55rem;
    padding-top: 0.45rem;
    border-top: 1px solid #27272a;
}
.ss-freshness {
    font-size: 0.65rem;
    color: #52525b;
    margin: 0;
}
.ss-yahoo-link {
    font-size: 0.65rem;
    font-weight: 600;
    color: #71717a;
    text-decoration: none;
    white-space: nowrap;
}
.ss-yahoo-link:hover {
    color: #c9a962;
}

/* Saved list */
.ss-saved-list {
    display: flex;
    flex-direction: column;
    gap: 0.35rem;
    margin-bottom: 0.75rem;
}
.ss-saved-row {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 0.5rem;
    padding: 0.45rem 0;
    border-bottom: 1px solid #27272a;
}
.ss-saved-name {
    font-size: 0.85rem;
    font-weight: 600;
    color: #f4f4f5;
    margin: 0;
}
.ss-saved-ticker {
    color: #c9a962;
    font-weight: 700;
}
.ss-saved-sector {
    font-size: 0.68rem;
    color: #71717a;
    margin: 0.1rem 0 0;
}

/* Welcome */
.welcome-panel {
    background: #141416;
    border: 1px solid #27272a;
    border-radius: 14px;
    padding: 1rem 1.1rem;
    margin-bottom: 0.75rem;
}
.welcome-lead {
    font-size: 0.9rem;
    color: #d4d4d8;
    line-height: 1.45;
    margin: 0;
}

/* Sticky action bar — marker div + next horizontal block */
.ss-action-shell + div[data-testid="stHorizontalBlock"] {
    position: fixed;
    left: 50%;
    transform: translateX(-50%);
    bottom: 0;
    width: min(480px, calc(100% - 2rem));
    padding: 0.65rem 0 calc(0.65rem + env(safe-area-inset-bottom));
    background: linear-gradient(to top, #0a0a0b 85%, transparent);
    z-index: 999;
    margin: 0 !important;
}
.ss-action-shell + div[data-testid="stHorizontalBlock"] button[kind="primary"] {
    background: #c9a962 !important;
    color: #0a0a0b !important;
    border: none !important;
    font-weight: 700 !important;
}
.ss-action-shell + div[data-testid="stHorizontalBlock"] button[kind="secondary"] {
    background: #141416 !important;
    color: #a1a1aa !important;
    border: 1px solid #27272a !important;
}

/* Search input */
[data-testid="stTextInput"] input {
    background: #141416 !important;
    border-color: #27272a !important;
    color: #f4f4f5 !important;
}

/* Compact empty states */
[data-testid="stAlert"] {
    font-size: 0.85rem;
    padding: 0.65rem 0.85rem;
}
</style>
""",
        unsafe_allow_html=True,
    )
