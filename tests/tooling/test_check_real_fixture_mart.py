"""The golden-mart gate must FAIL on a difference, not only pass on a match: CI only ever runs
the matching case, so a comparison that quietly returned nothing would stay green forever."""

from __future__ import annotations

import duckdb
import pandas as pd
import pytest

import check_real_fixture_mart as gate

ROWS = [
    ("us_sp500", "AAPL", 31.2345678912, True, 1976),
    ("uk_ftse100", "SHEL", None, True, None),
]


def _mart(path, rows=ROWS, extra_column: bool = False) -> None:
    with duckdb.connect(str(path)) as con:
        con.execute("create schema marts")
        extra = ", note varchar" if extra_column else ""
        con.execute(
            "create table marts.mart_stock_cards (market_code varchar, ticker varchar, "
            f"forward_pe double, is_card_eligible boolean, company_founded_year integer, "
            f"snapshot_date date{extra})"
        )
        for row in rows:
            values = (*row, "2026-10-05") + (("x",) if extra_column else ())
            con.execute(
                f"insert into marts.mart_stock_cards values ({', '.join('?' * len(values))})",
                values,
            )


@pytest.fixture
def golden(tmp_path, monkeypatch):
    path = tmp_path / "golden.csv"
    monkeypatch.setattr(gate, "GOLDEN_PATH", path)
    db = tmp_path / "golden.db"
    _mart(db)
    assert gate.main(["--duckdb-path", str(db), "--write"]) == 0
    return path


def _check(tmp_path, capsys, **kwargs) -> tuple[int, str]:
    db = tmp_path / "actual.db"
    _mart(db, **kwargs)
    code = gate.main(["--duckdb-path", str(db)])
    return code, capsys.readouterr().out


def test_an_identical_mart_passes(golden, tmp_path, capsys) -> None:
    code, out = _check(tmp_path, capsys)
    assert code == 0
    assert "2 rows match" in out


def test_a_changed_number_fails_and_is_listed(golden, tmp_path, capsys) -> None:
    rows = [("us_sp500", "AAPL", 31.3, True, 1976), ROWS[1]]
    code, out = _check(tmp_path, capsys, rows=rows)
    assert code == 1
    assert "us_sp500/AAPL.forward_pe: '31.2345679' -> '31.3'" in out


def test_a_missing_row_fails(golden, tmp_path, capsys) -> None:
    code, out = _check(tmp_path, capsys, rows=ROWS[:1])
    assert code == 1
    assert "uk_ftse100/SHEL: row missing" in out


def test_an_extra_row_fails(golden, tmp_path, capsys) -> None:
    code, out = _check(tmp_path, capsys, rows=ROWS + [("ca_tsx60", "NA", 11.0, True, 1859)])
    assert code == 1
    assert "ca_tsx60/NA: unexpected new row" in out


def test_a_changed_column_set_fails(golden, tmp_path, capsys) -> None:
    code, out = _check(tmp_path, capsys, extra_column=True)
    assert code == 1
    assert "columns changed" in out and "'note'" in out


def test_snapshot_date_is_not_compared(golden, tmp_path, capsys) -> None:
    assert "snapshot_date" not in pd.read_csv(golden).columns


@pytest.mark.parametrize(
    "value, expected",
    [
        (None, ""),
        (float("nan"), ""),
        (pd.NA, ""),
        (pd.NaT, ""),
        (True, "true"),
        (False, "false"),
        (31.2345678912, "31.2345679"),
        (0.1 + 0.2, "0.3"),
        (1976, "1976"),
        ("Nestlé", "Nestlé"),
    ],
)
def test_cell_rendering(value, expected) -> None:
    assert gate._cell(value) == expected
