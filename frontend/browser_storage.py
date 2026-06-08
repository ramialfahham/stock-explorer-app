"""Browser localStorage for save/skip interactions (v1, no auth)."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import streamlit as st
from streamlit_extras.local_storage_manager import local_storage_manager

STORAGE_ITEM_KEY = "interactions"
ONBOARDING_KEY = "onboarding_dismissed"
_MANAGER_KEY = "stock_swipe_interactions"
_MANAGER_INSTANCE_KEY = "_local_storage_manager_instance"
_MANAGER_RUN_KEY = "_local_storage_manager_run_id"
_STORE_KEY = f"{_MANAGER_KEY}__local_storage_state"
_LOADED_FLAG = "_interactions_storage_loaded"
_ONBOARDING_LOADED_FLAG = "_onboarding_storage_loaded"
_SYNC_PENDING_FLAG = "_storage_sync_pending"
_BOOT_RERUN_FLAG = "_storage_boot_rerun_done"
_DEBUG_MOUNT_COUNT = "_debug_mount_count"


def _debug_log(hypothesis_id: str, location: str, message: str, data: dict[str, Any]) -> None:
    # #region agent log
    try:
        import time

        entry = {
            "sessionId": "669620",
            "runId": "pre-fix",
            "hypothesisId": hypothesis_id,
            "location": location,
            "message": message,
            "data": data,
            "timestamp": int(time.time() * 1000),
        }
        log_path = Path(__file__).resolve().parents[1] / "debug-669620.log"
        with log_path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(entry) + "\n")
    except Exception:
        pass
    # #endregion


def _pending_store() -> dict[str, Any]:
    return st.session_state.setdefault(
        _STORE_KEY,
        {"next_operation_id": 1, "pending_operations": []},
    )


def _queue_storage_write(key: str, value: Any) -> None:
    """Queue a localStorage set without mounting a second component instance."""
    store = _pending_store()
    operation_id = store["next_operation_id"]
    store["next_operation_id"] = operation_id + 1
    store["pending_operations"].append(
        {
            "id": operation_id,
            "type": "set",
            "name": key,
            "value": value,
        }
    )


def _queue_interactions_write(interactions: list[dict[str, Any]]) -> None:
    _queue_storage_write(STORAGE_ITEM_KEY, interactions)


def _current_run_id() -> str | None:
    try:
        from streamlit.runtime.scriptrunner import get_script_run_ctx

        ctx = get_script_run_ctx()
        if ctx is None:
            return None
        return str(ctx.script_run_id)
    except Exception:
        return None


def _mount_manager():
    """Mount localStorage component once per run (flushes pending writes + reads snapshot)."""
    import inspect

    mount_count = st.session_state.get(_DEBUG_MOUNT_COUNT, 0) + 1
    st.session_state[_DEBUG_MOUNT_COUNT] = mount_count
    caller = inspect.stack()[1]
    run_id = _current_run_id()
    cached_manager = st.session_state.get(_MANAGER_INSTANCE_KEY)
    cached_run = st.session_state.get(_MANAGER_RUN_KEY)
    reused = cached_manager is not None and cached_run == run_id and run_id is not None
    _debug_log(
        "H1",
        "browser_storage.py:_mount_manager",
        "local_storage_manager mount attempt",
        {
            "runId": "post-fix",
            "mount_count": mount_count,
            "reused_cached": reused,
            "caller_function": caller.function,
            "caller_filename": caller.filename,
            "caller_lineno": caller.lineno,
        },
    )
    if reused:
        return cached_manager

    manager = local_storage_manager(key=_MANAGER_KEY)
    st.session_state[_MANAGER_INSTANCE_KEY] = manager
    st.session_state[_MANAGER_RUN_KEY] = run_id
    return manager


def _parse_interactions(raw: Any) -> list[dict[str, Any]]:
    if raw is None:
        return []
    if isinstance(raw, list):
        return raw
    if isinstance(raw, str):
        try:
            parsed = json.loads(raw)
        except json.JSONDecodeError:
            return []
        return parsed if isinstance(parsed, list) else []
    return []


def _parse_bool(raw: Any) -> bool:
    if raw is True:
        return True
    if isinstance(raw, str):
        return raw.lower() in {"true", "1", "yes"}
    if isinstance(raw, (int, float)):
        return bool(raw)
    return False


def _load_onboarding_from_manager(manager) -> None:
    if st.session_state.get(_ONBOARDING_LOADED_FLAG):
        return
    stored = manager.get(ONBOARDING_KEY, False)
    st.session_state["onboarding_dismissed"] = _parse_bool(stored)
    st.session_state[_ONBOARDING_LOADED_FLAG] = True


def ensure_interactions_loaded() -> list[dict[str, Any]]:
    """Load interactions from browser localStorage into session state."""
    import inspect

    caller = inspect.stack()[1]
    _debug_log(
        "H1",
        "browser_storage.py:ensure_interactions_loaded",
        "ensure_interactions_loaded called",
        {
            "runId": "post-fix",
            "caller_function": caller.function,
            "caller_filename": caller.filename,
            "caller_lineno": caller.lineno,
            "loaded_flag": bool(st.session_state.get(_LOADED_FLAG)),
        },
    )
    if "interactions" not in st.session_state:
        st.session_state["interactions"] = []

    manager = _mount_manager()

    if st.session_state.get(_LOADED_FLAG):
        if not st.session_state.get(_ONBOARDING_LOADED_FLAG) and manager.ready():
            _load_onboarding_from_manager(manager)
        return list(st.session_state.get("interactions", []))

    if not manager.ready():
        if not st.session_state.get(_BOOT_RERUN_FLAG):
            st.session_state[_BOOT_RERUN_FLAG] = True
            st.rerun()
        return list(st.session_state["interactions"])

    stored = manager.get(STORAGE_ITEM_KEY, [])
    interactions = _parse_interactions(stored)
    st.session_state["interactions"] = interactions
    st.session_state[_LOADED_FLAG] = True
    st.session_state[_BOOT_RERUN_FLAG] = False
    _load_onboarding_from_manager(manager)
    if interactions:
        st.session_state[_SYNC_PENDING_FLAG] = True
    return interactions


def storage_sync_pending() -> bool:
    return bool(st.session_state.pop(_SYNC_PENDING_FLAG, False))


def get_interactions() -> list[dict[str, Any]]:
    return list(st.session_state.get("interactions", []))


def append_interaction(card: dict[str, Any], action: str) -> None:
    row = {
        "market_code": card["market_code"],
        "ticker": card["ticker"],
        "action": action,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    interactions = get_interactions()
    interactions.append(row)
    st.session_state["interactions"] = interactions
    st.session_state[_LOADED_FLAG] = True
    _queue_interactions_write(interactions)


def clear_interactions() -> None:
    st.session_state["interactions"] = []
    st.session_state[_LOADED_FLAG] = True
    _queue_interactions_write([])
    st.rerun()


def onboarding_ready() -> bool:
    return bool(st.session_state.get(_ONBOARDING_LOADED_FLAG))


def is_onboarding_dismissed() -> bool:
    return bool(st.session_state.get("onboarding_dismissed", False))


def dismiss_onboarding() -> None:
    st.session_state["onboarding_dismissed"] = True
    st.session_state[_ONBOARDING_LOADED_FLAG] = True
    _queue_storage_write(ONBOARDING_KEY, True)
