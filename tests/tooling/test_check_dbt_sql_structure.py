"""check_dbt_sql_structure: each rule the script enforces fails a violating model and passes a
compliant one. The scalar-subquery rule is pinned for a model that starts with SELECT only, which
is all the script catches. Models are built in a temp tree that stands in for the repo; the real
scanned paths are checked separately."""

from __future__ import annotations

from pathlib import Path

import pytest

import check_dbt_sql_structure as gate

COMPLIANT = """with src as (
    select a from {{ ref('x') }}
)

select a from src
"""


@pytest.fixture
def repo(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    monkeypatch.setattr(gate, "REPO_ROOT", tmp_path)
    monkeypatch.setattr(
        gate,
        "SQL_PATHS",
        (tmp_path / "dbt_analytics" / "models", tmp_path / "dbt_analytics" / "tests"),
    )
    return tmp_path


def _errors(repo: Path, sql: str, folder: str = "models") -> list[str]:
    path = repo / "dbt_analytics" / folder / "m.sql"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(sql, encoding="utf-8")
    errors: list[str] = []
    gate._check_file(path, errors)
    return errors


def test_the_real_scan_paths_cover_models_and_singular_tests() -> None:
    root = gate.REPO_ROOT / "dbt_analytics"
    assert set(gate.SQL_PATHS) == {root / "models", root / "tests"}
    assert all(path.is_dir() for path in gate.SQL_PATHS)
    assert gate.main() == 0


def test_a_compliant_model_passes(repo: Path) -> None:
    assert _errors(repo, COMPLIANT) == []


def test_jinja_lines_and_leading_comments_before_with_are_allowed(repo: Path) -> None:
    sql = "{% set k = 1 %}\n-- why this model exists\n" + COMPLIANT
    assert _errors(repo, sql) == []


def test_a_model_must_start_with_with(repo: Path) -> None:
    errors = _errors(repo, "select a from {{ ref('x') }}")
    assert any("must start with a WITH clause" in e for e in errors)


def test_an_inline_subquery_in_from_is_refused(repo: Path) -> None:
    sql = "with src as (\n    select a from {{ ref('x') }}\n)\n\nselect a from (select a from src) t\n"
    assert any("inline subquery in FROM" in e for e in _errors(repo, sql))


def test_a_scalar_subquery_in_a_select_first_model_is_refused(repo: Path) -> None:
    sql = "select a, (select max(a) from {{ ref('x') }}) as m from {{ ref('y') }}\n"
    assert any("scalar subquery in SELECT" in e for e in _errors(repo, sql))


def test_a_ref_outside_an_import_cte_is_refused(repo: Path) -> None:
    sql = "with src as (\n    select 1 as a\n)\n\nselect a from src join {{ ref('y') }} on true\n"
    assert any("must appear inside import CTEs" in e for e in _errors(repo, sql))


def test_singular_tests_are_checked_too(repo: Path, capsys) -> None:
    assert any("must start with a WITH clause" in e for e in _errors(repo, "select 1", folder="tests"))
    assert gate.main() == 1
    assert "dbt_analytics/tests/m.sql" in capsys.readouterr().out


def test_main_exits_1_on_a_violation_and_0_when_clean(repo: Path, capsys) -> None:
    model = repo / "dbt_analytics" / "models" / "m.sql"
    model.parent.mkdir(parents=True)
    model.write_text(COMPLIANT, encoding="utf-8")
    assert gate.main() == 0
    model.write_text("select 1", encoding="utf-8")
    assert gate.main() == 1
    assert "failed" in capsys.readouterr().out
