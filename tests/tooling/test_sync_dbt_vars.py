"""sync_dbt_vars.py: exit status and message must say what happened to dbt_project.yml.

Issue #8: a dbt_project.yml with no active_market_codes block printed "already in sync" and
exited 0; dbt then read whatever list it had while ingestion fetched the new market.
"""

from __future__ import annotations

from pathlib import Path

import pytest

import sync_dbt_vars

REGISTRY = """markets:
  - market_code: us_sp500
    ingest_active: true
  - market_code: de_dax
    ingest_active: true
  - market_code: fr_cac40
    ingest_active: false
"""

PROJECT_WITH_BLOCK = """name: dbt_analytics
vars:
  active_market_codes:
    - us_sp500
  other: 1
"""

PROJECT_WITHOUT_BLOCK = """name: dbt_analytics
vars:
  other: 1
"""


def _point_at(monkeypatch: pytest.MonkeyPatch, tmp_path: Path, project_text: str) -> Path:
    registry = tmp_path / "market_registry.yml"
    registry.write_text(REGISTRY, encoding="utf-8")
    project = tmp_path / "dbt_project.yml"
    project.write_text(project_text, encoding="utf-8")
    monkeypatch.setattr(sync_dbt_vars, "REGISTRY_PATH", registry)
    monkeypatch.setattr(sync_dbt_vars, "DBT_PROJECT_PATH", project)
    return project


def test_missing_block_exits_1_and_does_not_claim_sync(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    project = _point_at(monkeypatch, tmp_path, PROJECT_WITHOUT_BLOCK)
    assert sync_dbt_vars.main() == 1
    out, err = capsys.readouterr()
    assert "already in sync" not in out
    assert "could not locate active_market_codes" in err
    assert "nothing written" in err
    assert project.read_text(encoding="utf-8") == PROJECT_WITHOUT_BLOCK


def test_out_of_sync_block_is_rewritten_and_exits_0(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    project = _point_at(monkeypatch, tmp_path, PROJECT_WITH_BLOCK)
    assert sync_dbt_vars.main() == 0
    out, _err = capsys.readouterr()
    assert "updated active_market_codes" in out
    assert project.read_text(encoding="utf-8") == PROJECT_WITH_BLOCK.replace(
        "    - us_sp500", "    - de_dax" + chr(10) + "    - us_sp500"
    )


def test_in_sync_block_is_left_alone_and_exits_0(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    synced = PROJECT_WITH_BLOCK.replace("    - us_sp500", "    - de_dax" + chr(10) + "    - us_sp500")
    project = _point_at(monkeypatch, tmp_path, synced)
    assert sync_dbt_vars.main() == 0
    out, _err = capsys.readouterr()
    assert "already in sync (2 markets" in out
    assert project.read_text(encoding="utf-8") == synced
