"""timing.py: the in-page stage clock, silent without ?timing=1."""

from __future__ import annotations

import pytest
import streamlit as st

import timing


@pytest.fixture(autouse=True)
def _clear_session_state():
    st.session_state.clear()
    yield
    st.session_state.clear()


def test_marks_live_in_session_state_not_a_module_global() -> None:
    timing.start_run()
    timing.mark("css")
    assert len(st.session_state[timing._MARKS_KEY]) == 2
    st.session_state.clear()
    assert timing.report_lines()[0].startswith("process age")


def test_entry_mark_is_consumed_by_the_run_that_follows_it(monkeypatch) -> None:
    ticks = iter([1.0, 2.0, 5.0])
    monkeypatch.setattr(timing.time, "perf_counter", lambda: next(ticks))
    timing.entry_started()
    timing.start_run()
    assert timing.report_lines()[:2] == ["entry script: 0 ms", "main start: +1000 ms"]
    timing.start_run()
    assert timing.report_lines()[0] == "main start: 0 ms"


def test_report_lists_gaps_in_order_and_a_total(monkeypatch) -> None:
    ticks = iter([10.0, 10.5, 10.6, 11.0])
    monkeypatch.setattr(timing.time, "perf_counter", lambda: next(ticks))
    timing.entry_started()
    timing.start_run()
    timing.mark("css")
    timing.mark("page")
    lines = timing.report_lines()
    assert lines[:4] == ["entry script: 0 ms", "main start: +500 ms", "css: +100 ms", "page: +400 ms"]
    assert lines[4] == "run total: 1000 ms"
    assert lines[5].startswith("process age: ")


def test_report_renders_only_with_the_flag(monkeypatch) -> None:
    captions: list[str] = []
    monkeypatch.setattr(timing.st, "caption", lambda text: captions.append(text))
    monkeypatch.setattr(timing, "enabled", lambda: False)
    timing.render_report()
    assert captions == []
    monkeypatch.setattr(timing, "enabled", lambda: True)
    timing.start_run()
    timing.render_report()
    assert len(captions) == 1 and "run total" in captions[0]
