"""Global Streamlit styling for Stock Swipe."""

from __future__ import annotations

import streamlit as st


def inject_global_css() -> None:
    st.markdown(
        """
<style>
/* App shell */
[data-testid="stAppViewContainer"] {
    background: #f7f8fa;
}
[data-testid="stHeader"] {
    background: transparent;
}
.block-container {
    padding-top: 1.25rem;
    padding-bottom: 2rem;
    max-width: 720px;
}

/* Typography */
h1 {
    font-size: 1.75rem !important;
    font-weight: 700 !important;
    letter-spacing: -0.02em;
}
h2, h3 {
    letter-spacing: -0.01em;
}

/* Tabs */
.stTabs [data-baseweb="tab-list"] {
    gap: 0.5rem;
    background: #eef1f5;
    border-radius: 10px;
    padding: 0.25rem;
}
.stTabs [data-baseweb="tab"] {
    border-radius: 8px;
    padding: 0.45rem 1rem;
    font-weight: 600;
}
.stTabs [aria-selected="true"] {
    background: #ffffff !important;
    box-shadow: 0 1px 3px rgba(15, 23, 42, 0.08);
}

/* Primary Save action — fallback when not using type=primary */
div[data-testid="column"]:first-child button[kind="secondary"] {
    background: #2563eb !important;
    color: #ffffff !important;
    border: 1px solid #2563eb !important;
    font-weight: 600;
}
div[data-testid="column"]:first-child button[kind="secondary"]:hover {
    background: #1d4ed8 !important;
    border-color: #1d4ed8 !important;
}

/* Saved list rows */
[data-testid="stSidebar"] hr {
    margin: 0.75rem 0;
}

/* Secondary Skip action */
div[data-testid="column"]:last-child button[kind="secondary"] {
    background: #ffffff !important;
    color: #475569 !important;
    border: 1px solid #cbd5e1 !important;
}

/* Metrics */
[data-testid="stMetric"] {
    background: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 10px;
    padding: 0.75rem 1rem;
}
[data-testid="stMetricLabel"] {
    font-size: 0.85rem !important;
    color: #64748b !important;
}
[data-testid="stMetricValue"] {
    font-size: 1.35rem !important;
    font-weight: 700 !important;
}

/* Sidebar */
[data-testid="stSidebar"] {
    background: #ffffff;
    border-right: 1px solid #e2e8f0;
}
[data-testid="stSidebar"] .stMarkdown p {
    font-size: 0.9rem;
    color: #64748b;
    line-height: 1.5;
}

/* Expanders and links */
[data-testid="stExpander"] {
    background: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 10px;
}

/* Welcome panel */
.welcome-panel {
    background: #ffffff;
    border: 1px solid #dbeafe;
    border-radius: 12px;
    padding: 1.25rem 1.5rem;
    margin-bottom: 1rem;
    box-shadow: 0 1px 3px rgba(37, 99, 235, 0.08);
}
.welcome-kicker {
    font-size: 0.8rem;
    font-weight: 700;
    letter-spacing: 0.04em;
    text-transform: uppercase;
    color: #2563eb;
    margin: 0 0 0.5rem 0;
}
.welcome-lead {
    font-size: 1.05rem;
    color: #0f172a;
    line-height: 1.5;
    margin: 0 0 0.75rem 0;
}
.welcome-list {
    margin: 0;
    padding-left: 1.25rem;
    color: #475569;
    line-height: 1.55;
}
.welcome-list li {
    margin-bottom: 0.35rem;
}

/* Stock card */
[data-testid="stVerticalBlockBorderWrapper"] {
    border-color: #e2e8f0 !important;
    border-radius: 12px !important;
    box-shadow: 0 1px 3px rgba(15, 23, 42, 0.06);
    padding: 0.25rem 0.5rem;
}
.card-progress-label {
    font-size: 0.8rem;
    font-weight: 600;
    color: #64748b;
    margin: 0 0 0.35rem 0;
    text-transform: uppercase;
    letter-spacing: 0.03em;
}
.card-company {
    font-size: 1.45rem;
    font-weight: 700;
    color: #0f172a;
    margin: 0;
    line-height: 1.25;
}
.card-ticker {
    font-size: 1rem;
    font-weight: 700;
    color: #2563eb;
    margin: 0;
    text-align: right;
}
.card-market {
    font-size: 0.75rem;
    font-weight: 600;
    color: #64748b;
    margin: 0.15rem 0 0 0;
    text-align: right;
    text-transform: uppercase;
    letter-spacing: 0.04em;
}
.card-sector {
    font-size: 0.95rem;
    color: #475569;
    margin: 0.25rem 0 0.75rem 0;
}
.card-freshness {
    font-size: 0.8rem;
    color: #64748b;
    margin: 0.75rem 0 0.5rem 0;
}
div[data-testid="column"] button[data-testid="stPopoverButton"] {
    font-size: 0.75rem;
    padding: 0.15rem 0.45rem;
    min-height: 1.75rem;
}
</style>
""",
        unsafe_allow_html=True,
    )
