"""The "Migrations on disk" table in docs/supabase_setup.md lists exactly the files in
supabase/migrations/, each once. A migration added without a row, or a row left behind after a
rename, fails here."""

from __future__ import annotations

import re
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
SETUP_DOC = REPO_ROOT / "docs" / "supabase_setup.md"
MIGRATIONS_DIR = REPO_ROOT / "supabase" / "migrations"

_HEADING = "### Migrations on disk"
_ROW_FILE = re.compile(r"^\|\s*`([^`|]+\.sql)`\s*\|")


def ledger_files(doc_text: str) -> list[str]:
    lines = doc_text.splitlines()
    assert _HEADING in lines, f"docs/supabase_setup.md has no '{_HEADING}' heading; this test reads the table under it"
    start = lines.index(_HEADING) + 1
    files: list[str] = []
    for line in lines[start:]:
        if line.startswith("#"):
            break
        match = _ROW_FILE.match(line)
        if match:
            files.append(match.group(1))
    return files


def find_ledger_problems(listed: list[str], on_disk: list[str]) -> list[str]:
    problems = [f"{name}: listed twice" for name in sorted({n for n in listed if listed.count(n) > 1})]
    problems += [f"{name}: on disk but not in the ledger" for name in sorted(set(on_disk) - set(listed))]
    problems += [f"{name}: in the ledger but not on disk" for name in sorted(set(listed) - set(on_disk))]
    return problems


def test_the_migrations_table_lists_every_file_on_disk() -> None:
    listed = ledger_files(SETUP_DOC.read_text(encoding="utf-8"))
    on_disk = [p.name for p in MIGRATIONS_DIR.glob("*.sql")]
    assert listed, "no rows found under the 'Migrations on disk' heading"
    assert find_ledger_problems(listed, on_disk) == []


_DOC = """\
## 2. Configure

### Migrations on disk

| File | Purpose |
|------|---------|
| `001_a.sql` | First |
| `002_b.sql` | Second, mentions `other.sql` in the text |

Prose after the table, with `003_c.sql` in it.

## 3. Next section

| `004_d.sql` | belongs to another section |
"""


def test_only_first_column_files_under_the_heading_are_read() -> None:
    assert ledger_files(_DOC) == ["001_a.sql", "002_b.sql"]


@pytest.mark.parametrize(
    ("listed", "on_disk", "expected"),
    [
        (["001_a.sql"], ["001_a.sql", "002_b.sql"], "002_b.sql: on disk but not in the ledger"),
        (["001_a.sql", "002_b.sql"], ["001_a.sql"], "002_b.sql: in the ledger but not on disk"),
        (["001_a.sql", "001_a.sql"], ["001_a.sql"], "001_a.sql: listed twice"),
    ],
)
def test_each_kind_of_ledger_mismatch_is_reported(listed: list[str], on_disk: list[str], expected: str) -> None:
    assert expected in find_ledger_problems(listed, on_disk)


def test_a_missing_heading_fails_with_a_message_that_names_it() -> None:
    with pytest.raises(AssertionError, match="Migrations on disk"):
        ledger_files("## 2. Configure\n\nno table here\n")


def test_a_matching_ledger_has_no_problem() -> None:
    assert find_ledger_problems(["001_a.sql", "002_b.sql"], ["002_b.sql", "001_a.sql"]) == []
