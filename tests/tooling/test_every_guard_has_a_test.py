"""Every guard script wired into a hook has a test file that names it, other than the import
smoke test. Wired means: a command in .claude/settings.json, or a local hook in
.pre-commit-config.yaml whose entry is `python <script>.py`."""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[2]
SMOKE_TEST = "test_hooks_import.py"
SELF = Path(__file__).name
ENTRY_SCRIPT = re.compile(r"^python\s+(\S+\.py)\b")


def _settings_scripts() -> set[Path]:
    settings = json.loads((ROOT / ".claude" / "settings.json").read_text(encoding="utf-8"))
    found: set[Path] = set()
    for groups in settings.get("hooks", {}).values():
        for group in groups:
            for hook in group.get("hooks", []):
                match = re.search(r"\.claude/hooks/[\w.]+\.py", hook.get("command", ""))
                if match:
                    found.add(ROOT / match.group(0))
    return found


def _precommit_scripts() -> set[Path]:
    config = yaml.safe_load((ROOT / ".pre-commit-config.yaml").read_text(encoding="utf-8"))
    found: set[Path] = set()
    for repo in config["repos"]:
        if repo["repo"] != "local":
            continue
        for hook in repo["hooks"]:
            match = ENTRY_SCRIPT.match(str(hook.get("entry", "")))
            if match:
                found.add(ROOT / match.group(1))
    return found


def _tests_naming(stem: str, test_files: list[Path]) -> list[Path]:
    pattern = re.compile(rf"\b{re.escape(stem)}\b")
    return [p for p in test_files if pattern.search(p.read_text(encoding="utf-8"))]


def _real_test_files() -> list[Path]:
    return [
        p for p in sorted((ROOT / "tests").rglob("test_*.py")) if p.name not in (SMOKE_TEST, SELF)
    ]


WIRED = sorted(_settings_scripts() | _precommit_scripts())


def test_the_wired_guards_are_found() -> None:
    names = {p.name for p in WIRED}
    assert {
        "pre_push_gate.py",
        "branch_discipline.py",
        "handover_in.py",
        "powershell_git_guard.py",
        "commit_review_gate.py",
        "check_layer_contract.py",
        "check_dbt_sql_structure.py",
        "check_registry_var_sync.py",
    } <= names


def test_every_local_pre_commit_hook_is_a_script_this_file_can_see() -> None:
    config = yaml.safe_load((ROOT / ".pre-commit-config.yaml").read_text(encoding="utf-8"))
    entries = [
        str(hook.get("entry", ""))
        for repo in config["repos"]
        if repo["repo"] == "local"
        for hook in repo["hooks"]
    ]
    assert entries
    unseen = [e for e in entries if not ENTRY_SCRIPT.match(e)]
    assert not unseen, f"local hooks this test cannot map to a script: {unseen}"


@pytest.mark.parametrize("script", WIRED, ids=lambda p: p.name)
def test_a_wired_guard_exists_and_has_a_test_that_names_it(script: Path) -> None:
    assert script.is_file(), f"{script.relative_to(ROOT)} is wired but does not exist"
    assert _tests_naming(script.stem, _real_test_files()), (
        f"no test names {script.stem}; add a test that fails when it stops working"
    )


def test_the_smoke_test_and_this_file_do_not_count_as_coverage() -> None:
    names = {p.name for p in _real_test_files()}
    assert SMOKE_TEST not in names
    assert SELF not in names
    assert "test_pre_push_gate.py" in names
