"""coerce_cell is the one cell conversion the Supabase export and the assessment generator share."""

from __future__ import annotations

from datetime import date

import numpy as np
import pandas as pd

from export_to_supabase import coerce_cell


def test_missing_values_become_none() -> None:
    assert coerce_cell(None) is None
    assert coerce_cell(float("nan")) is None
    assert coerce_cell(pd.NA) is None
    assert coerce_cell(pd.NaT) is None


def test_dates_become_iso_strings() -> None:
    assert coerce_cell(date(2026, 5, 1)) == "2026-05-01"
    assert coerce_cell(pd.Timestamp("2026-05-01")) == "2026-05-01T00:00:00"


def test_numpy_scalars_become_python_scalars() -> None:
    whole = coerce_cell(np.int64(7))
    fraction = coerce_cell(np.float64(1.5))

    assert whole == 7 and type(whole) is int
    assert fraction == 1.5 and type(fraction) is float


def test_other_values_pass_through() -> None:
    assert coerce_cell("Technology") == "Technology"
    assert coerce_cell(0) == 0
