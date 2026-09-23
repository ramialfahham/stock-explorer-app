"""A migration that alters mart_stock_cards after current_cards exists must recreate the view."""

from __future__ import annotations

import re
from pathlib import Path

MIGRATIONS_DIR = Path(__file__).resolve().parents[2] / "supabase" / "migrations"

_COMMENTS = re.compile(r"--[^\n]*|/\*.*?\*/", re.S)
_CREATES_VIEW = re.compile(r"create\s+(or\s+replace\s+)?view\s+public\.current_cards\b", re.I)
_RESHAPES_MART = re.compile(
    r"(alter|drop|create)\s+table\s+(if\s+(not\s+)?exists\s+)?(only\s+)?public\.mart_stock_cards\b",
    re.I,
)


def migrations_altering_mart_without_view(paths: list[Path]) -> list[str]:
    offenders: list[str] = []
    view_exists = False
    for path in sorted(paths):
        sql = _COMMENTS.sub("", path.read_text(encoding="utf-8"))
        recreates = bool(_CREATES_VIEW.search(sql))
        if view_exists and _RESHAPES_MART.search(sql) and not recreates:
            offenders.append(path.name)
        view_exists = view_exists or recreates
    return offenders


def test_repo_migrations_keep_current_cards_in_step_with_the_mart() -> None:
    assert migrations_altering_mart_without_view(list(MIGRATIONS_DIR.glob("*.sql"))) == []


def test_guard_catches_a_mart_change_that_skips_the_view(tmp_path: Path) -> None:
    (tmp_path / "020_view.sql").write_text("create view public.current_cards as select 1;")
    (tmp_path / "021_add.sql").write_text("alter table public.mart_stock_cards add column x int;")
    (tmp_path / "022_ok.sql").write_text(
        "alter table public.mart_stock_cards add column y int;\n"
        "drop view public.current_cards;\ncreate view public.current_cards as select 1;"
    )
    assert migrations_altering_mart_without_view(list(tmp_path.glob("*.sql"))) == ["021_add.sql"]


def test_guard_catches_rebuilds_only_variants_and_commented_out_recreates(tmp_path: Path) -> None:
    (tmp_path / "020_view.sql").write_text("create view public.current_cards as select 1;")
    (tmp_path / "021_rebuild.sql").write_text(
        "drop table if exists public.mart_stock_cards cascade;\n"
        "create table public.mart_stock_cards (x int);"
    )
    (tmp_path / "022_only.sql").write_text("alter table only public.mart_stock_cards add column y int;")
    (tmp_path / "023_commented.sql").write_text(
        "-- create view public.current_cards as select 1;\n"
        "alter table public.mart_stock_cards drop column y;"
    )
    assert migrations_altering_mart_without_view(list(tmp_path.glob("*.sql"))) == [
        "021_rebuild.sql",
        "022_only.sql",
        "023_commented.sql",
    ]


def test_guard_ignores_mart_changes_before_the_view_existed(tmp_path: Path) -> None:
    (tmp_path / "019_alter.sql").write_text("alter table public.mart_stock_cards add column x int;")
    (tmp_path / "020_view.sql").write_text("create view public.current_cards as select 1;")
    assert migrations_altering_mart_without_view(list(tmp_path.glob("*.sql"))) == []
