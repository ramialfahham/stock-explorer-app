# Task contract
> DISPOSABLE. **Owns:** THIS task's objective, `scope_paths`, reserved decisions and
> `done_when`.
> **Never:** anything that outlives the task. Overwritten by the next one.

objective: Test the grain the mart actually has. Issue #9 finding C3.

  Measured: `fct_fundamentals_snapshot` keeps the latest `snapshot_date` per `(market_code,
  ticker)` with one `qualify`, and nothing downstream reintroduces history, so
  `int_stock__card_metrics` and both marts hold one row per `(market_code, ticker)` per build.
  They are documented and tested at `(market_code, ticker, snapshot_date)`, the grain of the
  accumulating Postgres table. Raw parquet is overwritten each run and carries one
  `snapshot_date`, so the fact's own `(market_code, ticker)` test never sees a second date and
  the `qualify` is exercised by nothing: deleting it passes every test on the data CI has.

scope_paths:
  - dbt_analytics/models/3_core/_core.yml
  - dbt_analytics/models/3_core/_core_unit_tests.yml
  - dbt_analytics/models/4_intermediate/_intermediate.yml
  - dbt_analytics/models/5_marts/_marts.yml
  - docs/data_contract.md
  - tests/tooling/test_export_to_supabase.py
  - .claude/task/contract.md
  - .claude/task/review.md
  - .claude/active_work.md

decisions_reserved:
  - None. The models already behave this way and the fact's description says so; the change
    makes the tests and the model descriptions match the behaviour. The Supabase table's grain
    in `docs/data_contract.md` stays `(market_code, ticker, snapshot_date)`: that describes the
    table, which accumulates, and is correct.

done_when:
  - A dbt unit test on `fct_fundamentals_snapshot` feeds two rows for one ticker with different
    `snapshot_date`s and expects only the later one. Deleting the `qualify` fails it.
  - `int_stock__card_metrics`, `mart_stock_cards` and `mart_stock_eligibility_gaps` carry a
    `unique_combination_of_columns` on `(market_code, ticker)`, and their `Grain:` lines say so.
  - `dbt build` green locally on the stored raw data with the tightened tests.

impact_map: Tests and descriptions only. No model SQL, no export, no schema. Markets can sit
  on different dates after a per-market re-run; that stays legal, since the grain is per
  ticker, not per build.
