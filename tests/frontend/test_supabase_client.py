"""Supabase anon-client caching.

WHY THIS FILE EXISTS: get_anon_client() used to rebuild a Supabase client from scratch on
every single Streamlit script rerun -- measured at ~1.06-1.09s per call, versus ~0.12-0.18s
for everything else in a render combined. Since Streamlit reruns the whole script on every
widget interaction, and frontend/row_ui.py's row click handler calls st.rerun() right after
registering a click (aborting the in-flight run and starting a fresh one), this cost was paid
twice per row click -- closely matching an owner report of a 1-2s delay after clicking a row,
even after Discover's list was paginated. @st.cache_resource fixes it; this guards the fix.
"""

from __future__ import annotations

from unittest.mock import patch

import supabase_client


def _clear_cache() -> None:
    supabase_client.get_anon_client.clear()


def test_get_anon_client_is_cached_across_calls() -> None:
    """The whole point of the fix: create_client() runs once, not on every call, so a client
    built on script rerun N is reused on rerun N+1 instead of rebuilt from scratch."""
    _clear_cache()
    sentinel = object()
    with (
        patch("supabase_client.get_supabase_url", return_value="https://example.supabase.co"),
        patch("supabase_client.get_supabase_anon_key", return_value="test-anon-key"),
        patch("supabase_client.create_client", return_value=sentinel) as mock_create,
    ):
        first = supabase_client.get_anon_client()
        second = supabase_client.get_anon_client()
    assert first is second
    assert mock_create.call_count == 1
    _clear_cache()


def test_get_anon_client_raises_on_every_call_when_credentials_missing() -> None:
    """The credential check must still run and still raise on EVERY call, not just the first --
    a cache must not paper over a genuinely missing configuration by silently swallowing the
    exception on retry. A single call can't tell a real fix from a regression where the failure
    itself gets cached and a second call returns something falsy instead of re-raising; this
    calls it three times to actually prove that isn't happening."""
    _clear_cache()
    with (
        patch("supabase_client.get_supabase_url", return_value=None),
        patch("supabase_client.get_supabase_anon_key", return_value=None),
    ):
        for _ in range(3):
            try:
                supabase_client.get_anon_client()
                raise AssertionError("expected RuntimeError for missing credentials")
            except RuntimeError as exc:
                assert "SUPABASE_URL" in str(exc)
    _clear_cache()
