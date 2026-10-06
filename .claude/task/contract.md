# Task contract
> DISPOSABLE. **Owns:** THIS task's objective, `scope_paths`, reserved decisions and
> `done_when`.
> **Never:** anything that outlives the task. Overwritten by the next task.

objective: Closes #44 -- override tests check rules that hold for every row of
  `company_name_overrides.csv` and `ticker_overrides.csv`, not per-market copies of rows.

scope_paths:
  - tests/ingestion/test_market_onboarding.py
  - .claude/task/contract.md
  - .claude/task/review.md
  - .claude/task/review_input.patch

decisions_reserved: settled by the owner in-thread (option A): delete the per-market pin
  tests; the CSV and its `reason` column are the record of each decision. Accepted
  trade-off: a correct-looking but unwanted value change is caught by MR review of the CSV
  diff, not by a test.

done_when:
  - The six per-market pin tests and the au_asx200-only end-to-end test are gone.
  - Every row of both override files must have a non-empty `reason`; a blank one fails.
  - For every `ticker_overrides.csv` row, `load_constituents` returns the corrected ticker and
    not the raw one; an override mechanism that stops applying fails.
  - The existing every-row rules (real constituent target, no duplicate keys, override name
    through the scrape-artifact guard) are kept.

known_limits:
  - An unwanted but well-formed value change in either override CSV passes every test.

regression_checklist:
  - Both override CSVs and `ingestion/` are unchanged.
  - The every-row rules still run over all markets, including ones added later.
