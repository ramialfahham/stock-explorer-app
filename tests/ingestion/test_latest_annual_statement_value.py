"""Tests for the latest-annual statement pick that feeds revenue, FCF and margin inputs."""

from __future__ import annotations

from datetime import date

import pandas as pd

from ingestion.yfinance.ingest import _latest_annual_statement_value


def _statement(values: list[float | None], *, currency: str | None = None) -> pd.DataFrame:
    cols = pd.to_datetime(["2023-12-31", "2025-12-31", "2024-12-31"])
    frame = pd.DataFrame({"Total Revenue": values}, index=cols).T
    if currency:
        frame.attrs["currency"] = currency
    return frame


def test_picks_the_newest_dated_column_whatever_the_column_order() -> None:
    frame = _statement([100.0, 300.0, 200.0], currency="USD")

    assert _latest_annual_statement_value(frame, "Total Revenue") == (
        300.0,
        date(2025, 12, 31),
        "USD",
    )


def test_skips_a_null_newest_column_to_the_next_newest_dated_one() -> None:
    frame = _statement([100.0, None, 200.0])

    assert _latest_annual_statement_value(frame, "Total Revenue") == (200.0, date(2024, 12, 31), None)


def test_returns_nothing_for_a_missing_label_an_all_null_row_or_no_statement() -> None:
    nothing = (None, None, None)

    assert _latest_annual_statement_value(_statement([1.0, 2.0, 3.0]), "Net Income") == nothing
    assert _latest_annual_statement_value(_statement([None, None, None]), "Total Revenue") == nothing
    assert _latest_annual_statement_value(None, "Total Revenue") == nothing
