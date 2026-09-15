"""This is a guard, so each test proves it fires, not that a happy path passes. The repo tree
itself is checked last: if that test fails, a doc exists with no line in CLAUDE.md pointing to
it, and the fix is to add one there, not to silence the check."""

from __future__ import annotations

from pathlib import Path

from check_docs_indexed import (  # noqa: E402
    CLAUDE_MD,
    GOVERNED_GLOBS,
    REPO_ROOT,
    find_violations,
    governed_docs,
    linked_docs,
)


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def test_a_linked_doc_passes(tmp_path: Path) -> None:
    _write(tmp_path / "docs" / "a.md", "content")
    claude_md = tmp_path / "CLAUDE.md"
    _write(claude_md, "See [a](docs/a.md) for detail.")
    assert find_violations(tmp_path, claude_md) == []


def test_an_unlinked_doc_fails(tmp_path: Path) -> None:
    _write(tmp_path / "docs" / "a.md", "content")
    claude_md = tmp_path / "CLAUDE.md"
    _write(claude_md, "No links here.")
    violations = find_violations(tmp_path, claude_md)
    assert len(violations) == 1
    assert "docs/a.md" in violations[0]


def test_a_docs_ui_file_is_governed_too(tmp_path: Path) -> None:
    _write(tmp_path / "docs" / "ui" / "x.md", "content")
    claude_md = tmp_path / "CLAUDE.md"
    _write(claude_md, "No links here.")
    violations = find_violations(tmp_path, claude_md)
    assert len(violations) == 1
    assert "docs/ui/x.md" in violations[0]


def test_a_nested_backlog_doc_is_not_governed(tmp_path: Path) -> None:
    # docs/*.md matches only direct children, matching check_context_budget.py's own
    # GOVERNED_GLOBS semantics -- docs/backlog/x.md is a grandchild, out of scope here.
    _write(tmp_path / "docs" / "backlog" / "x.md", "content")
    assert governed_docs(tmp_path) == set()


def test_a_link_with_a_leading_dot_slash_still_counts(tmp_path: Path) -> None:
    _write(tmp_path / "docs" / "a.md", "content")
    claude_md = tmp_path / "CLAUDE.md"
    _write(claude_md, "See [a](./docs/a.md).")
    assert find_violations(tmp_path, claude_md) == []


def test_a_link_with_a_fragment_still_counts(tmp_path: Path) -> None:
    _write(tmp_path / "docs" / "a.md", "content")
    claude_md = tmp_path / "CLAUDE.md"
    _write(claude_md, "See [a](docs/a.md#section).")
    assert find_violations(tmp_path, claude_md) == []


def test_a_link_to_a_different_doc_does_not_satisfy_this_one(tmp_path: Path) -> None:
    _write(tmp_path / "docs" / "a.md", "content")
    _write(tmp_path / "docs" / "b.md", "content")
    claude_md = tmp_path / "CLAUDE.md"
    _write(claude_md, "See [b](docs/b.md).")
    violations = find_violations(tmp_path, claude_md)
    assert len(violations) == 1
    assert "docs/a.md" in violations[0]


def test_a_missing_claude_md_fails(tmp_path: Path) -> None:
    _write(tmp_path / "docs" / "a.md", "content")
    violations = find_violations(tmp_path, tmp_path / "CLAUDE.md")
    assert len(violations) == 1
    assert "does not exist" in violations[0]


def test_governed_globs_cover_the_files_the_contract_names() -> None:
    assert GOVERNED_GLOBS == ("docs/*.md", "docs/ui/*.md")


def test_linked_docs_ignores_non_doc_links(tmp_path: Path) -> None:
    claude_md = tmp_path / "CLAUDE.md"
    _write(claude_md, "See [gh](https://github.com/x) and [script](scripts/x.py).")
    assert linked_docs(claude_md) == set()


def test_the_repo_tree_has_every_doc_indexed() -> None:
    violations = find_violations(REPO_ROOT, CLAUDE_MD)
    assert violations == [], "\n".join(violations)
