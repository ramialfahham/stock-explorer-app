# Task contract
> DISPOSABLE. **Owner:** THIS task's objective, `scope_paths`, reserved decisions and
> `done_when`.
> **Never:** anything that outlives the task. Overwritten by the next task.

objective: Works #76 (HYG-1 defects 54 to 57 and HYG-3 defect 53 of the quality-baseline audit re-run; the owner calls
  58 to 60 stay untouched). Four tracked files nothing runs, and one helper copied into two modules. One rule: a file
  that no CI job, hook, import or runbook command uses is deleted, and one piece of logic has one definition.

scope_paths:
  - ingestion/yfinance/balance_sheet.py
  - ingestion/yfinance/quarterly.py
  - ingestion/yfinance/ingest.py
  - ingestion/__main__.py
  - scripts/backfill_fundamentals_parquet_schema.py
  - .claude/task/hygiene_sweep.py
  - .devcontainer/devcontainer.json
  - .pre-commit-config.yaml
  - docs/operations_guide.md
  - tests/ingestion/test_ingest_resume.py
  - tests/ingestion/test_latest_annual_statement_value.py
  - .claude/active_work.md
  - .claude/task/contract.md
  - .claude/task/review.md

decisions_reserved: Answered by the owner in chat: A, delete all four unused files (the sweep script, the devcontainer,
  the backfill script, `ingestion/__main__.py`) instead of wiring them in. Defect 53 is mechanical (one copy, public
  name). No behaviour, metric, copy or schema change.

changes:
  - `ingestion/yfinance/balance_sheet.py`: `_numeric_columns` becomes the public `numeric_columns`;
    `ingestion/yfinance/quarterly.py` imports it and its own copy is deleted.
  - Deleted: `scripts/backfill_fundamentals_parquet_schema.py`, `.claude/task/hygiene_sweep.py`,
    `.devcontainer/devcontainer.json`, `ingestion/__main__.py`; the `.devcontainer/` exclude and its comment leave
    `.pre-commit-config.yaml`.
  - The backfill script's name leaves `docs/operations_guide.md`, the `_is_fresh_today` docstring in
    `ingestion/yfinance/ingest.py` and the docstring of `test_fundamentals_ignores_a_same_day_write_from_another_script`;
    the wording speaks of the one remaining script, `seed_ci_raw_fixtures.py`.
  - `_latest_annual_statement_value` in `ingestion/yfinance/ingest.py` calls `numeric_columns` instead of its own
    inline loop (newest column first, the same column `max` picked).
  - `tests/ingestion/test_latest_annual_statement_value.py` (new): pins the newest-dated pick, the skip of a null newest
    column, the date and currency, and the empty cases of `_latest_annual_statement_value`, which had no test.
  - `.claude/active_work.md`: current facts.

done_when:
  - `git grep -n -E "backfill_fundamentals_parquet_schema|hygiene_sweep|devcontainer|_numeric_quarter_columns|_numeric_columns"
    -- . ':!.claude/task'` finds nothing.
  - `git grep -n "def numeric_columns"` finds exactly one definition, and `quarterly.py`, `balance_sheet.py` and
    `_latest_annual_statement_value` in `ingest.py` all use it (no inline copy of its filter loop is left).
  - None of the four deleted paths exists in the tree.
  - Mutating `numeric_columns` (sort oldest first) fails tests of both modules (mutation-checked).
  - Picking the oldest column in `_latest_annual_statement_value` fails the new test (mutation-checked).
  - `pytest tests -q` passes; `python scripts/check_context_budget.py` passes; pre-commit passes without the
    `.devcontainer/` exclude.

known_limits:
  - Rules R1 (duplicate functions), R2 (unused scripts), R4 (repeated pins) and R5 of the deleted sweep are checked
    only by the audit re-run from now on; no CI job checks them.

regression_checklist:
  - `scripts/seed_ci_raw_fixtures.py` and its tests are untouched.
  - The ingestion resume and checkpoint behaviour (`_is_fresh_today`) is unchanged; only its docstring is shorter.
