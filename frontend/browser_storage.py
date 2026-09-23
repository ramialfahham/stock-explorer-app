"""Browser-side persistence for saved interactions (v1, no auth): cookies.

Cookies need no component: Streamlit hands the request's cookies to the first script run
(st.context.cookies), so the saved list is known before the first element is drawn, and a
write is a few lines of JavaScript rendered only in the run that changes something.

What persists is the current state, not the event log: the saved (market_code, ticker) keys
with the epoch second of their save, under one cookie namespace (`COOKIE_PREFIX`). One
cookie holds about 130 entries; beyond that a list's value is split across its own numbered
cookies.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

import streamlit as st
import streamlit.components.v1 as components

COOKIE_PREFIX = "ss_saved_"
COOKIE_MAX_AGE_SECONDS = 365 * 24 * 3600
# Browsers refuse a cookie whose name plus value passes 4096 bytes; this budget leaves
# room for the name and attributes ("market:ticker:epoch" entries joined by "|").
COOKIE_CHUNK_BYTES = 3800
_ENTRY_SEP = "|"
_FIELD_SEP = ":"
# An epoch second fits in ten digits until the year 2286; anything longer is not ours.
_MAX_EPOCH_DIGITS = 10
# streamlit_extras namespaced its localStorage keys as "st_extras_" + sanitised pathname +
# "_" + item key; at the app root the pathname "/" sanitises to "_".
LEGACY_LOCAL_STORAGE_KEY = "st_extras___interactions"
_LOADED_FLAG = "_interactions_storage_loaded"
_SYNC_PENDING_FLAG = "_storage_sync_pending"
_WRITE_PENDING_KEY = "_cookie_write_pending"
_MIGRATION_CHECKED_FLAG = "_cookie_migration_checked"


def _iso(epoch: int) -> str | None:
    try:
        return datetime.fromtimestamp(epoch, tz=timezone.utc).isoformat()
    except (OverflowError, OSError, ValueError):
        return None


def _state_for_actions(
    interactions: list[dict[str, Any]], *, add_action: str, remove_action: str
) -> list[list[Any]]:
    """The persisted form: [market_code, ticker, epoch_second] per currently-active key for
    one add/remove action pair, in action order. Parameterized by action pair, not hardcoded
    to save/unsave, mirroring `explore_filters._latest_action_keys`'s tie-break logic (no
    shared module in frontend/ to import it from)."""
    latest: dict[tuple[str, str], tuple[str, str]] = {}
    for row in interactions:
        action = row.get("action")
        if action not in (add_action, remove_action):
            continue
        key = (row.get("market_code"), row.get("ticker"))
        created = row.get("created_at") or ""
        if key not in latest or created >= latest[key][0]:
            latest[key] = (created, action)
    out = []
    for (market, ticker), (created, action) in sorted(latest.items(), key=lambda kv: kv[1][0]):
        if action != add_action:
            continue
        try:
            epoch = int(datetime.fromisoformat(created).timestamp())
        except ValueError:
            epoch = 0
        out.append([market, ticker, epoch])
    return out


def saved_state(interactions: list[dict[str, Any]]) -> list[list[Any]]:
    """The persisted form for Saved: [market_code, ticker, epoch_second] per currently-saved
    key, in save order. The latest save/unsave per key wins, as saved_keys_with_order
    decides."""
    return _state_for_actions(interactions, add_action="save", remove_action="unsave")


def interactions_from_state(state: list[list[Any]]) -> list[dict[str, Any]]:
    """The in-memory form the rest of the app reads: one "save" row per persisted key. The
    Saved cookie's entries carry no action of their own (just market/ticker/epoch), so this
    supplies it."""
    rows = []
    for item in state:
        if not (isinstance(item, list) and len(item) == 3):
            continue
        market, ticker, epoch = item
        if not (isinstance(market, str) and isinstance(ticker, str) and isinstance(epoch, int)):
            continue
        created = _iso(epoch)
        if created is None:
            continue
        rows.append({"market_code": market, "ticker": ticker, "action": "save", "created_at": created})
    return rows


def encode_cookies(state: list[list[Any]]) -> list[str]:
    """One string of "market:ticker:epoch" entries, split into chunks that each fit one
    cookie. An empty state encodes to one empty chunk so a clear still overwrites the first
    cookie. Chunks may cut an entry in two; decode joins them before splitting."""
    if not state:
        return [""]
    encoded = _ENTRY_SEP.join(f"{m}{_FIELD_SEP}{t}{_FIELD_SEP}{e}" for m, t, e in state)
    return [encoded[i : i + COOKIE_CHUNK_BYTES] for i in range(0, len(encoded), COOKIE_CHUNK_BYTES)]


def decode_cookies(cookies: dict[str, str], *, prefix: str = COOKIE_PREFIX) -> list[list[Any]]:
    """Reassemble the numbered cookies under `prefix`; an entry that does not parse is
    dropped. `prefix` defaults to the Saved cookie, the only one this app writes now."""
    parts = []
    index = 0
    while f"{prefix}{index}" in cookies:
        parts.append(cookies[f"{prefix}{index}"])
        index += 1
    joined = "".join(parts)
    if not joined:
        return []
    state: list[list[Any]] = []
    for entry in joined.split(_ENTRY_SEP):
        fields = entry.split(_FIELD_SEP)
        if len(fields) != 3 or not fields[0] or not fields[1]:
            continue
        if not fields[2].isdigit() or len(fields[2]) > _MAX_EPOCH_DIGITS:
            continue
        state.append([fields[0], fields[1], int(fields[2])])
    return state


def _request_cookies() -> dict[str, str]:
    try:
        return dict(st.context.cookies)
    except Exception:  # noqa: BLE001
        return {}


def ensure_interactions_loaded() -> list[dict[str, Any]]:
    """Read the saved list from the request's cookies into session state, once per session.
    No component, no rerun: the cookies arrive with the websocket handshake."""
    if "interactions" not in st.session_state:
        st.session_state["interactions"] = []
    if st.session_state.get(_LOADED_FLAG):
        return list(st.session_state["interactions"])
    cookies = _request_cookies()
    interactions = interactions_from_state(decode_cookies(cookies, prefix=COOKIE_PREFIX))
    st.session_state["interactions"] = interactions
    st.session_state[_LOADED_FLAG] = True
    if interactions:
        st.session_state[_SYNC_PENDING_FLAG] = True
    return interactions


def storage_sync_pending() -> bool:
    return bool(st.session_state.pop(_SYNC_PENDING_FLAG, False))


def get_interactions() -> list[dict[str, Any]]:
    return list(st.session_state.get("interactions", []))


def _queue_write() -> None:
    st.session_state[_WRITE_PENDING_KEY] = encode_cookies(saved_state(get_interactions()))


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
    _queue_write()


def clear_interactions() -> None:
    """The Saved tab's "Clear saved" action -- save/unsave is the only interaction pair,
    so this clears everything, not a filtered subset."""
    st.session_state["interactions"] = []
    st.session_state[_LOADED_FLAG] = True
    _queue_write()
    st.rerun()


def _js_literal(value: object) -> str:
    """JSON as a script-safe literal: a "</" inside a string would otherwise end the
    <script> element early."""
    return json.dumps(value).replace("</", "<" + chr(92) + "/")


def write_script(chunks: list[str], *, prefix: str = COOKIE_PREFIX) -> str:
    """JavaScript that sets the numbered cookies under `prefix` to `chunks` and expires any
    leftover chunk from a previously longer list. Runs inside Streamlit's component iframe;
    its srcdoc origin is the page's own, so window.parent.document is reachable."""
    attrs = f"path=/; max-age={COOKIE_MAX_AGE_SECONDS}; samesite=lax"
    return (
        "<script>(function(){"
        "var d=window.parent.document;"
        "var secure=window.parent.location.protocol==='https:'?'; secure':'';"
        f"var chunks={_js_literal(chunks)};"
        f"var prefix={json.dumps(prefix)};"
        "for(var i=0;i<chunks.length;i++){"
        f"d.cookie=prefix+i+'='+chunks[i]+'; {attrs}'+secure;}}"
        "for(var j=chunks.length;j<chunks.length+20;j++){"
        "if(d.cookie.indexOf(prefix+j+'=')===-1){break;}"
        "d.cookie=prefix+j+'=; path=/; max-age=0'+secure;}"
        "})();</script>"
    )


