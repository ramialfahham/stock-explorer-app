# Task contract
> DISPOSABLE. **Owns:** THIS task's objective, `scope_paths`, reserved decisions and
> `done_when`.
> **Never:** anything that outlives the task. Overwritten by the next task.

objective: Closes #42 -- a constituent refresh fails, writing nothing, when the new table keeps
  under 85% of the committed seed's tickers (every market, not only `strip_suffix` ones), and
  onboarding documents `strip_suffix`.

scope_paths:
  - ingestion/constituents/seeds.py
  - ingestion/constituents/refresh.py
  - tests/ingestion/test_constituent_seeds.py
  - tests/ingestion/test_real_fixtures.py
  - docs/data_contract.md
  - docs/operations_guide.md
  - .claude/skills/onboard-market/SKILL.md
  - .claude/active_work.md
  - .claude/task/contract.md
  - .claude/task/review.md
  - .claude/task/review_input.patch

decisions_reserved: settled by the owner in-thread -- option B (one overlap rule for every
  market, replacing the issue's strip_suffix-only check), with (i) no bypass flag: a real
  reshuffle past the threshold means checking the page and replacing the seed by hand. The
  threshold is 85%, shared with the recorded-page test (`MIN_SEED_OVERLAP`). The manual import
  (`import_constituents.py`) is not checked: an import replaces a seed by intent.

done_when:
  - `refresh_market` passes `MIN_SEED_OVERLAP` to `write_constituents`, which raises before
    writing when a committed seed exists and the new tickers keep under that share of it.
  - The threshold is inclusive (17 of 20 passes, 16 fails); no committed seed means no check.
  - The recorded DAX page without `strip_suffix` is refused against the committed seed, and
    the seed is left byte-identical.
  - The activation checklist (step 2) mentions `strip_suffix`; the runbook states the overlap
    failure; the onboard-market skill's `table_index` trap reflects that only a first refresh
    is still silent.

known_limits:
  - A first refresh (no committed seed) is not checked, so a wrong `table_index` at onboarding
    still writes silently.
  - Drift that never removes more than 15% of the seed in one refresh is not caught.
  - A new table that contains the whole seed passes regardless of its size (a wrong
    `table_index` landing on a larger table that includes every committed ticker).

regression_checklist:
  - Every recorded Wikipedia page still parses into its committed seed.
  - The import path writes without an overlap check.
  - A refused refresh leaves the committed seed unchanged.
