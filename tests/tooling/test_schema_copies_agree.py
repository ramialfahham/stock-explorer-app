"""The dbt mart contract, EXPORT_COLUMNS and the Postgres migrations describe one table.

Nothing else compares them: a column added to one copy and not the others fails only at the
export, in production. This test reads the three copies and fails on a missing column, an
unexpected column or a type that does not map. Column types are compared by family
(numeric(18, 6) and numeric are both numeric)."""

from __future__ import annotations

import re
from pathlib import Path

import pytest
import yaml

import export_to_supabase as exp

REPO_ROOT = Path(__file__).resolve().parents[2]
MARTS_YML = REPO_ROOT / "dbt_analytics" / "models" / "5_marts" / "_marts.yml"
MIGRATIONS_DIR = REPO_ROOT / "supabase" / "migrations"

NOT_EXPORTED = {
    "info_ebitda": "data-only denominator of net_debt_to_ebitda; no card renders it",
    "stmt_free_cash_flow": "data-only numerator of fcf_margin_pct; no card renders it",
    "stmt_stockholders_equity": "data-only denominator of debt_to_equity and statement_roe_pct; no card renders it",
}
DATABASE_ONLY = {
    "id": "identity key the table adds",
    "exported_at": "write time the table adds",
}
POSTGRES_TYPE_FOR_CONTRACT_TYPE = {
    "varchar": "text",
    "double": "numeric",
    "bigint": "bigint",
    "integer": "integer",
    "boolean": "boolean",
    "date": "date",
}

_TABLE = r"public\.mart_stock_cards"
_STATEMENT = re.compile(
    rf"create\s+table\s+(?:if\s+not\s+exists\s+)?{_TABLE}\s*\((?P<create>.*?)\n\)\s*;"
    rf"|alter\s+table\s+(?:if\s+exists\s+)?(?:only\s+)?{_TABLE}\b(?P<alter>[^;]*);",
    re.IGNORECASE | re.DOTALL,
)
_ADD_COLUMN = re.compile(r"add\s+column\s+(?:if\s+not\s+exists\s+)?(\w+)\s+([a-z]+)", re.IGNORECASE)
_UNSUPPORTED = re.compile(r"\b(drop\s+column|rename|alter\s+column|add\s+constraint|drop\s+constraint)\b", re.IGNORECASE)
_NOT_A_COLUMN = {"unique", "constraint", "primary", "foreign", "check", "like", "exclude", "references"}
_DO_BLOCK = re.compile(r"\bdo\s+\$\$.*?\$\$\s*;", re.IGNORECASE | re.DOTALL)
_PRECISION_CAP_DROP = "atttypmod <> -1"


def contract_columns(yml_text: str) -> dict[str, str]:
    models = yaml.safe_load(yml_text)["models"]
    mart = next(m for m in models if m["name"] == "mart_stock_cards")
    return {c["name"]: c["data_type"] for c in mart["columns"]}


def table_columns(migrations: list[tuple[str, str]]) -> dict[str, str]:
    """Columns of public.mart_stock_cards after applying the migrations in file order.

    Reads `public.`-qualified, unquoted table names only. The one DO block it accepts is the
    numeric precision-cap drop of 019 (recognised by its catalogue filter), which never changes a
    column's type family. Any other statement or DO block that changes or mentions an existing
    column fails here, so the parser is extended on purpose."""
    columns: dict[str, str] = {}
    for name, sql in migrations:
        sql = re.sub(r"--[^\n]*", "", sql)
        for block in _DO_BLOCK.findall(sql):
            if "mart_stock_cards" in block and _PRECISION_CAP_DROP not in block:
                raise AssertionError(
                    f"{name}: a DO block touches mart_stock_cards; "
                    "extend table_columns in tests/tooling/test_schema_copies_agree.py"
                )
        sql = _DO_BLOCK.sub("", sql)
        for match in _STATEMENT.finditer(sql):
            if match.group("create") is not None:
                columns = {}
                for line in match.group("create").splitlines():
                    parts = re.match(r"\s*(\w+)\s+([a-z]+)", line, re.IGNORECASE)
                    if parts and parts.group(1).lower() not in _NOT_A_COLUMN:
                        columns[parts.group(1)] = parts.group(2).lower()
            else:
                body = match.group("alter")
                if _UNSUPPORTED.search(body):
                    raise AssertionError(
                        f"{name}: a statement on mart_stock_cards changes an existing column; "
                        "extend table_columns in tests/tooling/test_schema_copies_agree.py"
                    )
                for column, column_type in _ADD_COLUMN.findall(body):
                    columns[column] = column_type.lower()
    return columns


