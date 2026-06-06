"""Supabase client helpers for Streamlit."""

from __future__ import annotations

from supabase import Client, create_client

from settings import get_supabase_anon_key, get_supabase_url


def get_anon_client() -> Client:
    url = get_supabase_url()
    key = get_supabase_anon_key()
    if not url or not key:
        raise RuntimeError(
            "Set SUPABASE_URL and SUPABASE_ANON_KEY in Streamlit secrets or .env."
        )
    return create_client(url, key)


def client_for_session(session) -> Client:
    client = get_anon_client()
    client.auth.set_session(session.access_token, session.refresh_token)
    return client
