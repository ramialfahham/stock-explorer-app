"""check_layer_contract: each rule the script enforces (core has no ref to stg_ and no union_all,
intermediate has no ref to mart_, staging SQL sits under a source folder) fails a violating model
through main() and passes a compliant one. Models are built in a temp tree that stands in for the
repo root; the real paths are checked separately."""

from __future__ import annotations

from pathlib import Path

import pytest

import check_layer_contract as gate


@pytest.fixture
def models(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    root = tmp_path / "dbt_analytics" / "models"
    monkeypatch.setattr(gate, "REPO_ROOT", tmp_path)
    monkeypatch.setattr(gate, "DBT_MODELS", root)
    monkeypatch.setattr(gate, "CORE_DIR", root / "3_core")
    monkeypatch.setattr(gate, "INTERMEDIATE_DIR", root / "4_intermediate")
    monkeypatch.setattr(gate, "STAGING_DIR", root / "1_staging")
    return root


def _write(models: Path, relative: str, sql: str) -> None:
    path = models / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(sql, encoding="utf-8")


def _errors() -> list[str]:
    errors: list[str] = []
    gate.check_core_forbidden_patterns(errors)
    gate.check_intermediate_no_mart_refs(errors)
    gate.check_staging_layout(errors)
    return errors


def test_the_real_paths_point_at_the_dbt_layers_and_the_repo_passes() -> None:
    models = gate.REPO_ROOT / "dbt_analytics" / "models"
    assert gate.DBT_MODELS == models
    assert gate.CORE_DIR == models / "3_core" and gate.CORE_DIR.is_dir()
    assert gate.INTERMEDIATE_DIR == models / "4_intermediate" and gate.INTERMEDIATE_DIR.is_dir()
    assert gate.STAGING_DIR == models / "1_staging" and gate.STAGING_DIR.is_dir()
    assert gate.main() == 0


def test_a_compliant_tree_passes(models: Path, capsys) -> None:
    _write(models, "1_staging/yfinance/stg_a.sql", "select 1")
    _write(models, "3_core/core_a.sql", "select * from {{ ref('base_a') }}")
    _write(models, "4_intermediate/int_a.sql", "select * from {{ ref('core_a') }}")
    assert _errors() == []
    assert gate.main() == 0
    assert "passed" in capsys.readouterr().out


@pytest.mark.parametrize(
    "sql",
    ["select * from {{ ref('stg_a') }}", 'select * from {{ ref("stg_a") }}', "select {{ union_all(x) }}"],
)
def test_core_may_not_ref_staging_or_union_all(models: Path, sql: str, capsys) -> None:
    _write(models, "3_core/core_a.sql", sql)
    assert [e for e in _errors() if "3_core/core_a.sql" in e and "forbidden pattern in core" in e]
    assert gate.main() == 1
    assert "3_core/core_a.sql" in capsys.readouterr().out


def test_intermediate_may_not_ref_a_mart(models: Path, capsys) -> None:
    _write(models, "4_intermediate/int_a.sql", "select * from {{ ref('mart_cards') }}")
    assert [e for e in _errors() if "4_intermediate/int_a.sql" in e and "must not ref() mart_" in e]
    assert gate.main() == 1
    assert "4_intermediate/int_a.sql" in capsys.readouterr().out


def test_staging_sql_must_live_in_a_source_folder(models: Path, capsys) -> None:
    _write(models, "1_staging/stg_a.sql", "select 1")
    assert [e for e in _errors() if "1_staging/stg_a.sql" in e]
    assert gate.main() == 1
    assert "failed" in capsys.readouterr().out
