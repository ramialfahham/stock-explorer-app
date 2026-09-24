"""Tests for handover_in: the SessionStart hook that injects .claude/active_work.md."""

import contextlib
import io
import json
import os
import sys
import tempfile

import yaml

_REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))
sys.path.insert(0, os.path.join(_REPO_ROOT, ".claude", "hooks"))

import handover_in  # noqa: E402


def test_cap_covers_the_active_work_budget():
    with open(os.path.join(_REPO_ROOT, "docs", "context_budget.yml"), encoding="utf-8") as f:
        budget = yaml.safe_load(f)["budgets"][".claude/active_work.md"]
    assert handover_in.MAX_BYTES >= budget


def test_a_handover_at_the_cap_is_injected_whole():
    with tempfile.TemporaryDirectory() as project:
        os.makedirs(os.path.join(project, ".claude"))
        with open(os.path.join(project, ".claude", "review_routing.json"), "w", encoding="utf-8") as f:
            f.write("{}")
        body = "x" * (handover_in.MAX_BYTES - 4) + "TAIL"
        with open(os.path.join(project, ".claude", "active_work.md"), "w", encoding="utf-8") as f:
            f.write(body)
        old_stdin, old_env = sys.stdin, os.environ.get("CLAUDE_PROJECT_DIR")
        sys.stdin = io.StringIO(json.dumps({"cwd": project}))
        os.environ["CLAUDE_PROJECT_DIR"] = project
        buf = io.StringIO()
        try:
            with contextlib.redirect_stdout(buf):
                handover_in.main()
        finally:
            sys.stdin = old_stdin
            if old_env is None:
                os.environ.pop("CLAUDE_PROJECT_DIR", None)
            else:
                os.environ["CLAUDE_PROJECT_DIR"] = old_env
        context = json.loads(buf.getvalue())["hookSpecificOutput"]["additionalContext"]
        assert "TAIL" in context
