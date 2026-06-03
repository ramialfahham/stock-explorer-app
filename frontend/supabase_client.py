"""Supabase client helpers for Streamlit."""

from __future__ import annotations

import os

from dotenv import load_dotenv
from supabase import Client, create_client

load_dotenv()


def get_anon_client() -> Client:
    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_ANON_KEY")
    if not url or not key:
        raise RuntimeError("Set SUPABASE_URL and SUPABASE_ANON_KEY in environment or Streamlit secrets.")
    return create_client(url, key)


def client_for_session(session) -> Client:
    client = get_anon_client()
    client.auth.set_session(session.access_token, session.refresh_token)
    return client
