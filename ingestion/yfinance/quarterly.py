"""Extract raw quarterly income-statement values from yfinance frames."""

from __future__ import annotations

from typing import Any

import pandas as pd

OPERATING_INCOME_ROW = "Operating Income"
TOTAL_REVENUE_ROW = "Total Revenue"
OPERATING_REVENUE_ROW = "Operating Revenue"
OPERATING_EXPENSE_ROW = "Operating Expense"
TTM_QUARTERS = 4

# Yahoo alternate GAAP labels for operating profit (intl / banks). Order matters.
OPERATING_INCOME_FALLBACK_ROWS: tuple[str, ...] = (
    OPERATING_INCOME_ROW,
    "Total Operating Income As Reported",
    "Operating Profit",
    "EBIT",
)


def _numeric_quarter_columns(row: pd.Series) -> list[object]:
    cols: list[object] = []
    for col in row.index:
        try:
            val = row[col]
            if val is not None and not (isinstance(val, float) and pd.isna(val)):
                cols.append(col)
        except (TypeError, ValueError):
            continue
    cols.sort(key=lambda c: pd.Timestamp(c), reverse=True)
    return cols


def quarterly_row_values(
    statement: pd.DataFrame | None,
    row_label: str,
    *,
    quarters: int = TTM_QUARTERS,
) -> list[float | None]:
    """Return up to `quarters` values, index 0 = most recent quarter."""
    if statement is None or statement.empty or row_label not in statement.index:
        return [None] * quarters

    row = statement.loc[row_label]
    ordered_cols = _numeric_quarter_columns(row)
    values: list[float | None] = []
    for col in ordered_cols[:quarters]:
        raw = row[col]
        if raw is None or (isinstance(raw, float) and pd.isna(raw)):
            values.append(None)
        else:
            values.append(float(raw))
    while len(values) < quarters:
        values.append(None)
    return values


def quarterly_operating_income_values(
    statement: pd.DataFrame | None,
    *,
    quarters: int = TTM_QUARTERS,
) -> list[float | None]:
    """Fill each quarter from the first available operating-profit row label."""
    values: list[float | None] = [None] * quarters
    if statement is None or statement.empty:
        return values

    for label in OPERATING_INCOME_FALLBACK_ROWS:
        candidates = quarterly_row_values(statement, label, quarters=quarters)
        for idx in range(quarters):
            if values[idx] is None and candidates[idx] is not None:
                values[idx] = candidates[idx]
    return values


def quarterly_income_statement(ticker: Any) -> pd.DataFrame | None:
    """Prefer quarterly_income_stmt; fall back to quarterly_financials."""
    frame = ticker.quarterly_income_stmt
    if frame is not None and not frame.empty:
        return frame
    frame = ticker.quarterly_financials
    if frame is not None and not frame.empty:
        return frame
    return None


def land_quarterly_ttm_fields(ticker: Any) -> dict[str, float | None]:
    """Land raw quarterly scalars for TTM operating margin (no ratio in Python)."""
    income = quarterly_income_statement(ticker)
    op_values = quarterly_operating_income_values(income)
    rev_values = quarterly_row_values(income, TOTAL_REVENUE_ROW)
    op_rev_values = quarterly_row_values(income, OPERATING_REVENUE_ROW)
    op_exp_values = quarterly_row_values(income, OPERATING_EXPENSE_ROW)
    out: dict[str, float | None] = {}
    for idx in range(TTM_QUARTERS):
        out[f"qtr_operating_income_{idx}"] = op_values[idx]
        out[f"qtr_total_revenue_{idx}"] = rev_values[idx]
        out[f"qtr_operating_revenue_{idx}"] = op_rev_values[idx]
        out[f"qtr_operating_expense_{idx}"] = op_exp_values[idx]
    return out
