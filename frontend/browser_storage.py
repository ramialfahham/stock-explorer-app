"""Browser localStorage for save/skip interactions (v1, no auth)."""

from __future__ import annotations

import json
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import streamlit as st
from streamlit_extras.local_storage_manager import local_storage_manager

STORAGE_ITEM_KEY = "interactions"
_MANAGER_KEY = "stock_swipe_interactions"
_STORE_KEY = f"{_MANAGER_KEY}__local_storage_state"
_LOADED_FLAG = "_interactions_storage_loaded"
_SYNC_PENDING_FLAG = "_storage_sync_pending"
_BOOT_RERUN_FLAG = "_storage_boot_rerun_done"
_DEBUG_LOG = Path(__file__).resolve().parents[1] / "debug-3dd384.log"


def _debug_log(hypothesis_id: str, message: str, data: dict[str, Any]) -> None:
    # #region agent log
    payload = {
        "sessionId": "3dd384",
        "runId": "flush-fix",
        "hypothesisId": hypothesis_id,
        "location": "browser_storage.py",
        "message": message,
        "data": data,
        "timestamp": int(time.time() * 1000),
    }
    with _DEBUG_LOG.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload) + "\n")
    # #endregion


def _pending_store() -> dict[str, Any]:
    return st.session_state.setdefault(
        _STORE_KEY,
        {"next_operation_id": 1, "pending_operations": []},
    )


def _queue_interactions_write(interactions: list[dict[str, Any]]) -> None:
    """Queue a localStorage set without mounting a second component instance."""
    store = _pending_store()
    operation_id = store["next_operation_id"]
    store["next_operation_id"] = operation_id + 1
    store["pending_operations"].append(
        {
            "id": operation_id,
            "type": "set",
            "name": STORAGE_ITEM_KEY,
            "value": interactions,
        }
    )
    _debug_log(
        "A",
        "queued interactions write",
        {
            "operation_id": operation_id,
            "count": len(interactions),
            "saved": sum(1 for i in interactions if i.get("action") == "save"),
            "pending_count": len(store["pending_operations"]),
        },
    )


def _mount_manager():
    """Mount localStorage component once per run (flushes pending writes + reads snapshot)."""
    manager = local_storage_manager(key=_MANAGER_KEY)
    store = _pending_store()
    _debug_log(
        "C",
        "mounted localStorage manager",
        {
            "ready": manager.ready(),
            "pending_count": len(store["pending_operations"]),
            "loaded_flag": bool(st.session_state.get(_LOADED_FLAG)),
        },
    )
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


def ensure_interactions_loaded() -> list[dict[str, Any]]:
    """Load interactions from browser localStorage into session state."""
    if "interactions" not in st.session_state:
        st.session_state["interactions"] = []

    manager = _mount_manager()

    if st.session_state.get(_LOADED_FLAG):
        interactions = list(st.session_state.get("interactions", []))
        _debug_log("E", "session interactions (manager mounted for flush)", {"count": len(interactions)})
        return interactions

    ready = manager.ready()
    _debug_log("D", "manager ready check", {"ready": ready})

    if not ready:
        if not st.session_state.get(_BOOT_RERUN_FLAG):
            st.session_state[_BOOT_RERUN_FLAG] = True
            _debug_log("B", "boot rerun waiting for localStorage sync", {})
            st.rerun()
        _debug_log("B", "manager still not ready after boot rerun", {})
        return list(st.session_state["interactions"])

    stored = manager.get(STORAGE_ITEM_KEY, [])
    interactions = _parse_interactions(stored)
    st.session_state["interactions"] = interactions
    st.session_state[_LOADED_FLAG] = True
    st.session_state[_BOOT_RERUN_FLAG] = False
    if interactions:
        st.session_state[_SYNC_PENDING_FLAG] = True
    _debug_log(
        "D",
        "loaded interactions from localStorage",
        {"count": len(interactions), "saved": sum(1 for i in interactions if i.get("action") == "save")},
    )
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
