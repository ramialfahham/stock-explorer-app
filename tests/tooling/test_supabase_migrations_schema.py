"""Migration 019 drops every precision cap on mart_stock_cards because numeric(10,4) would
overflow on one Yahoo outlier and abort the export (issue #9, A2). Nothing in Postgres stops a
later migration from adding a capped column back; this does."""

from __future__ import annotations

import re
from pathlib import Path

MIGRATIONS_DIR = Path(__file__).resolve().parents[2] / "supabase" / "migrations"
CAPPED_NUMERIC = re.compile(r"\b(numeric|decimal|dec)\s*\(\s*\d+\s*(,\s*\d+\s*)?\)", re.IGNORECASE)
LAST_MIGRATION_ALLOWED_TO_CAP = "002"


def _migrations_after(prefix: str) -> list[Path]:
    return sorted(p for p in MIGRATIONS_DIR.glob("*.sql") if p.name[:3] > prefix)


def test_no_migration_after_002_declares_a_capped_numeric_column() -> None:
    offenders = [
        f"{p.name}:{n}: {line.strip()}"
        for p in _migrations_after(LAST_MIGRATION_ALLOWED_TO_CAP)
        for n, line in enumerate(p.read_text(encoding="utf-8").splitlines(), start=1)
        if CAPPED_NUMERIC.search(line) and not line.lstrip().startswith("--")
    ]
    assert offenders == [], "\n".join(offenders)


def test_the_regex_catches_the_shapes_002_used() -> None:
    assert CAPPED_NUMERIC.search("forward_pe numeric(18, 6),")
    assert CAPPED_NUMERIC.search("x NUMERIC(10,4)")
    assert CAPPED_NUMERIC.search("x numeric (12)")
    assert CAPPED_NUMERIC.search("x decimal(10,4)")
    assert CAPPED_NUMERIC.search("x dec(10,4)")
    assert not CAPPED_NUMERIC.search("x numeric,")
    assert not CAPPED_NUMERIC.search("alter column x type numeric")
