"""Enforce dbt documentation policy from docs/engineering_standards.md §2."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any

import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
DBT_PROJECT = REPO_ROOT / "dbt_analytics"
MODELS_DIR = DBT_PROJECT / "models"
MANIFEST_PATH = DBT_PROJECT / "target" / "manifest.json"
CATALOG_PATH = DBT_PROJECT / "target" / "catalog.json"
SOURCES_PATH = MODELS_DIR / "sources.yml"

GRAIN_PATTERN = re.compile(r"\*\*Grain:\*\*|Grain:", re.IGNORECASE)
WHAT_OR_SOURCE_PATTERN = re.compile(
    r"\*\*What:\*\*|\*\*Source:\*\*|What:|Source:",
    re.IGNORECASE,
)
REQUIRED_META_KEYS = ("owner", "domain", "criticality")


def _load_json(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise FileNotFoundError(
            f"Missing {path.relative_to(REPO_ROOT).as_posix()}. "
            "Run dbt build and dbt docs generate first."
        )
    return json.loads(path.read_text(encoding="utf-8"))


def _sql_model_names() -> set[str]:
    names: set[str] = set()
    for sql_path in MODELS_DIR.rglob("*.sql"):
        names.add(sql_path.stem)
    return names


def _column_description(
    manifest_columns: dict[str, Any],
    column_name: str,
) -> str:
    key = column_name.lower()
    col = manifest_columns.get(key) or manifest_columns.get(column_name)
    if not col:
        return ""
    return (col.get("description") or "").strip()


def check_model_descriptions(manifest: dict[str, Any], errors: list[str]) -> set[str]:
    documented: set[str] = set()
    sql_models = _sql_model_names()

    for node in manifest.get("nodes", {}).values():
        if node.get("resource_type") != "model":
            continue
        if node.get("package_name") != manifest.get("metadata", {}).get(
            "project_name", "dbt_analytics"
        ):
            continue

        name = node["name"]
        documented.add(name)
        description = (node.get("description") or "").strip()

        if not description:
            errors.append(f"model {name}: missing description")
            continue
        if not GRAIN_PATTERN.search(description):
            errors.append(f"model {name}: description must include Grain:")
        if not WHAT_OR_SOURCE_PATTERN.search(description):
            errors.append(
                f"model {name}: description must include What: or Source:"
            )

        meta = node.get("meta") or {}
        for key in REQUIRED_META_KEYS:
            if not meta.get(key):
                errors.append(f"model {name}: missing meta.{key}")

    missing_yaml = sorted(sql_models - documented)
    for name in missing_yaml:
        errors.append(f"model {name}: no manifest entry (missing YAML?)")

    return documented


def check_column_descriptions(
    manifest: dict[str, Any],
    catalog: dict[str, Any],
    errors: list[str],
) -> None:
    catalog_nodes = catalog.get("nodes", {})

    for node_id, node in manifest.get("nodes", {}).items():
        if node.get("resource_type") != "model":
            continue
        if node_id not in catalog_nodes:
            errors.append(
                f"model {node['name']}: not in catalog — run full dbt build before doc check"
            )
            continue

        manifest_columns = node.get("columns") or {}
        catalog_columns = catalog_nodes[node_id].get("columns") or {}

        for col_name in sorted(catalog_columns.keys()):
            desc = _column_description(manifest_columns, col_name)
            if not desc:
                errors.append(f"model {node['name']}.{col_name}: missing column description")


def check_sources(errors: list[str]) -> None:
    if not SOURCES_PATH.is_file():
        errors.append("sources.yml: missing")
        return

    data = yaml.safe_load(SOURCES_PATH.read_text(encoding="utf-8")) or {}
    for source in data.get("sources", []):
        source_name = source.get("name", "<unnamed>")
        if not (source.get("description") or "").strip():
            errors.append(f"source {source_name}: missing description")

        for table in source.get("tables", []):
            table_name = table.get("name", "<unnamed>")
            qualified = f"{source_name}.{table_name}"
            if not (table.get("description") or "").strip():
                errors.append(f"source table {qualified}: missing description")

            for column in table.get("columns", []):
                col_name = column.get("name", "<unnamed>")
                if not (column.get("description") or "").strip():
                    errors.append(
                        f"source {qualified}.{col_name}: missing column description"
                    )


def main() -> int:
    errors: list[str] = []

    try:
        manifest = _load_json(MANIFEST_PATH)
        catalog = _load_json(CATALOG_PATH)
    except FileNotFoundError as exc:
        print(str(exc))
        return 1

    check_model_descriptions(manifest, errors)
    check_column_descriptions(manifest, catalog, errors)
    check_sources(errors)

    if errors:
        print("dbt documentation checks failed:")
        for err in errors:
            print(f" - {err}")
        return 1

    print("dbt documentation checks passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
