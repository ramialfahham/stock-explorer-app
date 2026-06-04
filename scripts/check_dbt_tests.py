"""Enforce dbt testing policy from docs/engineering_standards.md §3.

Runs after `dbt parse` is optional — scans model YAML and singular tests only.
Does not replace `dbt test` / `dbt build`; complements Tier C volume gates.
"""

from __future__ import annotations

import re
import sys
from collections import defaultdict
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
DBT_MODELS = REPO_ROOT / "dbt_analytics" / "models"
DBT_TESTS = REPO_ROOT / "dbt_analytics" / "tests"
MIN_SINGULAR_TESTS = 3

REF_PATTERN = re.compile(
    r"""ref\s*\(\s*['"]([^'"]+)['"]\s*\)""",
    re.IGNORECASE,
)


def _sql_model_names() -> set[str]:
    return {p.stem for p in DBT_MODELS.rglob("*.sql")}


def _tests_key(entry: dict) -> list:
    return entry.get("data_tests") or entry.get("tests") or []


def _model_tests_from_yaml() -> dict[str, int]:
    counts: dict[str, int] = defaultdict(int)
    for yml_path in DBT_MODELS.rglob("*.yml"):
        data = yaml.safe_load(yml_path.read_text(encoding="utf-8")) or {}
        for model in data.get("models", []):
            name = model.get("name")
            if not name:
                continue
            counts[name] += len(_tests_key(model))
        for unit in data.get("unit_tests", []):
            model_name = unit.get("model")
            if model_name:
                counts[model_name] += 1
    return counts


def _singular_test_refs() -> dict[str, int]:
    counts: dict[str, int] = defaultdict(int)
    if not DBT_TESTS.is_dir():
        return counts
    for sql_path in DBT_TESTS.glob("*.sql"):
        text = sql_path.read_text(encoding="utf-8")
        for match in REF_PATTERN.finditer(text):
            counts[match.group(1)] += 1
    return counts


def main() -> int:
    errors: list[str] = []
    models = _sql_model_names()
    yaml_counts = _model_tests_from_yaml()
    singular_counts = _singular_test_refs()

    singular_files = list(DBT_TESTS.glob("*.sql")) if DBT_TESTS.is_dir() else []
    if len(singular_files) < MIN_SINGULAR_TESTS:
        errors.append(
            f"dbt_analytics/tests: expected at least {MIN_SINGULAR_TESTS} singular "
            f"SQL tests, found {len(singular_files)}"
        )

    for name in sorted(models):
        total = yaml_counts.get(name, 0) + singular_counts.get(name, 0)
        if total < 1:
            errors.append(
                f"model {name}: no model-level data_tests, unit test, or singular "
                "test coverage (§3)"
            )

    undocumented_yaml = sorted(set(yaml_counts) - models)
    for name in undocumented_yaml:
        errors.append(f"YAML tests reference unknown model {name}")

    if errors:
        print("dbt test policy checks failed:")
        for err in errors:
            print(f" - {err}")
        return 1

    print(
        f"dbt test policy checks passed ({len(models)} models, "
        f"{len(singular_files)} singular tests)."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
