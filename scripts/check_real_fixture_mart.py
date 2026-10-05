"""Compare the mart built from the replayed real-shaped fixtures with the committed golden file.

The golden file is `tests/fixtures/real/golden_mart.csv`: every `marts.mart_stock_cards` row
the replay produces, minus the run-dependent `snapshot_date`, floats at 9 significant digits.
Any changed number, flag, name or row fails with a cell-level list. When a change is intended
(a formula, an override, a re-recording), regenerate with `--write` and let the diff of the
golden file show the reviewer exactly which outputs moved.
"""

from __future__ import annotations

import argparse
import math
import sys
from pathlib import Path

import duckdb
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
GOLDEN_PATH = ROOT / "tests" / "fixtures" / "real" / "golden_mart.csv"
KEY = ["market_code", "ticker"]
RUN_DEPENDENT = ["snapshot_date"]
MAX_LISTED = 40


def _cell(value: object) -> str:
    if value is None or value is pd.NA or value is pd.NaT:
        return ""
    if isinstance(value, float) and math.isnan(value):
        return ""
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, float):
        return f"{value:.9g}"
    return str(value)


def mart_frame(duckdb_path: Path) -> pd.DataFrame:
    with duckdb.connect(str(duckdb_path), read_only=True) as con:
        frame = con.execute("select * from marts.mart_stock_cards").fetchdf()
    frame = frame.drop(columns=RUN_DEPENDENT).sort_values(KEY).reset_index(drop=True)
    return frame.astype(object).map(_cell)


def differences(expected: pd.DataFrame, actual: pd.DataFrame) -> list[str]:
    out: list[str] = []
    if list(expected.columns) != list(actual.columns):
        gone = [c for c in expected.columns if c not in actual.columns]
        new = [c for c in actual.columns if c not in expected.columns]
        out.append(f"columns changed: removed {gone}, added {new}")
        return out
    exp = expected.set_index(KEY)
    act = actual.set_index(KEY)
    for key in exp.index.difference(act.index):
        out.append(f"{'/'.join(key)}: row missing")
    for key in act.index.difference(exp.index):
        out.append(f"{'/'.join(key)}: unexpected new row")
    for key in exp.index.intersection(act.index):
        for column in exp.columns:
            if exp.at[key, column] != act.at[key, column]:
                out.append(
                    f"{'/'.join(key)}.{column}: {exp.at[key, column]!r} -> {act.at[key, column]!r}"
                )
    return out


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--duckdb-path", type=Path, required=True)
    parser.add_argument("--write", action="store_true", help="regenerate the golden file")
    args = parser.parse_args(argv)

    actual = mart_frame(args.duckdb_path)
    if args.write:
        actual.to_csv(GOLDEN_PATH, index=False, lineterminator="\n")
        print(f"wrote {len(actual)} rows to {GOLDEN_PATH}")
        return 0

    expected = pd.read_csv(GOLDEN_PATH, dtype=str, keep_default_na=False)
    diffs = differences(expected, actual)
    if not diffs:
        print(f"check_real_fixture_mart: {len(actual)} rows match the golden file.")
        return 0
    print(f"check_real_fixture_mart: {len(diffs)} difference(s) from the golden file:")
    for line in diffs[:MAX_LISTED]:
        print(f"  {line}")
    if len(diffs) > MAX_LISTED:
        print(f"  ... and {len(diffs) - MAX_LISTED} more")
    print("If the change is intended, regenerate: python scripts/check_real_fixture_mart.py "
          "--duckdb-path <db> --write")
    return 1


if __name__ == "__main__":
    sys.exit(main())
