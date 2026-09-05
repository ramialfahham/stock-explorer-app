"""Tests for browser_storage.py's session-state bookkeeping around localStorage.

`local_storage_manager` (streamlit_extras) is a real custom component -- it only responds
inside a live browser session, so it's faked here rather than exercised for real (matching
this repo's own pure/render-split testing convention, see test_app.py's discover-pagination
comment). `st.session_state` itself works standalone outside `streamlit run` (confirmed
directly: it's a real dict-like object, just with a "bare mode" warning), so it's used as-is
rather than mocked.
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


class _FakeManager:
    """Stand-in for local_storage_manager's return value."""

    def __init__(self, *, ready: bool = True, stored: Any = None) -> None:
        self._ready = ready
        self._stored = stored

    def ready(self) -> bool:
        return self._ready

    def get(self, key: str, default: Any = None) -> Any:
        return self._stored if self._stored is not None else default


@pytest.fixture
def fake_reruns(monkeypatch):
    calls: list[None] = []
    monkeypatch.setattr(st, "rerun", lambda: calls.append(None))
    return calls


def _mock_manager(monkeypatch, manager: _FakeManager) -> None:
    monkeypatch.setattr(bs, "_mount_manager", lambda: manager)


# --- _parse_interactions: pure function, no session_state or component involved ---


def test_parse_interactions_none_returns_empty_list() -> None:
    assert bs._parse_interactions(None) == []


def test_parse_interactions_list_passed_through() -> None:
    rows = [{"ticker": "AAPL", "action": "save"}]
    assert bs._parse_interactions(rows) == rows


def test_parse_interactions_valid_json_list_string_is_parsed() -> None:
    raw = '[{"ticker": "AAPL", "action": "save"}]'
    assert bs._parse_interactions(raw) == [{"ticker": "AAPL", "action": "save"}]


def test_parse_interactions_json_string_encoding_a_non_list_returns_empty() -> None:
    """A stored value that's valid JSON but not a list (e.g. localStorage holding a stray
    object) must not crash the read path -- it's not this app's own write shape."""
    assert bs._parse_interactions('{"not": "a list"}') == []


def test_parse_interactions_invalid_json_string_returns_empty() -> None:
    assert bs._parse_interactions("not json at all") == []


def test_parse_interactions_unexpected_type_returns_empty() -> None:
    assert bs._parse_interactions(42) == []


# --- pending-write queue ---


def test_pending_store_initializes_on_first_access() -> None:
    store = bs._pending_store()
    assert store == {"next_operation_id": 1, "pending_operations": []}


def test_queue_storage_write_appends_operation_and_increments_id() -> None:
    bs._queue_storage_write("interactions", [{"ticker": "AAPL"}])
    bs._queue_storage_write("interactions", [{"ticker": "AAPL"}, {"ticker": "MSFT"}])
    store = bs._pending_store()
    assert store["next_operation_id"] == 3
    assert [op["id"] for op in store["pending_operations"]] == [1, 2]
    assert store["pending_operations"][-1] == {
        "id": 2,
        "type": "set",
        "name": "interactions",
        "value": [{"ticker": "AAPL"}, {"ticker": "MSFT"}],
    }


def test_queue_interactions_write_uses_the_interactions_storage_key() -> None:
    bs._queue_interactions_write([{"ticker": "AAPL"}])
    op = bs._pending_store()["pending_operations"][0]
    assert op["name"] == bs.STORAGE_ITEM_KEY


# --- read helpers ---


def test_get_interactions_is_empty_when_unset() -> None:
    assert bs.get_interactions() == []


def test_get_interactions_returns_a_copy_not_the_live_list() -> None:
    st.session_state["interactions"] = [{"ticker": "AAPL"}]
    result = bs.get_interactions()
    result.append({"ticker": "MSFT"})
    assert st.session_state["interactions"] == [{"ticker": "AAPL"}]


def test_storage_sync_pending_defaults_false_and_clears_after_one_read() -> None:
    assert bs.storage_sync_pending() is False
    st.session_state[bs._SYNC_PENDING_FLAG] = True
    assert bs.storage_sync_pending() is True
    assert bs.storage_sync_pending() is False


# --- append / clear ---


def test_append_interaction_builds_the_expected_row_shape() -> None:
    card = {"market_code": "us_sp500", "ticker": "AAPL"}
    bs.append_interaction(card, "save")
    [row] = bs.get_interactions()
    assert row["market_code"] == "us_sp500"
    assert row["ticker"] == "AAPL"
    assert row["action"] == "save"
    assert "created_at" in row


