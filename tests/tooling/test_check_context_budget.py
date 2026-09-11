"""The context budget is a guard, so each test proves the guard fires, not that a happy path
passes. The repo tree itself is checked last: if that test fails, a file grew past its budget
and the fix is to raise the budget deliberately in docs/context_budget.yml, or shrink the file."""

from __future__ import annotations

from pathlib import Path

import pytest

from check_context_budget import (  # noqa: E402
    BUDGET_PATH,
    GOVERNED_GLOBS,
    REPO_ROOT,
    find_violations,
    governed_files,
    load_budgets,
    measured_size,
)


def _tree(tmp_path: Path, files: dict[str, int]) -> Path:
    for rel, size in files.items():
        p = tmp_path / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(b"x" * size)
    return tmp_path


def test_a_file_exactly_at_budget_passes(tmp_path: Path) -> None:
    root = _tree(tmp_path, {"docs/a.md": 100})
    assert find_violations(root, {"docs/a.md": 100}) == []


def test_a_file_one_byte_over_budget_fails_and_says_by_how_much(tmp_path: Path) -> None:
    root = _tree(tmp_path, {"docs/a.md": 101})
    violations = find_violations(root, {"docs/a.md": 100})
    assert len(violations) == 1
    assert "docs/a.md" in violations[0]
    assert "over by 1" in violations[0]


@pytest.mark.parametrize(
    "rel", ["CLAUDE.md", ".claude/x.md", ".claude/task/x.md", "docs/x.md", "docs/ui/x.md"]
)
def test_a_governed_file_with_no_budget_fails(tmp_path: Path, rel: str) -> None:
    root = _tree(tmp_path, {rel: 10})
    violations = find_violations(root, {})
    assert len(violations) == 1
    assert rel in violations[0]
    assert "no budget" in violations[0]


def test_an_ungoverned_markdown_file_is_ignored(tmp_path: Path) -> None:
    root = _tree(
        tmp_path, {"README.md": 10, ".claude/skills/s/SKILL.md": 10, "docs/ui/deep/x.md": 10}
    )
    assert governed_files(root) == set()
    assert find_violations(root, {}) == []


def test_crlf_and_lf_copies_of_the_same_text_measure_the_same(tmp_path: Path) -> None:
    lf = tmp_path / "lf.md"
    crlf = tmp_path / "crlf.md"
    lf.write_bytes(b"a\nb\nc\n")
    crlf.write_bytes(b"a\r\nb\r\nc\r\n")
    assert measured_size(lf) == measured_size(crlf) == 6


def test_a_budget_entry_whose_file_is_missing_fails(tmp_path: Path) -> None:
    violations = find_violations(tmp_path, {"docs/gone.md": 100})
    assert len(violations) == 1
    assert "does not exist" in violations[0]


@pytest.mark.parametrize("bad", ["0", "-5", "'100'", "true", "1.5"])
def test_a_non_positive_or_non_integer_budget_is_rejected(tmp_path: Path, bad: str) -> None:
    cfg = tmp_path / "b.yml"
    cfg.write_text(f"budgets:\n  docs/a.md: {bad}\n", encoding="utf-8")
    with pytest.raises(ValueError):
        load_budgets(cfg)


def test_governed_globs_cover_the_files_the_contract_names() -> None:
    assert GOVERNED_GLOBS == (
        "CLAUDE.md", ".claude/*.md", ".claude/task/*.md", "docs/*.md", "docs/ui/*.md"
    )


def test_the_repo_tree_is_within_budget() -> None:
    violations = find_violations(REPO_ROOT, load_budgets(BUDGET_PATH))
    assert violations == [], "\n".join(violations)
