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

/* Primary Save action */
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
</style>
""",
        unsafe_allow_html=True,
    )
