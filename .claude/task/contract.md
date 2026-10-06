# Task contract
> DISPOSABLE. **Owns:** THIS task's objective, `scope_paths`, reserved decisions and
> `done_when`.
> **Never:** anything that outlives the task. Overwritten by the next task.

objective: Closes #34 -- `refresh_yfinance_names.py --market <code>` keeps every other
  market's rows in `ingestion/constituents/yfinance_name_snapshot.csv`.

scope_paths:
  - scripts/refresh_yfinance_names.py
  - tests/tooling/test_refresh_yfinance_names.py
  - .claude/active_work.md
  - .claude/task/contract.md
  - .claude/task/review.md
  - .claude/task/review_input.patch

decisions_reserved: none open. Owner approved the plan in-thread: merge only when `--market`
  is given; a run without it stays a full rewrite; "refreshed" means the filtered target
  list (active, provider:wikipedia), not the raw `--market` values.

done_when:
  - With `--market`, rows for markets not refreshed are written back unchanged; the
    refreshed markets' rows are replaced.
  - A test proves it and fails against the pre-fix script.
  - A run without `--market` still rewrites the whole snapshot.
  - `.claude/active_work.md` no longer lists #39 as in flight.

known_limits:
  - A ticker whose fetch fails during a `--market` run loses its row, the same as in a full
    refresh.

regression_checklist:
  - A run without `--market` still prunes rows of markets no longer refreshed.
  - The committed snapshot file is not touched by the tests.
