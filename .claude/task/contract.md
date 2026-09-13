# Task contract
> DISPOSABLE. **Owns:** THIS task's objective, `scope_paths`, reserved decisions and
> `done_when`.
> **Never:** anything that outlives the task. Overwritten by the next task.

objective: `scripts/sync_dbt_vars.py` prints "already in sync" and exits 0 when
  `dbt_project.yml` has no `active_market_codes` block to rewrite. Issue #8. A missing block
  is a failure: say so on stderr, exit 1.

scope_paths:
  - scripts/sync_dbt_vars.py
  - tests/tooling/test_sync_dbt_vars.py
  - .claude/task/contract.md
  - .claude/task/review.md
  - .claude/active_work.md

decisions_reserved:
  - None. The two gates that already catch the resulting state (`check_registry_var_sync.py`
    in CI, `test_dbt_active_markets_match_the_registry`) are untouched; this fixes what the
    operator is told.

done_when:
  - `_update_dbt_project` raises `BlockNotFound` instead of returning False for a missing
    block; `main` prints the reason on stderr and returns 1; nothing is written.
  - Tests: missing block gives exit 1, stderr names the block, stdout never says "already in
    sync", the file is untouched; an out-of-sync block is rewritten with exit 0; an in-sync
    block is left alone with exit 0. The first test fails against HEAD's script.
  - `pytest tests/ -q` green.

impact_map: One script's exit status on one error path; `docs/data_contract.md`'s activation
  checklist step 3 still holds (the script reads `ingest_active` and writes `dbt_project.yml`).
