"""Verify dbt vars.active_market_codes matches registry ingest_active markets.

Registry source of truth: docs/market_registry.yml (ingest_active: true).
dbt var: active_market_codes in dbt_analytics/dbt_project.yml.

Usage (from repo root):
    python scripts/check_registry_var_sync.py
"""

from __future__ import annotations

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
    return out


def _dbt_var_codes() -> list[str]:
    data = yaml.safe_load(DBT_PROJECT_PATH.read_text(encoding="utf-8"))
    vars_block = data.get("vars") or {}
    raw = vars_block.get("active_market_codes")
    if raw is None:
        raise KeyError("dbt_project.yml missing vars.active_market_codes")
    if not isinstance(raw, list):
        raise TypeError("active_market_codes must be a YAML list")
    return [str(x) for x in raw]


def main() -> int:
    try:
        reg = _registry_active_codes()
        var = _dbt_var_codes()
    except Exception as e:
        print(f"check_registry_var_sync: {e}", file=sys.stderr)
        return 1

    if not reg:
        print(
            "check_registry_var_sync: registry has no ingest_active markets",
            file=sys.stderr,
        )
        return 1
    if not var:
        print(
            "check_registry_var_sync: active_market_codes is empty",
            file=sys.stderr,
        )
        return 1

    s_reg = sorted(set(reg))
    s_var = sorted(set(var))
    if s_reg != s_var:
        only_reg = sorted(set(reg) - set(var))
        only_var = sorted(set(var) - set(reg))
        print(
            "check_registry_var_sync: registry and dbt var lists differ.",
            file=sys.stderr,
        )
        if only_reg:
            print(f"  in registry only: {only_reg}", file=sys.stderr)
        if only_var:
            print(f"  in dbt_project.yml only: {only_var}", file=sys.stderr)
        print("  Run: python scripts/sync_dbt_vars.py", file=sys.stderr)
        return 1

    print(f"check_registry_var_sync: OK ({len(s_reg)} markets).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