def test_append_interaction_queues_a_write_and_sets_the_loaded_flag() -> None:
    bs.append_interaction({"market_code": "us_sp500", "ticker": "AAPL"}, "skip")
    assert st.session_state[bs._LOADED_FLAG] is True
    queued = bs._pending_store()["pending_operations"][-1]
    assert queued["name"] == bs.STORAGE_ITEM_KEY
    assert queued["value"] == bs.get_interactions()


def test_clear_interactions_empties_state_queues_an_empty_write_and_reruns(fake_reruns) -> None:
    st.session_state["interactions"] = [{"ticker": "AAPL"}]
    bs.clear_interactions()
    assert st.session_state["interactions"] == []
    assert st.session_state[bs._LOADED_FLAG] is True
    queued = bs._pending_store()["pending_operations"][-1]
    assert queued["value"] == []
    assert len(fake_reruns) == 1


# --- ensure_interactions_loaded: the boot sequence ---


def test_ensure_interactions_loaded_not_ready_triggers_exactly_one_rerun(
    monkeypatch, fake_reruns
) -> None:
    """The manager needs a run before its JS side reports ready -- one rerun buys that,
    but the boot flag must stop a second one from firing forever if it's still not ready."""
    _mock_manager(monkeypatch, _FakeManager(ready=False))
    result = bs.ensure_interactions_loaded()
    assert result == []
    assert len(fake_reruns) == 1
    assert st.session_state[bs._BOOT_RERUN_FLAG] is True


def test_ensure_interactions_loaded_does_not_rerun_again_once_boot_flag_is_set(
    monkeypatch, fake_reruns
) -> None:
    st.session_state[bs._BOOT_RERUN_FLAG] = True
    _mock_manager(monkeypatch, _FakeManager(ready=False))
    result = bs.ensure_interactions_loaded()
    assert result == []
    assert len(fake_reruns) == 0


def test_ensure_interactions_loaded_reads_and_parses_once_ready(monkeypatch) -> None:
    stored = [{"ticker": "AAPL", "action": "save"}]
    _mock_manager(monkeypatch, _FakeManager(ready=True, stored=stored))
    result = bs.ensure_interactions_loaded()
    assert result == stored
    assert st.session_state["interactions"] == stored
    assert st.session_state[bs._LOADED_FLAG] is True
    assert st.session_state[bs._BOOT_RERUN_FLAG] is False


def test_ensure_interactions_loaded_sets_sync_pending_only_when_non_empty(monkeypatch) -> None:
    _mock_manager(monkeypatch, _FakeManager(ready=True, stored=[{"ticker": "AAPL"}]))
    bs.ensure_interactions_loaded()
    assert st.session_state[bs._SYNC_PENDING_FLAG] is True


def test_ensure_interactions_loaded_leaves_sync_pending_unset_when_empty(monkeypatch) -> None:
    _mock_manager(monkeypatch, _FakeManager(ready=True, stored=[]))
    bs.ensure_interactions_loaded()
    assert bs._SYNC_PENDING_FLAG not in st.session_state


def test_ensure_interactions_loaded_returns_cached_value_without_touching_manager_again(
    monkeypatch,
) -> None:
    """Once loaded, later calls in the same session must not re-read the component --
    proven by making a second read return something different and confirming it's ignored."""
    st.session_state["interactions"] = [{"ticker": "AAPL"}]
    st.session_state[bs._LOADED_FLAG] = True
    _mock_manager(monkeypatch, _FakeManager(ready=True, stored=[{"ticker": "MSFT"}]))
    result = bs.ensure_interactions_loaded()
    assert result == [{"ticker": "AAPL"}]


# --- _mount_manager: one instance per script run ---


def test_mount_manager_caches_the_same_instance_within_one_run(monkeypatch) -> None:
    monkeypatch.setattr(bs, "_current_run_id", lambda: "run-1")
    calls: list[None] = []

    def fake_local_storage_manager(key: str):
        calls.append(None)
        return object()

    monkeypatch.setattr(bs, "local_storage_manager", fake_local_storage_manager)
    first = bs._mount_manager()
    second = bs._mount_manager()
    assert first is second
    assert len(calls) == 1


def test_mount_manager_remounts_for_a_new_run_id(monkeypatch) -> None:
    run_id = ["run-1"]
    monkeypatch.setattr(bs, "_current_run_id", lambda: run_id[0])
    instances: list[object] = []

    def fake_local_storage_manager(key: str):
        instance = object()
        instances.append(instance)
        return instance

    monkeypatch.setattr(bs, "local_storage_manager", fake_local_storage_manager)
    first = bs._mount_manager()
    run_id[0] = "run-2"
    second = bs._mount_manager()
    assert first is not second
    assert len(instances) == 2
