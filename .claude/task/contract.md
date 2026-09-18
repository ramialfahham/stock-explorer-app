# Task contract
> DISPOSABLE. **Owns:** THIS task's objective, `scope_paths`, reserved decisions and
> `done_when`.
> **Never:** anything that outlives the task. Overwritten by the next task.

objective: Move `ticker_overrides.csv` from `ingestion/constituents/` into
  `dbt_analytics/seeds/`, per the owner's direct instruction. Owner observation that
  prompted this: two structurally identical per-ticker correction tables
  (`ticker_overrides.csv`, `company_name_overrides.csv`) lived in different directories
  with different governance -- only `company_name_overrides.csv` was an actual dbt seed
  with schema-enforced `not_null`/`unique` tests; `ticker_overrides.csv` was a bare CSV
  read directly by Python, validated only by ad hoc pytest assertions.

  `dbt_project.yml`'s `seed-paths: ["seeds"]` means dbt auto-discovers every CSV under
  `dbt_analytics/seeds/` as a real seed table the next `dbt build` -- so this move alone
  makes `ticker_overrides` a real dbt seed, loaded into DuckDB, whether or not it is
  documented. Adding a `_seeds.yml` entry (mirroring `company_name_overrides`'s schema +
  tests) closes the exact governance gap the owner pointed out, not just the file's
  address.

  The correction itself keeps applying in Python, before any yfinance fetch
  (`ingestion/constituents/seeds.py`'s `_apply_ticker_overrides`, called from
  `load_constituents()`) -- unchanged. It cannot move into a dbt model: the ticker must be
  corrected before the fetch that dbt's own input depends on, not after. This is a file
  relocation plus real dbt-test governance, not a change to when or how the correction is
  applied.

scope_paths:
  - dbt_analytics/seeds/ticker_overrides.csv (new path)
  - ingestion/constituents/ticker_overrides.csv (removed)
  - dbt_analytics/seeds/_seeds.yml
  - ingestion/paths.py
  - scripts/check_company_names_vs_yfinance.py
  - tests/ingestion/test_market_onboarding.py
  - .claude/task/contract.md
  - .claude/task/review.md

decisions_reserved: none -- the owner gave the exact instruction ("move ticker_overrides.csv
  into dbt_analytics/seeds") after confirming the finding live in chat.

done_when:
  - `ticker_overrides.csv` lives at `dbt_analytics/seeds/ticker_overrides.csv`, gone from
    `ingestion/constituents/`.
  - `dbt_analytics/seeds/_seeds.yml` documents it: column types, `not_null` on all four
    columns, `unique_combination_of_columns` on (market_code, ticker) -- same rigor as
    `company_name_overrides`.
  - `ingestion/paths.py`'s `TICKER_OVERRIDES_PATH` points at the new location; ingestion
    still reads the raw CSV directly (unchanged behavior, just a new path).
  - `dbt seed --project-dir dbt_analytics --profiles-dir .` succeeds and the new seed
    passes its own tests (`dbt test --select ticker_overrides`).
  - `pytest tests/ingestion -q` passes with paths updated, no stale-path assertions left.
  - `python scripts/check_no_em_dash.py` passes.

impact_map: one CSV relocated, one dbt seed schema entry added, one Python path constant,
  one script comment, one test file's path constants. No behavior change to which ticker
  gets corrected or when -- the correction still runs in Python before any fetch.
