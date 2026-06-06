"""Browser localStorage for save/skip interactions (v1, no auth)."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

import streamlit as st
import streamlit.components.v1 as components

STORAGE_KEY = "stock_swipe_interactions"
_LOADED_FLAG = "_interactions_storage_loaded"


def _read_script() -> str:
    return f"""
    <script>
    (function() {{
        const value = localStorage.getItem({json.dumps(STORAGE_KEY)}) || "[]";
        window.parent.postMessage({{type: "streamlit:setComponentValue", value: value}}, "*");
    }})();
    </script>
    """


def _write_script(data: list[dict[str, Any]]) -> str:
    payload = json.dumps(data)
    return f"""
    <script>
    (function() {{
        localStorage.setItem({json.dumps(STORAGE_KEY)}, {json.dumps(payload)});
        window.parent.postMessage({{type: "streamlit:setComponentValue", value: "ok"}}, "*");
    }})();
    </script>
    """


def _parse_interactions(raw: str | None) -> list[dict[str, Any]]:
    if not raw:
        return []
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError:
        return []
    return parsed if isinstance(parsed, list) else []


def ensure_interactions_loaded() -> list[dict[str, Any]]:
    """Load interactions from browser localStorage into session state (once per session)."""
    if st.session_state.get(_LOADED_FLAG):
        return list(st.session_state.get("interactions", []))

    result = components.html(_read_script(), height=0, key="load_interactions")
    if result is None:
        st.stop()

    interactions = _parse_interactions(result)
    st.session_state["interactions"] = interactions
    st.session_state[_LOADED_FLAG] = True
    return interactions


def get_interactions() -> list[dict[str, Any]]:
    return list(st.session_state.get("interactions", []))


def _persist_interactions(interactions: list[dict[str, Any]], *, key: str) -> None:
    components.html(_write_script(interactions), height=0, key=key)


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
    _persist_interactions(interactions, key=f"write_interactions_{len(interactions)}")


def clear_interactions() -> None:
    st.session_state["interactions"] = []
    st.session_state[_LOADED_FLAG] = True
    _persist_interactions([], key="clear_interactions")
    st.rerun()
