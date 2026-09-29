#!/usr/bin/env python
"""PreToolUse(PowerShell) guardrail -- no git-hook bypass from PowerShell.

The review gate and `no-commit-to-branch` run as git commit hooks, so they gate commits
from the PowerShell tool as well; a push to `main` is refused by GitLab. What a git hook
cannot stop is being skipped, so this refuses a PowerShell command that commits with a
bypass (`--no-verify`, `commit -n`, `core.hooksPath`, pre-commit's `SKIP`, a CLAUDECODE
change) or sets `core.hooksPath`. Everything else, including ordinary commits and pushes,
passes.

Fails OPEN: a non-matching command exits 0 with no output; an unexpected error exits
non-zero with a traceback, which Claude Code treats as non-blocking.
"""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _command_utils import (  # noqa: E402
    bash_command,
    emit_deny,
    hook_bypass,
    project_opted_in,
    read_event,
)


def main() -> int:
    event = read_event()
    if not project_opted_in(event):
        return 0
    bypass = hook_bypass(bash_command(event))
    if bypass:
        emit_deny(
            f"HOOK BYPASS BLOCKED: {bypass} would skip git's commit hooks (the review gate "
            "and `no-commit-to-branch`). Commit without it."
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
