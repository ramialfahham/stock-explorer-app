#!/usr/bin/env python3
"""Install repo git hooks (pre-commit blocks commits on main/master)."""

from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
HOOKS_DIR = REPO_ROOT / ".git" / "hooks"
PRE_COMMIT = HOOKS_DIR / "pre-commit"

HOOK_BODY = """#!/bin/sh
# Installed by scripts/install_git_hooks.py — do not edit by hand.
python scripts/check_not_on_main.py || exit 1
"""


def main() -> int:
    if not HOOKS_DIR.is_dir():
        print(f"Missing git hooks directory: {HOOKS_DIR}", file=sys.stderr)
        return 1

    PRE_COMMIT.write_text(HOOK_BODY, encoding="utf-8", newline="\n")
    PRE_COMMIT.chmod(PRE_COMMIT.stat().st_mode | 0o111)
    print(f"Installed {PRE_COMMIT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
