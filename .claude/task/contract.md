# Task contract
> DISPOSABLE. **Owns:** THIS task's objective, `scope_paths`, reserved decisions and
> `done_when`.
> **Never:** anything that outlives the task. Overwritten by the next one.

objective: Fail the build when a raw parquet's `market_code` column disagrees with the folder
  it sits in. Issue #9 finding C4.

  Measured: `raw_parquet_union` loops `active_market_codes` to build file paths and reads every
  column, `market_code` included, from the file. Ingestion writes the column and the folder
  from the same `market.market_code`, so they agree unless a file is copied or restored by hand.
  Nothing checks it: no `accepted_values` on `market_code` in any layer, no comparison to the
  folder. A file under `ch_smi/` carrying `nl_aex` rows partitions them into `nl_aex`.

scope_paths:
  - dbt_analytics/macros/raw_parquet_partition.sql
  - dbt_analytics/tests/assert_raw_market_code_matches_folder.sql
  - .claude/task/contract.md
  - .claude/task/review.md
  - .claude/active_work.md

decisions_reserved:
  - Test, not override. Making the folder authoritative (`'{{ market }}' as market_code` in the
    union) would silently relabel a misplaced file's rows; that is a behaviour change and the
    owner's call. A test that fails the build changes nothing about what a correct file
    produces. Agent-executable under the audit finding the owner ordered.

done_when:
  - A singular test reads each active market's three raw files under their folder and returns
    every row whose `market_code` differs from the folder name. Swapping one market's
    `yf_constituents.parquet` for another's fails it; the stored tree passes.
  - `check_dbt_sql_structure.py` accepts the test (§1.1 shape).

impact_map: A new dbt test node; no model, export or schema change. A hand-copied raw file now
  fails `dbt build` instead of landing in the wrong market.