def migration_script() -> str:
    """One-time move of a saved list left in localStorage by the prior storage mechanism.
    Runs only when no cookie exists. On finding saves it writes the cookies, then removes
    the localStorage copy and reloads once, only if the browser accepted the first cookie
    chunk; otherwise the localStorage list is left in place and there is no reload."""
    key = json.dumps(LEGACY_LOCAL_STORAGE_KEY)
    prefix = json.dumps(COOKIE_PREFIX)
    return (
        "<script>(function(){"
        "var d=window.parent.document; var w=window.parent;"
        f"var prefix={prefix};"
        "if(d.cookie.indexOf(prefix+'0=')!==-1) return;"
        f"var raw=null; try{{raw=w.localStorage.getItem({key});}}catch(e){{return;}}"
        "if(!raw) return;"
        "var rows; try{rows=JSON.parse(raw);}catch(e){return;}"
        "if(!Array.isArray(rows)) return;"
        "var latest={};"
        "for(var i=0;i<rows.length;i++){var r=rows[i];"
        "if(!r||(r.action!=='save'&&r.action!=='unsave')) continue;"
        "var k=r.market_code+'|'+r.ticker; var c=r.created_at||'';"
        "if(!(k in latest)||c>=latest[k][0]) latest[k]=[c,r.action,r.market_code,r.ticker];}"
        "var keys=Object.keys(latest).sort(function(a,b){return latest[a][0]<latest[b][0]?-1:1});"
        "var state=[];"
        "for(var j=0;j<keys.length;j++){var e=latest[keys[j]]; if(e[1]!=='save') continue;"
        "var t=Math.floor(Date.parse(e[0])/1000)||0; state.push([e[2],e[3],t]);}"
        "if(!state.length) return;"
        "var enc=state.map(function(s){return s[0]+':'+s[1]+':'+s[2]}).join('|');"
        "var secure=w.location.protocol==='https:'?'; secure':'';"
        f"var attrs='; path=/; max-age={COOKIE_MAX_AGE_SECONDS}; samesite=lax'+secure;"
        f"for(var n=0;n*{COOKIE_CHUNK_BYTES}<enc.length;n++){{"
        f"d.cookie=prefix+n+'='+enc.substr(n*{COOKIE_CHUNK_BYTES},{COOKIE_CHUNK_BYTES})+attrs;}}"
        "if(d.cookie.indexOf(prefix+'0=')===-1) return;"
        f"try{{w.localStorage.removeItem({key});}}catch(e){{}}"
        "w.location.reload();"
        "})();</script>"
    )


def flush_storage_writes() -> None:
    """Render the cookie-writing script when a save changed something this run, and the
    one-time localStorage migration on a session's first run without a saved-list cookie.
    Called once per run from app.main, after everything else, so it never delays a paint."""
    chunks = st.session_state.pop(_WRITE_PENDING_KEY, None)
    if chunks is not None:
        components.html(write_script(chunks, prefix=COOKIE_PREFIX), height=0)
    if not st.session_state.get(_MIGRATION_CHECKED_FLAG):
        st.session_state[_MIGRATION_CHECKED_FLAG] = True
        if not decode_cookies(_request_cookies()):
            components.html(migration_script(), height=0)
