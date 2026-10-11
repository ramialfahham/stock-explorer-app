"""Model-file lookups shared by the dbt policy checkers."""

from __future__ import annotations

from pathlib import Path


def sql_model_names(models_dir: Path) -> set[str]:
    return {p.stem for p in models_dir.rglob("*.sql")}
