# Review

diff_sha256: 069a41abd2139cfbf1b48b3a284395c6177786fbb7124eb6875e62a684d5b562
rounds: 2

Works #76 (HYG-1 defects 54 to 57, HYG-3 defect 53; the owner calls 58 to 60 are untouched). Owner answer A: delete the
four unused files (`scripts/backfill_fundamentals_parquet_schema.py`, `.claude/task/hygiene_sweep.py`,
`.devcontainer/devcontainer.json`, `ingestion/__main__.py`) and the `.devcontainer/` exclude of the `check-json` hook.
Defect 53: one `numeric_columns` in `ingestion/yfinance/balance_sheet.py`, used by `quarterly.py`. Round 1 (tree
4182c0f): all three reviewers PASS; two of them named the same contract wording fix (the `done_when` search matched the
contract itself, now `-- . ':!.claude/task'`), and the data-engineer named a third inline copy of the same filter loop in
`_latest_annual_statement_value` (`ingest.py`), which had no test. Round 2 (tree 9f0f773): that function now calls
`numeric_columns`, and the new `tests/ingestion/test_latest_annual_statement_value.py` pins it; all three PASS on the
delta.

Coordinator evidence:
- `pytest tests` 1485 passed, 1 skipped; `check_context_budget.py` passes.
- Mutations, file restored after each: `numeric_columns` sorted oldest first fails 7 of the 9 tests of
  `test_quarterly.py` and `test_balance_sheet.py`; picking `numeric_cols[-1]` in `_latest_annual_statement_value` fails 2
  of the 3 new tests (before the new test existed the same mutation left all 1482 tests green).
- The done_when searches: no `backfill_fundamentals_parquet_schema`, `hygiene_sweep`, `devcontainer`,
  `_numeric_quarter_columns` or `_numeric_columns` outside `.claude/task`; one `def numeric_columns`.

follow_ups: the `try/except` around `pd.Timestamp(latest_col).date()` in `_latest_annual_statement_value` cannot fire
any more (`numeric_columns` already converted that label); a `NaT` column label could order differently under `sort`
than under `max` (yfinance emits none); no CI job checks rules R1, R2, R4 and R5 of the deleted sweep (known limit in
the contract).

## scope-auditor

VERDICT: PASS
reviewed_tree: 9f0f773751d8a34a2ed0220812a62da38a5b506d
risks_checked:
- Every path of the diff is in `scope_paths`; no new mechanism; the owner's answer A is the only decision and is recorded.
- One definition of `numeric_columns` with three callers; ties and unconvertible labels behave as before (`max` and a stable reverse sort pick the same column).
wording_fixes: none.

## platform-reviewer

VERDICT: PASS
reviewed_tree: 9f0f773751d8a34a2ed0220812a62da38a5b506d
risks_checked:
- No CI job, hook, script, doc or `review_routing.json` entry still depends on a deleted file; every remaining tracked `.json` file parses under strict `check-json`.
- The new test is collected by `pytest tests/`, makes no network call and follows its neighbours' layout.
wording_fixes: none.

## data-engineer-reviewer

VERDICT: PASS
reviewed_tree: 9f0f773751d8a34a2ed0220812a62da38a5b506d
risks_checked:
- `quarterly_row_values`, `latest_annual_value` and `_latest_annual_statement_value` return exactly what they returned before; no import cycle.
- The `_is_fresh_today` docstring and `docs/operations_guide.md` still describe the checkpoint correctly with only `seed_ci_raw_fixtures.py` left; the deleted backfill has no job left (a column mismatch refetches every ticker).
wording_fixes: none.
