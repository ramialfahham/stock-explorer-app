"""active_market_codes is the sorted active-market list that the registry-sync, pipeline, eligibility and seed scripts read."""

from __future__ import annotations

import ast
import sys
from pathlib import Path

import yaml

import ingestion.registry as registry

INGESTION = Path(registry.__file__).resolve().parent


def test_returns_only_active_codes_in_sorted_order(tmp_path: Path, monkeypatch) -> None:
    path = tmp_path / "market_registry.yml"
    path.write_text(
        yaml.safe_dump(
            {
                "markets": [
                    {"market_code": "us_sp500", "index_name": "S&P 500", "ingest_active": True},
                    {"market_code": "fr_cac40", "index_name": "CAC 40", "ingest_active": False},
                    {"market_code": "de_dax", "index_name": "DAX", "ingest_active": True},
                ]
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(registry, "REGISTRY_PATH", path)

    assert registry.active_market_codes() == ["de_dax", "us_sp500"]


def test_registry_modules_import_only_the_standard_library_and_yaml() -> None:
    """The registry-var-sync pre-commit hook runs in an environment that has PyYAML and
    nothing else, and it imports ingestion.registry."""
    allowed_top = set(sys.stdlib_module_names) | {"yaml"}
    allowed_ingestion = {"ingestion", "ingestion.paths", "ingestion.registry"}
    for name in ("registry.py", "paths.py", "__init__.py"):
        tree = ast.parse((INGESTION / name).read_text(encoding="utf-8"))
        imported = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported.update(a.name for a in node.names)
            elif isinstance(node, ast.ImportFrom) and node.level:
                names = [node.module] if node.module else [a.name for a in node.names]
                imported.update(f"ingestion.{name}" for name in names)
            elif isinstance(node, ast.ImportFrom):
                imported.add(node.module)
        outside = {
            m for m in imported
            if m.split(".")[0] not in allowed_top and m not in allowed_ingestion
        }
        assert not outside, f"{name} imports {sorted(outside)}"
