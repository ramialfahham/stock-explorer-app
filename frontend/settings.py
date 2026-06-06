"""Resolve config from Streamlit secrets (Cloud) or environment (local)."""

from __future__ import annotations

import os

from dotenv import load_dotenv

load_dotenv()


def _from_streamlit_secrets(key: str) -> str | None:
    try:
        import streamlit as st

        if key in st.secrets:
            value = st.secrets[key]
            return str(value) if value is not None else None
    except Exception:
        pass
    return None


def get_supabase_url() -> str | None:
    return _from_streamlit_secrets("SUPABASE_URL") or os.environ.get("SUPABASE_URL")


def get_supabase_anon_key() -> str | None:
    return _from_streamlit_secrets("SUPABASE_ANON_KEY") or os.environ.get(
        "SUPABASE_ANON_KEY"
    )
