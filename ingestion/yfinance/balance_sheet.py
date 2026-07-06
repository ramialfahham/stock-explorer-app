"""Extract latest-annual balance-sheet snapshot values from yfinance frames.

The balance sheet is point-in-time (a stock, not a flow), so — unlike the quarterly
income-statement TTM machinery in ``quarterly.py`` — we take the latest annual column
only, with no summing across periods. yfinance normalises row labels to a fixed key set
(camel2title of its balance-sheet keys), so a single canonical label per line is consistent
across markets (the probe confirms ~100% coverage without market-specific variants). The
ordered-fallback tuple (mirror of ``quarterly.OPERATING_INCOME_FALLBACK_ROWS``) is kept for
the one line with a genuine alternate — equity (``Stockholders Equity`` vs ``Common Stock
Equity``). Per-market coverage is recorded in ``docs/intl-balance-sheet-row-labels.md``
(from ``probe_balance_sheet_labels.py``).

Raw scalars only — no ratios are computed here (that is dbt's job).
"""

from __future__ import annotations

from typing import Any

import pandas as pd

# Row labels per balance-sheet line. yfinance canonicalises these to a fixed key set, so
# most lines have a single canonical label; only equity has a genuine second fallback
# (order matters — the first present label with a value wins).
STOCKHOLDERS_EQUITY_FALLBACK_ROWS: tuple[str, ...] = (
    # Common shareholders' equity (attributable to the parent). Deliberately NOT
    # "Total Equity Gross Minority Interest", which folds in non-controlling
    # interest and would overstate common equity / understate debt-to-equity.
    "Stockholders Equity",
    "Common Stock Equity",
)
# yfinance canonicalises these lines, so one label each resolves across markets
# (probe: ~100% coverage). Single-element tuples are intentional, not oversights.
TOTAL_DEBT_FALLBACK_ROWS: tuple[str, ...] = (
    "Total Debt",
)
CURRENT_ASSETS_FALLBACK_ROWS: tuple[str, ...] = (
    "Current Assets",
)
CURRENT_LIABILITIES_FALLBACK_ROWS: tuple[str, ...] = (
    "Current Liabilities",
)
# Narrow cash only — deliberately NOT "Cash Cash Equivalents And Short Term Investments",
# which folds in marketable investments and would inflate a downstream net-cash figure.
CASH_AND_EQUIVALENTS_FALLBACK_ROWS: tuple[str, ...] = (
    "Cash And Cash Equivalents",
)
TANGIBLE_BOOK_VALUE_FALLBACK_ROWS: tuple[str, ...] = (
    "Tangible Book Value",
)

# Raw field name -> ordered fallback labels. Field names carry the ``stmt_`` prefix
# (statement-sourced) and are distinct from the ``info_*`` scalar passthroughs.
BALANCE_SHEET_FIELDS: dict[str, tuple[str, ...]] = {
    "stmt_stockholders_equity": STOCKHOLDERS_EQUITY_FALLBACK_ROWS,
    "stmt_total_debt": TOTAL_DEBT_FALLBACK_ROWS,
    "stmt_current_assets": CURRENT_ASSETS_FALLBACK_ROWS,
    "stmt_current_liabilities": CURRENT_LIABILITIES_FALLBACK_ROWS,
    "stmt_cash_and_equivalents": CASH_AND_EQUIVALENTS_FALLBACK_ROWS,
    "stmt_tangible_book_value": TANGIBLE_BOOK_VALUE_FALLBACK_ROWS,
}


def _numeric_columns(row: pd.Series) -> list[object]:
    """Dated columns that hold a usable (non-null) numeric value, newest first."""
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


def latest_annual_value(
    statement: pd.DataFrame | None,
    labels: tuple[str, ...],
) -> float | None:
    """Latest-annual value for the first fallback label that has one.

    Point-in-time: pick the most recent dated column with a value for that label.
    """
    if statement is None or statement.empty:
        return None
    for label in labels:
        if label not in statement.index:
            continue
        ordered_cols = _numeric_columns(statement.loc[label])
        if not ordered_cols:
            continue
        raw = statement.loc[label][ordered_cols[0]]
        if raw is None or (isinstance(raw, float) and pd.isna(raw)):
            continue
        return float(raw)
    return None


def land_balance_sheet_fields(ticker: Any) -> dict[str, float | None]:
    """Land latest-annual balance-sheet scalars (no ratios; dbt computes those)."""
    balance = getattr(ticker, "balance_sheet", None)
    return {
        field: latest_annual_value(balance, labels)
        for field, labels in BALANCE_SHEET_FIELDS.items()
    }
