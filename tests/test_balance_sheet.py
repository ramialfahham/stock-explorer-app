"""Tests for balance-sheet (latest-annual snapshot) extraction."""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from ingestion.yfinance.balance_sheet import (  # noqa: E402
    land_balance_sheet_fields,
    latest_annual_value,
)


def _balance_frame(rows: dict[str, list[float]]) -> pd.DataFrame:
    # Columns are fiscal period-ends (newest first), rows are line labels — the
    # transposed layout yfinance returns for ticker.balance_sheet.
    cols = pd.to_datetime(["2025-12-31", "2024-12-31", "2023-12-31"])
    return pd.DataFrame(rows, index=cols).T


def test_latest_annual_value_picks_most_recent_column() -> None:
    frame = _balance_frame({"Stockholders Equity": [300.0, 250.0, 200.0]})
    assert latest_annual_value(frame, ("Stockholders Equity",)) == 300.0


def test_latest_annual_value_uses_fallback_order() -> None:
    # Primary label absent -> the next fallback label wins.
    frame = _balance_frame({"Common Stock Equity": [180.0, 150.0, 120.0]})
    labels = ("Stockholders Equity", "Common Stock Equity")
    assert latest_annual_value(frame, labels) == 180.0


def test_latest_annual_value_skips_null_to_older_column() -> None:
    # Most recent period is null -> fall back to the newest period with a value.
    frame = _balance_frame({"Total Debt": [float("nan"), 90.0, 80.0]})
    assert latest_annual_value(frame, ("Total Debt",)) == 90.0


def test_latest_annual_value_none_when_absent_or_empty() -> None:
    frame = _balance_frame({"Total Debt": [50.0, 40.0, 30.0]})
    assert latest_annual_value(frame, ("Tangible Book Value",)) is None
    assert latest_annual_value(None, ("Total Debt",)) is None
    assert latest_annual_value(pd.DataFrame(), ("Total Debt",)) is None


def test_land_balance_sheet_fields_operating_company() -> None:
    class _Ticker:
        balance_sheet = _balance_frame(
            {
                "Stockholders Equity": [300.0, 250.0, 200.0],
                "Total Debt": [120.0, 100.0, 90.0],
                "Current Assets": [150.0, 130.0, 110.0],
                "Current Liabilities": [80.0, 70.0, 60.0],
                "Cash And Cash Equivalents": [40.0, 35.0, 30.0],
                "Tangible Book Value": [280.0, 230.0, 180.0],
            }
        )

    fields = land_balance_sheet_fields(_Ticker())
    assert fields["stmt_stockholders_equity"] == 300.0
    assert fields["stmt_total_debt"] == 120.0
    assert fields["stmt_current_assets"] == 150.0
    assert fields["stmt_current_liabilities"] == 80.0
    assert fields["stmt_cash_and_equivalents"] == 40.0
    assert fields["stmt_tangible_book_value"] == 280.0


def test_land_balance_sheet_fields_financial_has_null_current_items() -> None:
    # Banks have no current/non-current split -> current items null, others present.
    # Mirrors the live JPM shape (equity via a fallback label; tangible book < equity).
    class _Ticker:
        balance_sheet = _balance_frame(
            {
                "Common Stock Equity": [360.0, 340.0, 320.0],
                "Total Debt": [500.0, 480.0, 460.0],
                "Cash And Cash Equivalents": [340.0, 300.0, 280.0],
                "Tangible Book Value": [278.0, 260.0, 240.0],
            }
        )

    fields = land_balance_sheet_fields(_Ticker())
    assert fields["stmt_stockholders_equity"] == 360.0
    assert fields["stmt_current_assets"] is None
    assert fields["stmt_current_liabilities"] is None
    assert fields["stmt_tangible_book_value"] == 278.0


def test_land_balance_sheet_fields_missing_balance_sheet() -> None:
    class _Ticker:
        balance_sheet = None

    fields = land_balance_sheet_fields(_Ticker())
    assert set(fields) == {
        "stmt_stockholders_equity",
        "stmt_total_debt",
        "stmt_current_assets",
        "stmt_current_liabilities",
        "stmt_cash_and_equivalents",
        "stmt_tangible_book_value",
    }
    assert all(value is None for value in fields.values())
