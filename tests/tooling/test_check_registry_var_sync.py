"""check_registry_var_sync: the script fails when the registry's ingest_active markets and the
dbt var `active_market_codes` differ, and passes when they match. Runs the real script's main()
against temp files."""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

import check_registry_var_sync as gate
import ingestion.registry as registry_module

ACTIVE = [
    {"market_code": "us", "index_name": "US", "ingest_active": True},
    {"market_code": "de", "index_name": "DE", "ingest_active": True},
    {"market_code": "xx", "index_name": "XX", "ingest_active": False},
]


@pytest.fixture
def files(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    registry, project = tmp_path / "market_registry.yml", tmp_path / "dbt_project.yml"
    monkeypatch.setattr(registry_module, "REGISTRY_PATH", registry)
    monkeypatch.setattr(gate, "DBT_PROJECT_PATH", project)

    def write(registry_markets, var_codes) -> None:
        registry.write_text(yaml.safe_dump({"markets": registry_markets}), encoding="utf-8")
        project.write_text(yaml.safe_dump({"vars": {"active_market_codes": var_codes}}), encoding="utf-8")

    return write


def test_matching_lists_pass_regardless_of_order(files, capsys) -> None:
    files(ACTIVE, ["de", "us"])
    assert gate.main() == 0
    assert "OK (2 markets)" in capsys.readouterr().out


def test_an_active_market_missing_from_the_var_fails(files, capsys) -> None:
    files(ACTIVE, ["us"])
    assert gate.main() == 1
    assert "in registry only: ['de']" in capsys.readouterr().err


def test_a_var_market_missing_from_the_registry_fails(files, capsys) -> None:
    files(ACTIVE, ["us", "de", "xx"])
    assert gate.main() == 1
    assert "in dbt_project.yml only: ['xx']" in capsys.readouterr().err


def test_a_missing_var_fails(files, capsys) -> None:
    files(ACTIVE, ["us", "de"])
    gate.DBT_PROJECT_PATH.write_text(yaml.safe_dump({"vars": {}}), encoding="utf-8")
    assert gate.main() == 1
    assert "missing vars.active_market_codes" in capsys.readouterr().err


def test_an_empty_var_fails(files, capsys) -> None:
    files(ACTIVE, [])
    assert gate.main() == 1
    assert "active_market_codes is empty" in capsys.readouterr().err


def test_a_var_that_is_not_a_list_fails(files, capsys) -> None:
    files(ACTIVE, "us")
    assert gate.main() == 1
    assert "must be a YAML list" in capsys.readouterr().err


def test_no_active_markets_fails(files, capsys) -> None:
    files([{"market_code": "xx", "index_name": "XX", "ingest_active": False}], ["xx"])
    assert gate.main() == 1
    assert "no ingest_active markets" in capsys.readouterr().err
