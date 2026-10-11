"""pre_push_gate: a `git push` in an opted-in project gets the pre-push checklist as context;
other commands and projects without review routing get nothing."""

from __future__ import annotations

import io
import json
import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", ".claude", "hooks"))

import pre_push_gate as gate  # noqa: E402


def _project(tmp_path, opted_in: bool) -> str:
    if opted_in:
        (tmp_path / ".claude").mkdir()
        (tmp_path / ".claude" / "review_routing.json").write_text("{}", encoding="utf-8")
    return str(tmp_path)


def _run(monkeypatch, capsys, command: str, project: str) -> str:
    event = {"tool_name": "Bash", "tool_input": {"command": command}}
    monkeypatch.setattr(sys, "stdin", io.StringIO(json.dumps(event)))
    monkeypatch.setenv("CLAUDE_PROJECT_DIR", project)
    assert gate.main() == 0
    return capsys.readouterr().out


@pytest.mark.parametrize(
    "command",
    ["git push gitlab x:x", "git add a && git push", "git -c k=v push gitlab x:x"],
)
def test_a_push_emits_the_checklist(monkeypatch, capsys, tmp_path, command: str) -> None:
    out = json.loads(_run(monkeypatch, capsys, command, _project(tmp_path, True)))
    assert out["hookSpecificOutput"]["hookEventName"] == "PreToolUse"
    assert out["hookSpecificOutput"]["additionalContext"] == gate.MESSAGE


@pytest.mark.parametrize("command", ["git log", "git status", "echo git push", "ls"])
def test_other_commands_emit_nothing(monkeypatch, capsys, tmp_path, command: str) -> None:
    assert _run(monkeypatch, capsys, command, _project(tmp_path, True)) == ""


def test_a_project_without_review_routing_emits_nothing(monkeypatch, capsys, tmp_path) -> None:
    assert _run(monkeypatch, capsys, "git push gitlab x:x", _project(tmp_path, False)) == ""
