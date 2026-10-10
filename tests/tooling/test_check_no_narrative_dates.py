"""This is a guard, so each test proves it fires, not that a happy path passes. The repo
tree itself is checked last: if that test fails, a real date/MR-ref/owner-decision wording
sat in a comment, docstring, or governed or DURABLE doc, and the fix is to state the current fact
instead. narrative-check: allow (this docstring names the very pattern it guards against)."""

from __future__ import annotations

from pathlib import Path

import pytest

from check_no_narrative_dates import (  # noqa: E402
    REPO_ROOT,
    find_violations,
)


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def test_a_dated_python_comment_fails(tmp_path: Path) -> None:
    _write(tmp_path / "a.py", "x = 1  # fixed 2026-09-05\n")
    violations = find_violations(tmp_path)
    assert len(violations) == 1
    assert "a.py" in violations[0] and "date-stamp" in violations[0]


def test_a_tool_cache_is_not_scanned(tmp_path: Path) -> None:
    # CI keeps pre-commit's hook environments (third-party pip code) in .cache/ in the repo.
    _write(tmp_path / ".cache" / "pre-commit" / "env" / "pip.py", "x = 1  # fixed 2026-09-05\n")
    assert find_violations(tmp_path) == []


def test_a_dated_python_docstring_fails(tmp_path: Path) -> None:
    _write(tmp_path / "a.py", '''def f():\n    """Fixed on 2026-09-05."""\n    pass\n''')
    violations = find_violations(tmp_path)
    assert len(violations) == 1
    assert "docstring" in violations[0]


def test_a_dated_string_literal_that_is_not_a_docstring_passes(tmp_path: Path) -> None:
    _write(tmp_path / "a.py", 'x = "snapshot_date is 2026-09-01"\n')
    assert find_violations(tmp_path) == []


def test_an_mr_reference_in_a_comment_fails(tmp_path: Path) -> None:
    _write(tmp_path / "a.py", "x = 1  # fixed in MR !115\n")
    violations = find_violations(tmp_path)
    assert len(violations) == 1
    assert "MR/PR reference" in violations[0]


def test_owner_approved_wording_in_a_comment_fails(tmp_path: Path) -> None:
    _write(tmp_path / "a.py", "x = 1  # owner-approved change\n")
    violations = find_violations(tmp_path)
    assert len(violations) == 1
    assert "owner-approved" in violations[0]


def test_a_sql_line_comment_with_a_date_fails(tmp_path: Path) -> None:
    _write(tmp_path / "a.sql", "select 1 -- fixed 2026-09-05\n")
    violations = find_violations(tmp_path)
    assert len(violations) == 1
    assert "a.sql" in violations[0]


def test_a_date_inside_a_sql_string_literal_passes(tmp_path: Path) -> None:
    _write(tmp_path / "a.sql", "select '2026-09-01' as snapshot_date\n")
    assert find_violations(tmp_path) == []


def test_a_sql_block_comment_with_an_mr_reference_fails(tmp_path: Path) -> None:
    _write(tmp_path / "a.sql", "/* owner-approved follow-up to MR #22 */\nselect 1\n")
    violations = find_violations(tmp_path)
    assert len(violations) == 1
    assert "block comment" in violations[0]


def test_a_durable_markdown_doc_with_a_date_fails(tmp_path: Path) -> None:
    _write(tmp_path / "a.md", "> DURABLE. **Owns:** x.\n\nFixed 2026-09-05.\n")
    violations = find_violations(tmp_path)
    assert len(violations) == 1
    assert "a.md" in violations[0]


def test_a_non_durable_markdown_doc_with_a_date_passes(tmp_path: Path) -> None:
    _write(tmp_path / "a.md", "# Just a title\n\nFixed 2026-09-05.\n")
    assert find_violations(tmp_path) == []


@pytest.mark.parametrize(
    "rel",
    [
        "docs/guide.md",
        "docs/ui/spec.md",
        "README.md",
        "CLAUDE.md",
        ".claude/working-agreement.md",
        ".claude/skills/onboard/SKILL.md",
        ".claude/agents/reviewer.md",
    ],
)
def test_a_governed_doc_is_scanned_without_a_durable_header(tmp_path: Path, rel: str) -> None:
    _write(tmp_path / rel, "# Title\n\nFixed 2026-09-05.\n")
    violations = find_violations(tmp_path)
    assert len(violations) == 1 and Path(rel).name in violations[0]


