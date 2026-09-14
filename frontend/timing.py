"""Per-run stage timestamps, shown in the page when the URL carries `?timing=1`.

Render's logs are not readable from here and its box behaves unlike a laptop, so the page
carries its own clock: streamlit_app.py marks the moment the entry script starts, app.py
marks each stage of main(), and the caption at the end prints the gaps. Costs nothing when
the flag is absent beyond a few perf_counter calls.
"""

from __future__ import annotations

import time

import streamlit as st

PROCESS_STARTED = time.time()
# Streamlit runs each session's script in its own thread of one process, so the marks live
# in session state, never in a module global two sessions would share.
_MARKS_KEY = "_timing_marks"
_ENTRY_KEY = "_timing_entry_started"


def _marks() -> list[tuple[str, float]]:
    return st.session_state.setdefault(_MARKS_KEY, [])


def entry_started() -> None:
    """Called first thing by the entry script, before it imports the app."""
    st.session_state[_ENTRY_KEY] = time.perf_counter()


def start_run() -> None:
    marks = _marks()
    marks.clear()
    entry = st.session_state.pop(_ENTRY_KEY, None)
    if entry is not None:
        marks.append(("entry script", entry))
    marks.append(("main start", time.perf_counter()))


def mark(name: str) -> None:
    _marks().append((name, time.perf_counter()))


def enabled() -> bool:
    try:
        return bool(st.query_params.get("timing"))
    except Exception:  # noqa: BLE001
        return False


def report_lines() -> list[str]:
    """One line per stage: the gap since the previous mark, in milliseconds."""
    marks = _marks()
    lines = []
    previous = None
    for name, at in marks:
        if previous is not None:
            lines.append(f"{name}: +{(at - previous) * 1000:.0f} ms")
        else:
            lines.append(f"{name}: 0 ms")
        previous = at
    if marks:
        lines.append(f"run total: {(marks[-1][1] - marks[0][1]) * 1000:.0f} ms")
    lines.append(f"process age: {time.time() - PROCESS_STARTED:.0f} s")
    return lines


def render_report() -> None:
    if enabled():
        st.caption(" | ".join(report_lines()))
