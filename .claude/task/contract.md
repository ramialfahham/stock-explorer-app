# Task contract
> DISPOSABLE. **Owns:** THIS task's objective, `scope_paths`, reserved decisions and
> `done_when`.
> **Never:** anything that outlives the task. Overwritten by the next one.

objective: Remove the Postgres precision caps on `mart_stock_cards` so a Yahoo outlier cannot
  abort the export. Issue #9 finding A2.

  Measured: migration `002` created ten `numeric(10,4)` / `numeric(18,6)` columns; every column
  added since is plain `numeric`. `numeric(10,4)` overflows above 999,999.9999.
  `revenue_growth_yoy_pct` is `info_revenue_growth * 100` straight from Yahoo, so a company
  going from trivial to real revenue produces a value the column cannot hold, and the atomic
  export (one transaction) then writes nothing for that cycle. The dbt contract declares these
  columns `double` and `docs/data_contract.md` lists them as `numeric`; neither mentions a cap.
  The split is historical: only `002`'s columns were capped.

scope_paths:
  - supabase/migrations/019_drop_numeric_precision_caps.sql
  - docs/supabase_setup.md
  - tests/tooling/test_supabase_migrations_schema.py
  - .claude/task/contract.md
  - .claude/task/review.md
  - .claude/active_work.md

decisions_reserved:
  - Removing a cap widens what the table accepts; it changes no shipped number and no
    definition. Agent-executable under the audit's finding, which the owner ordered as next.
  - NOT done here: `accepted_range` tests on the metrics. Their bounds are metric definitions
    (§6) and nothing in the repo states them. Once the caps are gone, the only reason for a
    range test is data sanity, which is a separate question with owner-set bounds.

done_when:
  - `019_drop_numeric_precision_caps.sql` alters every `numeric` column of
    `public.mart_stock_cards` that carries a typmod to plain `numeric`, found from `pg_attribute`
    at run time rather than from a hand-written list, and raises if any remain afterwards.
  - Applied to `--target dev` and verified there over a direct connection: zero capped numeric
    columns; a row with `revenue_growth_yoy_pct = 12345678.9` inserts and reads back.
  - A test in `tests/tooling` asserts that no migration after `002` declares a `numeric(p,s)`,
    `decimal(p,s)` or `dec(p,s)` column, so the cap cannot come back by copy-paste.
  - `docs/supabase_setup.md`'s migration table gains the `019` row.

impact_map: Production schema change, applied by the existing runner on the next scheduled
  run. Ten columns on a table of roughly one row per exported card, so a rewrite costs nothing
  if Postgres does one. Reads are unaffected: the frontend formats through `card_copy.py`, which
  does not depend on column precision.
