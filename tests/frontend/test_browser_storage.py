"""Tests for browser_storage.py: the saved list persisted in cookies.

The request's cookies are faked at `browser_storage._request_cookies` (AppTest and bare mode
carry no request headers); the cookie-writing script is asserted as rendered HTML, never
executed here. `st.session_state` works standalone outside `streamlit run`, so it is used
as-is.
"""

from __future__ import annotations

from typing import Any

import pytest
import streamlit as st

import browser_storage as bs


@pytest.fixture(autouse=True)
def _clear_session_state():
    st.session_state.clear()
    yield
    st.session_state.clear()


@pytest.fixture
def fake_reruns(monkeypatch):
    calls: list[None] = []
    monkeypatch.setattr(st, "rerun", lambda: calls.append(None))
    return calls


@pytest.fixture
def rendered_html(monkeypatch):
    """Captures what flush_storage_writes hands to components.html."""
    out: list[str] = []
    monkeypatch.setattr(bs.components, "html", lambda body, height=0: out.append(body))
    return out


def _row(ticker: str, action: str, created: str, market: str = "us_sp500") -> dict[str, Any]:
    return {"market_code": market, "ticker": ticker, "action": action, "created_at": created}


# --- pure functions ---


def test_saved_state_keeps_the_latest_action_per_key_and_only_saves() -> None:
    rows = [
        _row("AAPL", "save", "2026-09-01T10:00:00+00:00"),
        _row("MSFT", "save", "2026-09-02T10:00:00+00:00"),
        _row("AAPL", "unsave", "2026-09-03T10:00:00+00:00"),
        _row("SAP.DE", "other", "2026-09-03T11:00:00+00:00", market="de_dax"),
    ]
    assert bs.saved_state(rows) == [["us_sp500", "MSFT", 1788343200]]


def test_saved_state_orders_by_save_time() -> None:
    rows = [
        _row("B", "save", "2026-09-02T10:00:00+00:00"),
        _row("A", "save", "2026-09-01T10:00:00+00:00"),
    ]
    assert [s[1] for s in bs.saved_state(rows)] == ["A", "B"]


def test_interactions_from_state_round_trips_and_drops_malformed_entries() -> None:
    state = [["us_sp500", "MSFT", 1788343200], ["bad"], ["x", 1, 2], "junk"]
    rows = bs.interactions_from_state(state)
    assert rows == [
        {
            "market_code": "us_sp500",
            "ticker": "MSFT",
            "action": "save",
            "created_at": "2026-09-02T10:00:00+00:00",
        }
    ]
    assert bs.saved_state(rows) == [["us_sp500", "MSFT", 1788343200]]


def test_encode_decode_round_trip_including_dots_and_dashes_in_tickers() -> None:
    state = [["de_dax", "SAP.DE", 1], ["uk_ftse100", "BA-B.L", 2], ["jp_nikkei225", "7203.T", 3]]
    chunks = bs.encode_cookies(state)
    assert chunks == ["de_dax:SAP.DE:1|uk_ftse100:BA-B.L:2|jp_nikkei225:7203.T:3"]
    assert bs.decode_cookies({"ss_saved_0": chunks[0]}) == state


def test_decode_cookies_reads_only_its_own_prefix() -> None:
    saved_chunks = bs.encode_cookies([["us_sp500", "AAPL", 1]])
    other_chunks = bs.encode_cookies([["us_sp500", "MSFT", 2]])
    cookies = {"ss_saved_0": saved_chunks[0], "ss_other_0": other_chunks[0]}
    assert bs.decode_cookies(cookies, prefix=bs.COOKIE_PREFIX) == [["us_sp500", "AAPL", 1]]
    assert bs.decode_cookies(cookies, prefix="ss_other_") == [["us_sp500", "MSFT", 2]]


def test_encode_splits_a_long_list_across_numbered_cookies_and_decode_rejoins() -> None:
    state = [["us_sp500", f"T{i:04d}", 1789391499 + i] for i in range(400)]
    chunks = bs.encode_cookies(state)
    assert len(chunks) > 1
    assert all(len(c) <= bs.COOKIE_CHUNK_BYTES for c in chunks)
    cookies = {f"ss_saved_{i}": c for i, c in enumerate(chunks)}
    assert bs.decode_cookies(cookies) == state


def test_empty_state_encodes_to_one_empty_chunk_and_decodes_to_nothing() -> None:
    assert bs.encode_cookies([]) == [""]
    assert bs.decode_cookies({"ss_saved_0": ""}) == []
    assert bs.decode_cookies({}) == []


def test_decode_skips_entries_it_cannot_parse() -> None:
    assert bs.decode_cookies({"ss_saved_0": "garbage|us_sp500:AAPL:12|x:y:z|:t:1"}) == [
        ["us_sp500", "AAPL", 12]
    ]


def test_decode_stops_at_the_first_missing_chunk_number() -> None:
    assert bs.decode_cookies({"ss_saved_0": "a:b:1", "ss_saved_2": "c:d:2"}) == [["a", "b", 1]]


# --- session-state behaviour ---


def test_ensure_loaded_reads_the_cookie_once_and_flags_a_sync(monkeypatch) -> None:
    monkeypatch.setattr(bs, "_request_cookies", lambda: {"ss_saved_0": "us_sp500:MMM:1789392503"})
    first = bs.ensure_interactions_loaded()
    assert [r["ticker"] for r in first] == ["MMM"]
    assert bs.storage_sync_pending() is True
    assert bs.storage_sync_pending() is False
    monkeypatch.setattr(bs, "_request_cookies", lambda: {"ss_saved_0": "us_sp500:XXX:1"})
    assert [r["ticker"] for r in bs.ensure_interactions_loaded()] == ["MMM"]


