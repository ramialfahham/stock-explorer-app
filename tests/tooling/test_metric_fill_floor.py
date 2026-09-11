"""Executes assert_metric_fill_floor.sql against an in-memory DuckDB, so the floor, the sample
size and the set of metrics it iterates are proven by running it, not by reading its text. CI
fixtures hold one financial and one pre-revenue row per market, so dbt build exercises the
floor for operating metrics only; this test covers the other two types.

jinja2 ships with dbt-core (requirements.txt); it is imported here to render the singular test
the way dbt would, with ref() mapped to the in-memory table names."""

from __future__ import annotations

import csv
import re
from pathlib import Path

import duckdb
import jinja2

REPO = Path(__file__).resolve().parents[2]
CATALOGUE = REPO / "dbt_analytics" / "seeds" / "metric_catalogue.csv"
FILL_FLOOR_TEST = REPO / "dbt_analytics" / "tests" / "assert_metric_fill_floor.sql"
METRIC_LITERAL = re.compile(r"'([a-z_]+)' as metric_id")


def _catalogue() -> list[dict[str, str]]:
    with CATALOGUE.open(encoding="utf-8") as f:
        return list(csv.DictReader(f))


def _rendered_sql() -> str:
    env = jinja2.Environment(undefined=jinja2.StrictUndefined)
    return env.from_string(FILL_FLOOR_TEST.read_text(encoding="utf-8")).render(ref=lambda n: n)


def _metric_ids() -> list[str]:
    return [row["metric_id"].strip() for row in _catalogue()]


def _run(rows: list[dict]) -> list[tuple]:
    """rows: dicts with market_code, company_type and any subset of metric columns."""
    con = duckdb.connect()
    con.execute(
        f"create table metric_catalogue as select * from read_csv('{CATALOGUE.as_posix()}')"
    )
    cols = ", ".join(f"{m} double" for m in _metric_ids())
    con.execute(
        "create table mart_stock_cards "
        f"(market_code varchar, company_type varchar, is_card_eligible boolean, {cols})"
    )
    for r in rows:
        names = ["market_code", "company_type", "is_card_eligible"] + [
            m for m in _metric_ids() if m in r
        ]
        eligible = r.get("is_card_eligible", True)
        values = [r["market_code"], r["company_type"], eligible] + [r[m] for m in names[3:]]
        con.execute(
            f"insert into mart_stock_cards ({', '.join(names)}) "
            f"values ({', '.join('?' for _ in names)})",
            values,
        )
    return con.execute(_rendered_sql()).fetchall()


def _rows(n: int, company_type: str, market: str = "m1", **filled: float) -> list[dict]:
    return [dict(market_code=market, company_type=company_type, **filled) for _ in range(n)]


def _all_filled(company_type: str) -> dict[str, float]:
    return {
        row["metric_id"]: 1.0
        for row in _catalogue()
        if company_type in row["applies_to"].split("|")
    }


def test_the_rendered_test_iterates_exactly_the_catalogue_metrics() -> None:
    assert sorted(set(METRIC_LITERAL.findall(_rendered_sql()))) == sorted(_metric_ids())


def test_five_rows_at_forty_percent_are_returned() -> None:
    filled = _all_filled("operating")
    partly = {**filled, "debt_to_equity": None}
    rows = _rows(2, "operating", **filled) + _rows(3, "operating", **partly)
    result = _run(rows)
    assert result == [("m1", "operating", "debt_to_equity", 5, 0.4)]


def test_five_rows_at_sixty_percent_pass() -> None:
    filled = _all_filled("operating")
    partly = {**filled, "debt_to_equity": None}
    rows = _rows(3, "operating", **filled) + _rows(2, "operating", **partly)
    assert _run(rows) == []


def test_four_rows_entirely_null_are_skipped_by_the_sample_floor() -> None:
    filled = {**_all_filled("operating"), "debt_to_equity": None}
    assert _run(_rows(4, "operating", **filled)) == []


def test_a_pre_revenue_metric_null_across_five_rows_is_returned() -> None:
    filled = {**_all_filled("pre_revenue"), "cash_runway_months": None}
    assert _run(_rows(5, "pre_revenue", **filled)) == [
        ("m1", "pre_revenue", "cash_runway_months", 5, 0.0)
    ]


def test_a_financial_metric_null_across_five_rows_is_returned() -> None:
    filled = {**_all_filled("financial"), "roa_pct": None}
    assert _run(_rows(5, "financial", **filled)) == [("m1", "financial", "roa_pct", 5, 0.0)]


def test_a_metric_that_does_not_apply_to_the_type_is_ignored() -> None:
    rows = _rows(5, "financial", **_all_filled("financial"))
    for r in rows:
        r["fcf_margin_pct"] = None
    assert _run(rows) == []


def test_exactly_half_filled_passes() -> None:
    filled = _all_filled("operating")
    partly = {**filled, "debt_to_equity": None}
    rows = _rows(3, "operating", **filled) + _rows(3, "operating", **partly)
    assert _run(rows) == []


def test_ineligible_rows_do_not_count() -> None:
    """The mart holds eligible rows only today, so the filter is a no-op there; this pins that
    the floor is defined over eligible cards, as the contract says, not over whatever the table
    holds."""
    filled = _all_filled("operating")
    ineligible = {**filled, "debt_to_equity": None, "is_card_eligible": False}
    rows = _rows(5, "operating", **filled) + _rows(6, "operating", **ineligible)
    assert _run(rows) == []
