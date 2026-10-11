"""Sync active_market_codes in dbt_project.yml from docs/market_registry.yml.

Run after updating docs/market_registry.yml (adding, removing, or toggling a market).

Usage (from repo root):
    python scripts/sync_dbt_vars.py
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from ingestion.registry import active_market_codes

DBT_PROJECT_PATH = REPO_ROOT / "dbt_analytics" / "dbt_project.yml"


class BlockNotFound(Exception):
    """dbt_project.yml has no active_market_codes block to rewrite."""


def _update_dbt_project(codes: list[str]) -> bool:
    """Rewrite the block; True when the file changed, False when it already matched.
    Raises BlockNotFound when there is no block, which is a failure, not a no-op."""
    text = DBT_PROJECT_PATH.read_text(encoding="utf-8")

    new_list = "\n".join(f"    - {c}" for c in codes)
    new_block = f"  active_market_codes:\n{new_list}"

    pattern = re.compile(
        r"^  active_market_codes:\n(?:    - .+\n)*",
        re.MULTILINE,
    )

    if not pattern.search(text):
        raise BlockNotFound(
            "could not locate active_market_codes block in dbt_analytics/dbt_project.yml"
        )

    new_text = pattern.sub(new_block + "\n", text)
    if new_text == text:
        return False

    DBT_PROJECT_PATH.write_text(new_text, encoding="utf-8")
    return True


def main() -> int:
    try:
        codes = active_market_codes()
    except Exception as e:
        print(f"sync_dbt_vars: failed to read registry: {e}", file=sys.stderr)
        return 1

    if not codes:
        print(
            "sync_dbt_vars: no ingest_active markets found in registry",
            file=sys.stderr,
        )
        return 1

    try:
        changed = _update_dbt_project(codes)
    except BlockNotFound as e:
        print(f"sync_dbt_vars: {e}; nothing written", file=sys.stderr)
        return 1
    if changed:
        print(f"sync_dbt_vars: updated active_market_codes -> {codes}")
    else:
        print(f"sync_dbt_vars: already in sync ({len(codes)} markets: {codes})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
