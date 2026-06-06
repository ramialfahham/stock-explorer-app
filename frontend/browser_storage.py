"""Browser localStorage for save/skip interactions (v1, no auth)."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import streamlit as st
import streamlit.components.v1 as components

STORAGE_KEY = "stock_swipe_interactions"
_LOADED_FLAG = "_interactions_storage_loaded"
_COMPONENT_DIR = Path(__file__).resolve().parent / "components" / "local_storage"

_local_storage = components.declare_component(
    "stock_swipe_local_storage",
    path=str(_COMPONENT_DIR),
)


def _parse_interactions(raw: str | None) -> list[dict[str, Any]]:
    if not raw:
        return []
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError:
        return []
    return parsed if isinstance(parsed, list) else []


def _read_from_browser() -> str | None:
    result = _local_storage(
        mode="read",
        storage_key=STORAGE_KEY,
        default_value="[]",
        key="load_interactions",
    )
    if result is None:
        return None
    if isinstance(result, str):
        return result
    return json.dumps(result)


def _write_to_browser(interactions: list[dict[str, Any]], *, component_key: str) -> None:
    _local_storage(
        mode="write",
        storage_key=STORAGE_KEY,
        value=json.dumps(interactions),
        key=component_key,
    )


def ensure_interactions_loaded() -> list[dict[str, Any]]:
    """Load interactions from browser localStorage into session state (once per session)."""
    if st.session_state.get(_LOADED_FLAG):
        return list(st.session_state.get("interactions", []))

    raw = _read_from_browser()
    if raw is None:
        st.stop()

    interactions = _parse_interactions(raw)
    st.session_state["interactions"] = interactions
    st.session_state[_LOADED_FLAG] = True
    return interactions


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
    _write_to_browser(interactions, component_key=f"write_interactions_{len(interactions)}")


def clear_interactions() -> None:
    st.session_state["interactions"] = []
    st.session_state[_LOADED_FLAG] = True
    _write_to_browser([], component_key="clear_interactions")
    st.rerun()