def test_ensure_loaded_with_no_cookie_gives_an_empty_list_and_no_rerun(
    monkeypatch, fake_reruns
) -> None:
    monkeypatch.setattr(bs, "_request_cookies", lambda: {})
    assert bs.ensure_interactions_loaded() == []
    assert bs.storage_sync_pending() is False
    assert fake_reruns == []


def test_a_save_queues_the_write(monkeypatch) -> None:
    monkeypatch.setattr(bs, "_request_cookies", lambda: {})
    bs.ensure_interactions_loaded()
    bs.append_interaction({"market_code": "us_sp500", "ticker": "MMM"}, "save")
    chunks = st.session_state[bs._WRITE_PENDING_KEY]
    assert len(chunks) == 1 and chunks[0].startswith("us_sp500:MMM:")


def test_unsave_queues_a_write_without_the_key(monkeypatch) -> None:
    monkeypatch.setattr(bs, "_request_cookies", lambda: {"ss_saved_0": "us_sp500:MMM:1"})
    bs.ensure_interactions_loaded()
    bs.append_interaction({"market_code": "us_sp500", "ticker": "MMM"}, "unsave")
    assert st.session_state[bs._WRITE_PENDING_KEY] == [""]


def test_clear_queues_an_empty_write_and_reruns(monkeypatch, fake_reruns) -> None:
    monkeypatch.setattr(bs, "_request_cookies", lambda: {"ss_saved_0": "us_sp500:MMM:1"})
    bs.ensure_interactions_loaded()
    bs.clear_interactions()
    assert bs.get_interactions() == []
    assert st.session_state[bs._WRITE_PENDING_KEY] == [""]
    assert len(fake_reruns) == 1


# --- the rendered scripts ---


def test_flush_renders_the_write_script_once_then_nothing(monkeypatch, rendered_html) -> None:
    monkeypatch.setattr(bs, "_request_cookies", lambda: {"ss_saved_0": "us_sp500:MMM:1"})
    st.session_state[bs._MIGRATION_CHECKED_FLAG] = True
    bs.ensure_interactions_loaded()
    bs.append_interaction({"market_code": "de_dax", "ticker": "SAP.DE"}, "save")
    bs.flush_storage_writes()
    assert len(rendered_html) == 1
    script = rendered_html[0]
    assert "window.parent.document" in script
    assert '"ss_saved_"' in script
    assert "us_sp500:MMM:1|de_dax:SAP.DE:" in script
    assert f"max-age={bs.COOKIE_MAX_AGE_SECONDS}" in script
    bs.flush_storage_writes()
    assert len(rendered_html) == 1


def test_flush_renders_the_migration_only_on_a_cookieless_first_run(
    monkeypatch, rendered_html
) -> None:
    monkeypatch.setattr(bs, "_request_cookies", lambda: {})
    bs.flush_storage_writes()
    assert len(rendered_html) == 1
    assert bs.LEGACY_LOCAL_STORAGE_KEY in rendered_html[0]
    assert "location.reload()" in rendered_html[0]
    bs.flush_storage_writes()
    assert len(rendered_html) == 1


def test_flush_skips_the_migration_when_a_cookie_exists(monkeypatch, rendered_html) -> None:
    monkeypatch.setattr(bs, "_request_cookies", lambda: {"ss_saved_0": "us_sp500:MMM:1"})
    bs.flush_storage_writes()
    assert rendered_html == []


def test_write_script_expires_leftover_chunks_and_has_no_apostrophe_breaking_js() -> None:
    script = bs.write_script(["a:b:1"])
    assert "max-age=0" in script
    assert script.count("<script>") == 1 and script.count("</script>") == 1


# --- crafted cookies must never raise out of the first run ---


@pytest.mark.parametrize(
    "value",
    [
        "us_sp500:AAPL:253402300800",
        "us_sp500:AAPL:" + "9" * 5000,
        "us_sp500:AAPL:99999999999999999999",
        "|||:::",
        "us_sp500:AAPL:-5",
        "ü:é:1",
    ],
)
def test_crafted_cookie_values_load_as_nothing_or_partial_never_raise(monkeypatch, value) -> None:
    monkeypatch.setattr(bs, "_request_cookies", lambda: {"ss_saved_0": value + "|us_sp500:IBM:1"})
    rows = bs.ensure_interactions_loaded()
    assert [r["ticker"] for r in rows if r["market_code"] == "us_sp500" and r["ticker"] == "IBM"]


def test_an_epoch_past_the_platform_range_is_skipped_not_raised() -> None:
    assert bs.interactions_from_state([["a", "b", 10**12], ["a", "c", 1]]) == [
        {"market_code": "a", "ticker": "c", "action": "save", "created_at": "1970-01-01T00:00:01+00:00"}
    ]


def test_write_script_cannot_be_closed_early_by_a_chunk() -> None:
    script = bs.write_script(["a</script>b"])
    assert script.count("</script>") == 1


def test_migration_verifies_the_cookie_before_removing_localstorage_and_chunks() -> None:
    script = bs.migration_script()
    verify = script.index("if(d.cookie.indexOf(prefix+'0=')===-1) return;")
    remove = script.index("localStorage.removeItem")
    reload = script.index("location.reload()")
    assert verify < remove < reload
    assert f"enc.substr(n*{bs.COOKIE_CHUNK_BYTES},{bs.COOKIE_CHUNK_BYTES})" in script