def find_disagreements(
    contract: dict[str, str],
    exported: list[str],
    table: dict[str, str],
    not_exported: set[str],
    database_only: set[str],
) -> list[str]:
    problems: list[str] = []
    exported_set = set(exported)
    if len(exported) != len(exported_set):
        problems.append("EXPORT_COLUMNS lists a column twice")
    for column in sorted(exported_set - set(contract)):
        problems.append(f"{column}: exported but not in the dbt contract")
    for column in sorted(set(contract) - exported_set - not_exported):
        problems.append(f"{column}: in the dbt contract, not exported and not in NOT_EXPORTED")
    for column in sorted(not_exported & exported_set):
        problems.append(f"{column}: listed in NOT_EXPORTED but exported")
    for column in sorted(not_exported - set(contract)):
        problems.append(f"{column}: listed in NOT_EXPORTED but not in the dbt contract")
    for column in sorted(exported_set - set(table)):
        problems.append(f"{column}: exported but missing from the migrations")
    for column in sorted(set(table) - exported_set - database_only):
        problems.append(f"{column}: in the migrations but not exported")
    for column in sorted(set(contract) & set(table)):
        wanted = POSTGRES_TYPE_FOR_CONTRACT_TYPE.get(contract[column])
        if wanted is None:
            problems.append(
                f"{column}: contract type {contract[column]} has no Postgres mapping; "
                "add it to POSTGRES_TYPE_FOR_CONTRACT_TYPE in tests/tooling/test_schema_copies_agree.py"
            )
        elif wanted != table[column]:
            problems.append(f"{column}: contract {contract[column]} but migrations {table[column]}")
    return problems


def _migrations_on_disk() -> list[tuple[str, str]]:
    return [(p.name, p.read_text(encoding="utf-8")) for p in sorted(MIGRATIONS_DIR.glob("*.sql"))]


def test_the_three_schema_copies_agree() -> None:
    problems = find_disagreements(
        contract_columns(MARTS_YML.read_text(encoding="utf-8")),
        exp.EXPORT_COLUMNS,
        table_columns(_migrations_on_disk()),
        set(NOT_EXPORTED),
        set(DATABASE_ONLY),
    )
    assert problems == []


_CONTRACT = {"a": "varchar", "b": "double", "c": "integer", "z": "double"}
_EXPORTED = ["a", "b", "c"]
_TABLE_COLUMNS = {"id": "bigint", "a": "text", "b": "numeric", "c": "integer"}


def _problems(**changes) -> list[str]:
    args = {
        "contract": _CONTRACT,
        "exported": _EXPORTED,
        "table": _TABLE_COLUMNS,
        "not_exported": {"z"},
        "database_only": {"id"},
    }
    args.update(changes)
    return find_disagreements(**args)


def test_a_consistent_set_of_copies_has_no_problem() -> None:
    assert _problems() == []


@pytest.mark.parametrize(
    ("changes", "expected"),
    [
        ({"exported": _EXPORTED + ["new"]}, "new: exported but not in the dbt contract"),
        ({"contract": {**_CONTRACT, "extra": "double"}}, "extra: in the dbt contract, not exported and not in NOT_EXPORTED"),
        ({"not_exported": {"z", "a"}}, "a: listed in NOT_EXPORTED but exported"),
        ({"not_exported": {"z", "gone"}}, "gone: listed in NOT_EXPORTED but not in the dbt contract"),
        ({"table": {"id": "bigint", "a": "text", "b": "numeric"}}, "c: exported but missing from the migrations"),
        ({"table": {**_TABLE_COLUMNS, "stray": "text"}}, "stray: in the migrations but not exported"),
        ({"table": {**_TABLE_COLUMNS, "c": "bigint"}}, "c: contract integer but migrations bigint"),
        ({"contract": {**_CONTRACT, "a": "float"}}, "a: contract type float has no Postgres mapping"),
        ({"exported": _EXPORTED + ["a"]}, "EXPORT_COLUMNS lists a column twice"),
    ],
)
def test_each_kind_of_disagreement_is_reported(changes: dict, expected: str) -> None:
    assert any(problem.startswith(expected) for problem in _problems(**changes))


