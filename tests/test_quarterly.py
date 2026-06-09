"""Tests for quarterly income-statement extraction."""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from ingestion.yfinance.quarterly import (  # noqa: E402
    land_quarterly_ttm_fields,
    quarterly_operating_income_values,
)


def _quarterly_frame(rows: dict[str, list[float]]) -> pd.DataFrame:
    cols = pd.to_datetime(["2025-12-31", "2025-09-30", "2025-06-30", "2025-03-31"])
    return pd.DataFrame(rows, index=cols).T


def test_quarterly_operating_income_uses_ebit_fallback() -> None:
    frame = _quarterly_frame(
        {
            "Total Revenue": [100.0, 90.0, 80.0, 70.0],
            "EBIT": [20.0, 18.0, 16.0, 14.0],
        }
    )
    values = quarterly_operating_income_values(frame)
    assert values == [20.0, 18.0, 16.0, 14.0]


def test_land_quarterly_ttm_fields_includes_operating_revenue_expense() -> None:
    class _Ticker:
        quarterly_income_stmt = _quarterly_frame(
            {
                "Total Revenue": [100.0, 90.0, 80.0, 70.0],
                "Operating Revenue": [50.0, 45.0, 40.0, 35.0],
                "Operating Expense": [30.0, 27.0, 24.0, 21.0],
            }
        )

    fields = land_quarterly_ttm_fields(_Ticker())
    assert fields["qtr_operating_revenue_0"] == 50.0
    assert fields["qtr_operating_expense_0"] == 30.0
