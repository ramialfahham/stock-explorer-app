"""Supabase client helpers for Streamlit."""

from __future__ import annotations

import streamlit as st
from supabase import Client, create_client

from settings import get_supabase_anon_key, get_supabase_url


@st.cache_resource
def get_anon_client() -> Client:
    """The anonymous (non-user-specific) Supabase client, built once and reused across every
    session and script rerun. Uncached, `create_client()` measured at ~1.06-1.09s per call;
    since Streamlit reruns the whole script on every widget interaction, that cost was being
    paid on every single click, twice per row click (frontend/row_ui.py's st.rerun() aborts and
    restarts a run). Safe to share globally: this client carries no per-user auth state, only
    the public anon key.
    """
    url = get_supabase_url()
    key = get_supabase_anon_key()
    if not url or not key:
        raise RuntimeError(
            "Set SUPABASE_URL and SUPABASE_ANON_KEY in Streamlit secrets or .env."
        )
    return create_client(url, key)