@pytest.mark.parametrize(
    "text,kind",
    [
        ("# Title\n\nThis rotted in MR\n!115 before it was fixed.\n", "MR/PR reference"),
        ("# Title\n\nA lower-stakes claim (owner\ndecision) than a score.\n", "owner-approved"),
        ("# Title\n\nThis rotted in MR !\n115 before it was fixed.\n", "MR/PR reference"),
        ("# Title\n\nThe metric was owner-\napproved last week.\n", "owner-approved"),
        ("# Title\n\nFixed on 2026-09-\n05 by a later run.\n", "date-stamp"),
    ],
)
def test_wording_split_across_a_line_break_fails(tmp_path: Path, text: str, kind: str) -> None:
    _write(tmp_path / "docs" / "a.md", text)
    violations = find_violations(tmp_path)
    assert len(violations) == 1 and ":3:" in violations[0].replace("\\", "/")
    assert kind in violations[0]


@pytest.mark.parametrize(
    "text",
    [
        "# Title\n\nNot 'fixed in MR\n!115'. <!-- narrative-check: allow -->\n",
        "# Title\n\n<!-- narrative-check: allow --> Not 'fixed in MR\n!115'.\n",
    ],
)
def test_a_split_mr_reference_with_the_allow_marker_on_either_line_passes(
    tmp_path: Path, text: str
) -> None:
    _write(tmp_path / "docs" / "a.md", text)
    assert find_violations(tmp_path) == []


@pytest.mark.parametrize(
    "rel",
    ["tests/README.md", "dbt_analytics/README.md", "docs/notes/old.md", ".pytest_cache/README.md"],
)
def test_a_doc_outside_the_governed_paths_is_not_scanned(tmp_path: Path, rel: str) -> None:
    _write(tmp_path / rel, "# Title\n\nFixed 2026-09-05.\n")
    assert find_violations(tmp_path) == []


def test_a_durable_doc_inside_the_pytest_cache_is_not_scanned(tmp_path: Path) -> None:
    _write(
        tmp_path / ".pytest_cache" / "notes.md", "> DURABLE. **Owns:** x.\n\nFixed 2026-09-05.\n"
    )
    assert find_violations(tmp_path) == []


def test_a_date_inside_a_fenced_code_block_in_a_durable_doc_passes(tmp_path: Path) -> None:
    _write(
        tmp_path / "a.md",
        "> DURABLE. **Owns:** x.\n\n```\nsnapshot_date: 2026-09-01\n```\n",
    )
    assert find_violations(tmp_path) == []


def test_a_date_in_a_durable_doc_table_row_still_fails(tmp_path: Path) -> None:
    _write(
        tmp_path / "a.md",
        "> DURABLE. **Owns:** x.\n\n| Added 2026-09-01 |\n",
    )
    violations = find_violations(tmp_path)
    assert len(violations) == 1


def test_the_allow_marker_exempts_one_line(tmp_path: Path) -> None:
    _write(
        tmp_path / "a.md",
        "> DURABLE. **Owns:** x.\n\nNot \"fixed 2026-09-05\". <!-- narrative-check: allow -->\n",
    )
    assert find_violations(tmp_path) == []


def test_a_migration_file_with_a_date_is_not_exempt(tmp_path: Path) -> None:
    _write(tmp_path / "supabase" / "migrations" / "001_x.sql", "-- fixed 2026-08-26\n")
    violations = find_violations(tmp_path)
    assert len(violations) == 1


def test_a_date_inside_a_migration_s_sql_comment_on_string_passes(tmp_path: Path) -> None:
    _write(
        tmp_path / "supabase" / "migrations" / "001_x.sql",
        "comment on column t.c is 'replaced x 2026-08-26';\n",
    )
    assert find_violations(tmp_path) == []


def test_the_repo_tree_has_no_narrative_dates() -> None:
    violations = find_violations(REPO_ROOT)
    assert violations == [], "\n".join(violations)
