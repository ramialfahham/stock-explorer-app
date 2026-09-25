"""Smoke test: every hook module imports cleanly.

Byte-compilation checks syntax but does NOT resolve imports, so a broken
`from _command_utils import <name>` would compile yet fail at runtime. Importing
each module here catches that -- it matters most for pre_push_gate, which no
other test imports.
"""

import importlib
import json
import os
import re
import sys

_HOOKS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", ".claude", "hooks")
sys.path.insert(0, _HOOKS)

_HOOK_MODULES = [
    "_command_utils",
    "branch_discipline",
    "commit_review_gate",
    "handover_in",
    "pre_push_gate",
]


def test_every_hook_module_imports():
    for name in _HOOK_MODULES:
        mod = importlib.import_module(name)
        assert mod is not None


# A PreToolUse deny survives every permission mode because Claude Code evaluates
# hooks first. That only holds while each gate's decision is purely a function of
# repo/diff state, so a gate that starts branching on permission_mode fails here.
_MODE_INDEPENDENT_HOOKS = ["commit_review_gate", "branch_discipline"]


def test_gate_hooks_never_branch_on_permission_mode():
    hooks_dir = _HOOKS
    for name in _MODE_INDEPENDENT_HOOKS:
        path = os.path.join(hooks_dir, f"{name}.py")
        with open(path, encoding="utf-8") as f:
            source = f.read()
        assert "permission_mode" not in source, (
            f"{name}.py references permission_mode; its deny would then depend on "
            "the session's permission mode instead of the repo state")


_SETTINGS = os.path.join(_HOOKS, "..", "settings.json")
_HOOK_SCRIPT_RE = re.compile(r'\$\{CLAUDE_PROJECT_DIR\}/(\.claude/hooks/[\w.]+\.py)')


def _settings_commands():
    with open(_SETTINGS, encoding="utf-8") as f:
        settings = json.load(f)
    for groups in settings.get("hooks", {}).values():
        for group in groups:
            for hook in group.get("hooks", []):
                yield hook.get("command", "")


def test_every_hook_in_settings_is_a_repo_script_that_exists():
    commands = list(_settings_commands())
    assert commands, "settings.json wires no hooks"
    repo_root = os.path.join(_HOOKS, "..", "..")
    for command in commands:
        m = _HOOK_SCRIPT_RE.search(command)
        assert m, f"hook does not run a repo script via CLAUDE_PROJECT_DIR: {command}"
        assert os.path.isfile(os.path.join(repo_root, m.group(1))), m.group(1)


if __name__ == "__main__":
    _failed = 0
    for _name, _fn in sorted(globals().items()):
        if _name.startswith("test_") and callable(_fn):
            try:
                _fn()
                print(f"ok   {_name}")
            except Exception as e:  # noqa: BLE001 -- surface import errors too
                _failed += 1
                print(f"FAIL {_name}: {type(e).__name__}: {e}")
    print("all tests passed" if not _failed else f"{_failed} test(s) failed")
    sys.exit(1 if _failed else 0)