def test_the_table_is_rebuilt_from_the_last_create_then_extended_by_add_column() -> None:
    columns = table_columns(
        [
            ("001.sql", "create table public.mart_stock_cards (\n    old_one text\n);"),
            (
                "002.sql",
                "drop table if exists public.mart_stock_cards;\n"
                "create table public.mart_stock_cards (\n"
                "    id bigint generated always as identity primary key,\n"
                "    ticker text not null,\n"
                "    forward_pe numeric(18, 6),\n"
                "    unique (ticker)\n"
                ");",
            ),
            (
                "003.sql",
                "-- add column if not exists commented_out text;\n"
                "alter table public.mart_stock_cards\n"
                "    add column if not exists a text,\n"
                "    add column if not exists b bigint;\n"
                "alter table public.other_table add column if not exists c text;",
            ),
        ]
    )
    assert columns == {"id": "bigint", "ticker": "text", "forward_pe": "numeric", "a": "text", "b": "bigint"}


def test_a_do_block_that_only_drops_precision_caps_is_skipped() -> None:
    columns = table_columns(
        [
            ("001.sql", "create table public.mart_stock_cards (\n    x numeric(10, 4)\n);"),
            (
                "019.sql",
                "do $$\nbegin\n    for col in select attname from pg_attribute where atttypmod <> -1 loop\n"
                "        execute format('alter table public.mart_stock_cards alter column %I type numeric', col.attname);\n"
                "    end loop;\nend\n$$;",
            ),
        ]
    )
    assert columns == {"x": "numeric"}


def test_a_do_block_that_is_not_the_precision_cap_drop_is_not_silently_ignored() -> None:
    block = "do $$\nbegin\n    execute 'alter table public.mart_stock_cards alter column x type text';\nend\n$$;"
    with pytest.raises(AssertionError, match="009.sql"):
        table_columns(
            [
                ("001.sql", "create table public.mart_stock_cards (\n    x numeric\n);"),
                ("009.sql", block),
            ]
        )


def test_constraint_lines_in_a_create_body_are_not_columns() -> None:
    columns = table_columns(
        [
            (
                "001.sql",
                "create table public.mart_stock_cards (\n"
                "    a text,\n"
                "    constraint c1 unique (a),\n"
                "    primary key (a),\n"
                "    check (a is not null),\n"
                "    foreign key (a) references public.markets (market_code),\n"
                "    b text\n"
                "        references public.markets (market_code)\n"
                ");",
            )
        ]
    )
    assert columns == {"a": "text", "b": "text"}


def test_alter_table_only_is_read_like_alter_table() -> None:
    columns = table_columns(
        [
            ("001.sql", "create table public.mart_stock_cards (\n    a text\n);"),
            ("002.sql", "alter table only public.mart_stock_cards add column if not exists b text;"),
        ]
    )
    assert columns == {"a": "text", "b": "text"}


@pytest.mark.parametrize(
    "statement",
    [
        "alter table public.mart_stock_cards drop column x;",
        "alter table public.mart_stock_cards rename column x to y;",
        "alter table public.mart_stock_cards alter column x type text;",
    ],
)
def test_a_statement_that_changes_an_existing_column_is_not_silently_ignored(statement: str) -> None:
    with pytest.raises(AssertionError, match="009.sql"):
        table_columns(
            [
                ("001.sql", "create table public.mart_stock_cards (\n    x numeric\n);"),
                ("009.sql", statement),
            ]
        )
