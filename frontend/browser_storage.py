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
_LOADED_FLAG = "_interactions_storage_loaded"
_SYNC_PENDING_FLAG = "_storage_sync_pending"
_DEBUG_LOG = Path(__file__).resolve().parents[1] / "debug-3dd384.log"


def _debug_log(hypothesis_id: str, message: str, data: dict[str, Any]) -> None:
    # #region agent log
    payload = {
        "sessionId": "3dd384",
        "runId": "cloud-fix",
        "hypothesisId": hypothesis_id,
        "location": "browser_storage.py",
        "message": message,
        "data": data,
        "timestamp": int(time.time() * 1000),
    }
    with _DEBUG_LOG.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload) + "\n")
    # #endregion


def _legacy_component_dir() -> Path:
    return Path(__file__).resolve().parent / "components" / "local_storage"


def _manager():
    return local_storage_manager(key=_MANAGER_KEY)


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
    legacy_dir = _legacy_component_dir()
    _debug_log(
        "A",
        "storage backend init",
        {
            "legacy_component_dir_exists": legacy_dir.is_dir(),
            "legacy_index_exists": (legacy_dir / "index.html").is_file(),
            "backend": "streamlit_extras.local_storage_manager",
        },
    )

    if st.session_state.get(_LOADED_FLAG):
        interactions = list(st.session_state.get("interactions", []))
        _debug_log("E", "interactions already loaded", {"count": len(interactions)})
        return interactions

    if "interactions" not in st.session_state:
        st.session_state["interactions"] = []

    manager = _manager()
    ready = manager.ready()
    _debug_log("D", "localStorage manager ready check", {"ready": ready})

    if not ready:
        return list(st.session_state["interactions"])

    stored = manager.get(STORAGE_ITEM_KEY, [])
    interactions = _parse_interactions(stored)
    st.session_state["interactions"] = interactions
    st.session_state[_LOADED_FLAG] = True
    st.session_state[_SYNC_PENDING_FLAG] = True
    _debug_log("D", "loaded interactions from localStorage", {"count": len(interactions)})
    return interactions


def storage_sync_pending() -> bool:
    return bool(st.session_state.pop(_SYNC_PENDING_FLAG, False))


def get_interactions() -> list[dict[str, Any]]:
    return list(st.session_state.get("interactions", []))


def _persist_interactions(interactions: list[dict[str, Any]]) -> None:
    manager = _manager()
    if not manager.ready():
        _debug_log("D", "skip persist; manager not ready", {"count": len(interactions)})
        return
    manager[STORAGE_ITEM_KEY] = interactions
    _debug_log("D", "persisted interactions", {"count": len(interactions)})


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
    _persist_interactions(interactions)


def clear_interactions() -> None:
    st.session_state["interactions"] = []
    st.session_state[_LOADED_FLAG] = True
    manager = _manager()
    if manager.ready():
        manager[STORAGE_ITEM_KEY] = []
    st.rerun()
