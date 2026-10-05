# Task contract
> DISPOSABLE. **Owns:** THIS task's objective, `scope_paths`, reserved decisions and
> `done_when`.
> **Never:** anything that outlives the task. Overwritten by the next task.

objective: Closes #38 -- the dotted class shares BRK.B, BF.B (us_sp500) and BT.A (uk_ftse100)
  resolve to Yahoo's symbols, so the three companies get fundamentals and cards.

scope_paths:
  - dbt_analytics/seeds/ticker_overrides.csv
  - ingestion/constituents/yfinance_name_snapshot.csv
  - tests/ingestion/test_market_onboarding.py
  - tests/tooling/test_record_ingestion_fixtures.py
  - scripts/record_ingestion_fixtures.py
  - tests/fixtures/real/
  - docs/operations_guide.md
  - .claude/active_work.md
  - .claude/task/contract.md
  - .claude/task/review.md
  - .claude/task/review_input.patch

decisions_reserved: settled by the owner in-thread before implementation --
  Fix (option B): three `ticker_overrides.csv` rows (BRK.B -> BRK-B, BF.B -> BF-B,
  BT.A -> BT-A.L), the mechanism already used for the Canadian class shares; no code change in
  `ingestion/yfinance/symbols.py`. Cards show the Yahoo form. A guard test fails CI on any
  future dotted ticker that is not an exchange suffix.

known_limits: none.

regression_checklist:
  - No other market's tickers, overrides or name-snapshot rows change.
  - The golden mart changes only by the new cards and what they move (sector peer counts).
  - The synthetic CI fixtures and every `validate:full` step still pass.

done_when:
  - The three overrides exist and are pinned; `test_no_symbol_carries_a_dot_that_is_not_an_
    exchange_suffix` fails without them and passes with them.
  - Only Berkshire and BT are re-recorded (`record_ingestion_fixtures.py --ticker`, which keeps
    every other recording); the golden diff is the two new cards and JPM's sector peer count.
  - `pytest tests` passes; review cycle run; MR opened. Not merged.

amendments:
  - Round 1: analytics-engineer, data-engineer and scope-auditor PASS; platform FAIL
    [broken-guarantee]: the recorder's `--ticker` mode was untested. Fixed:
    `tests/tooling/test_record_ingestion_fixtures.py` (only the named ticker replaced, other
    JSON and price rows kept, stale JSON removed, nothing touched when the network fails,
    single-symbol download frame, manifest update, ambiguous arguments rejected). The
    re-record now finishes every network call before writing; `--ticker` with `--market` is an
    error. Wording fixes applied; the US/UK pin asserts a subset. Follow-ups filed.
