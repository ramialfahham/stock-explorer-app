# Task contract
> DISPOSABLE. **Owns:** THIS task's objective, `scope_paths`, reserved decisions and
> `done_when`.
> **Never:** anything that outlives the task. Overwritten by the next task.

objective: Closes #36 -- constituent ingestion reads the ticker `NA` safely everywhere,
  reports the rows it wrote, and refuses a kept row without a company name.

scope_paths:
  - ingestion/constituents/seeds.py
  - ingestion/constituents/refresh.py
  - scripts/import_constituents.py
  - tests/ingestion/test_constituent_seeds.py
  - tests/ingestion/test_real_fixtures.py
  - tests/tooling/test_import_constituents.py
  - .claude/task/contract.md
  - .claude/task/review.md
  - .claude/task/review_input.patch

decisions_reserved: none open. Owner approved the plan in-thread: `write_constituents` returns
  the written row count (not the path) and raises before writing when a kept row has no
  company name; refresh and import both go through it. Issue item 5 (override test resolves
  through `ticker_overrides`) is already on main (f01c6df); no change.

done_when:
  - `scripts/import_constituents.py` and `_load_ticker_overrides` read with `na_filter=False`;
    an `NA` ticker survives an import and an override keyed on `NA` matches.
  - `refresh_market` returns the rows written: ca_tsx60's recorded page returns 60, not 61.
  - A kept row with an empty, blank or null company name raises and writes no seed; the
    import script exits 1 on it.
  - Offline tests over the recorded OBX and TSX 60 pages pin the `OSE: ` prefix strip, the
    dropped footer row and the kept `NA`.

known_limits: none.

regression_checklist:
  - Every recorded Wikipedia page still parses into its committed seed.
  - A missing ticker is still dropped, never written as "nan".
  - A row dropped for its ticker is never reported as an unnamed row.
