"""sql_model_names lists dbt model names from the .sql files under a models folder."""

from __future__ import annotations

from pathlib import Path

from dbt_models import sql_model_names


def test_names_come_from_sql_files_in_nested_folders_only(tmp_path: Path) -> None:
    (tmp_path / "1_staging" / "yfinance").mkdir(parents=True)
    (tmp_path / "1_staging" / "yfinance" / "stg_a.sql").write_text("select 1", encoding="utf-8")
    (tmp_path / "5_marts").mkdir()
    (tmp_path / "5_marts" / "mart_b.sql").write_text("select 1", encoding="utf-8")
    (tmp_path / "5_marts" / "_marts.yml").write_text("version: 2", encoding="utf-8")

    assert sql_model_names(tmp_path) == {"stg_a", "mart_b"}
