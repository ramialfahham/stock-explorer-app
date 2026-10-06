# Task contract
> DISPOSABLE. **Owns:** THIS task's objective, `scope_paths`, reserved decisions and
> `done_when`.
> **Never:** anything that outlives the task. Overwritten by the next task.

objective: Closes #37 -- the headline override pins check each (ticker, company_name) pair,
  and the override-target test's docstring describes how it reads the seed.

scope_paths:
  - tests/ingestion/test_market_onboarding.py
  - .claude/task/contract.md
  - .claude/task/review.md
  - .claude/task/review_input.patch

decisions_reserved: none open. Owner approved in-thread: the pinned names are the current
  values of `dbt_analytics/seeds/company_name_overrides.csv` (the approved headlines); no
  override or output change.

done_when:
  - The Nikkei, SMI and Nordic pin tests compare ticker -> company_name maps, matching the
    committed override CSV exactly.
  - Changing one pinned name (e.g. "Nordea" to "Nordea Bank Abp") fails its pin.
  - `test_company_name_overrides_target_real_constituents`'s docstring says it reads the seed
    through `load_constituents`, which applies `ticker_overrides.csv`.

known_limits: none.

regression_checklist:
  - The pins still fail when a row is added or removed.
  - `company_name_overrides.csv` is unchanged.
