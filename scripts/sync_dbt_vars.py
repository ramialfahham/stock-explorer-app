"""Sync active_market_codes in dbt_project.yml from docs/market_registry.yml.

Run after updating docs/market_registry.yml (adding, removing, or toggling a market).

Usage (from repo root):
    python scripts/sync_dbt_vars.py
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
REGISTRY_PATH = REPO_ROOT / "docs" / "market_registry.yml"
DBT_PROJECT_PATH = REPO_ROOT / "dbt_analytics" / "dbt_project.yml"


def _registry_active_codes() -> list[str]:
    data = yaml.safe_load(REGISTRY_PATH.read_text(encoding="utf-8"))
    markets = data.get("markets") or []
    out: list[str] = []
    for row in markets:
        if not isinstance(row, dict):
            continue
        if not row.get("ingest_active"):
            continue
        code = row.get("market_code")
        if code:
            out.append(str(code))
    return sorted(out)


def _update_dbt_project(codes: list[str]) -> bool:
    text = DBT_PROJECT_PATH.read_text(encoding="utf-8")

    new_list = "\n".join(f"    - {c}" for c in codes)
    new_block = f"  active_market_codes:\n{new_list}"

    pattern = re.compile(
        r"^  active_market_codes:\n(?:    - .+\n)*",
        re.MULTILINE,
    )

    if not pattern.search(text):
        print(
            "sync_dbt_vars: could not locate active_market_codes block "
            "in dbt_analytics/dbt_project.yml",
            file=sys.stderr,
        )
        return False

    new_text = pattern.sub(new_block + "\n", text)
    if new_text == text:
        return False

    DBT_PROJECT_PATH.write_text(new_text, encoding="utf-8")
    return True


def main() -> int:
    try:
        codes = _registry_active_codes()
    except Exception as e:
        print(f"sync_dbt_vars: failed to read registry — {e}", file=sys.stderr)
        return 1

    if not codes:
        print(
            "sync_dbt_vars: no ingest_active markets found in registry",
            file=sys.stderr,
        )
        return 1

    changed = _update_dbt_project(codes)
    if changed:
        print(f"sync_dbt_vars: updated active_market_codes → {codes}")
    else:
        print(f"sync_dbt_vars: already in sync ({len(codes)} markets: {codes})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
