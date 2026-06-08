#!/usr/bin/env python3
"""Fail if the current git branch is a protected default branch."""

from __future__ import annotations

import subprocess
import sys

PROTECTED_BRANCHES = frozenset({"main", "master"})


def current_branch() -> str:
    result = subprocess.run(
        ["git", "rev-parse", "--abbrev-ref", "HEAD"],
        capture_output=True,
        text=True,
        check=True,
    )
    return result.stdout.strip()


def main() -> int:
    branch = current_branch()
    if branch in PROTECTED_BRANCHES:
        print(
            f"Blocked: commits on '{branch}' are not allowed.\n"
            "Create a feature branch first:\n"
            "  git checkout -b feature/short-description",
            file=sys.stderr,
        )
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
