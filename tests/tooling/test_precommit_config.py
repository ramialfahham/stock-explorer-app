"""Every hook from pre-commit-hooks starts as `python -m`, because Windows Smart App Control
blocks the unsigned .exe launcher pre-commit would otherwise generate for it."""

from __future__ import annotations

from pathlib import Path

import yaml

CONFIG = Path(__file__).resolve().parents[2] / ".pre-commit-config.yaml"


def test_pre_commit_hooks_run_through_python_not_their_launcher() -> None:
    repos = yaml.safe_load(CONFIG.read_text(encoding="utf-8"))["repos"]
    blocks = [r for r in repos if r["repo"].endswith("/pre-commit/pre-commit-hooks")]
    hooks = [hook for block in blocks for hook in block["hooks"]]
    assert hooks
    for hook in hooks:
        assert str(hook.get("entry", "")).startswith("python -m pre_commit_hooks."), hook["id"]
