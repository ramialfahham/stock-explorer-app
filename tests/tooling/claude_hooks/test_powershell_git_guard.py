"""powershell_git_guard: a PowerShell command that commits with a git-hook bypass is refused;
ordinary commits are left to the git hooks, pushes to GitLab's protection.

Runnable with `pytest` or directly: `python tests/tooling/claude_hooks/test_powershell_git_guard.py`.
"""

import contextlib
import io
import json
import os
import sys
import tempfile

_HOOKS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", ".claude", "hooks")
sys.path.insert(0, _HOOKS)

import powershell_git_guard as guard  # noqa: E402


def _run(command: str, project: str) -> str:
    old_stdin, old_env = sys.stdin, os.environ.get("CLAUDE_PROJECT_DIR")
    sys.stdin = io.StringIO(json.dumps({"tool_name": "PowerShell", "tool_input": {"command": command}}))
    os.environ["CLAUDE_PROJECT_DIR"] = project
    buf = io.StringIO()
    try:
        with contextlib.redirect_stdout(buf):
            guard.main()
    finally:
        sys.stdin = old_stdin
        if old_env is None:
            os.environ.pop("CLAUDE_PROJECT_DIR", None)
        else:
            os.environ["CLAUDE_PROJECT_DIR"] = old_env
    return buf.getvalue()


def test_a_bypass_is_refused_and_an_ordinary_commit_is_not():
    with tempfile.TemporaryDirectory() as project, tempfile.TemporaryDirectory() as other:
        os.makedirs(os.path.join(project, ".claude"))
        with open(os.path.join(project, ".claude", "review_routing.json"), "w", encoding="utf-8") as f:
            f.write("{}")
        for command in ("git add a; if ($?) { git commit -m x --no-verify }",
                        "$env:CLAUDECODE=''; git commit -m x"):
            denied = json.loads(_run(command, project))
            assert denied["hookSpecificOutput"]["permissionDecision"] == "deny", command
        assert _run("git add a; if ($?) { git commit -m 'x' }", project) == ""
        assert _run("git commit --no-verify -m x", other) == ""


if __name__ == "__main__":
    _failed = 0
    for _name, _fn in sorted(globals().items()):
        if _name.startswith("test_") and callable(_fn):
            try:
                _fn()
                print(f"ok   {_name}")
            except AssertionError as e:
                _failed += 1
                print(f"FAIL {_name}: {e}")
    print("all tests passed" if not _failed else f"{_failed} test(s) failed")
    sys.exit(1 if _failed else 0)
