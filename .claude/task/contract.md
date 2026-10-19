# Task contract
> DISPOSABLE. **Owner:** THIS task's objective, `scope_paths`, reserved decisions and
> `done_when`.
> **Never:** anything that outlives the task. Overwritten by the next task.

objective: Refs #52 (items 16, 17, 19; item 18 is split out, see decisions_reserved). The dbt mart
  contract (`_marts.yml`, 80 columns), `EXPORT_COLUMNS` in `scripts/export_to_supabase.py` (77) and the
  Postgres table `public.mart_stock_cards` built by `supabase/migrations/*.sql` agree on column names today
  and disagree on one type: `sector_peer_count` is `bigint` in the contract and `integer` in Postgres and in
  `docs/data_contract.md`. Nothing in CI compares them, and nothing checks that the migrations table in
  `docs/supabase_setup.md` lists the files on disk. One rule: every copy is compared by a test that runs in
  CI, and the one disagreement is fixed at the layer that creates the value.

scope_paths:
  - dbt_analytics/models/4_intermediate/int_stock__sector_benchmarks.sql
  - dbt_analytics/models/5_marts/_marts.yml
  - tests/tooling/test_schema_copies_agree.py
  - tests/tooling/test_migration_ledger.py
  - docs/supabase_setup.md
  - docs/data_contract.md
  - docs/context_budget.yml
  - .claude/active_work.md
  - .claude/task/contract.md
  - .claude/task/review.md

decisions_reserved: Answered by the owner in chat. Item 16: cast `sector_peer_count` to `integer` where it is
  born (`count(*)` in `int_stock__sector_benchmarks.sql`, not in the mart and not in base), contract set to
  `integer`; no migration, no production change. Item 18 (run the migrations and `replace_cards_snapshot`
  against a throwaway Postgres in CI): split into its own issue, not built here; it is a new CI mechanism
  with cost and the migrations may not apply on plain Postgres. Items 17 and 19 are plain tests with no new
  mechanism and are built as the issue describes. No change to a shipped number, label, verdict or export
  column.

changes:
  - `int_stock__sector_benchmarks.sql`: `cast(count(*) as integer) as sector_peer_count`; `_marts.yml`:
    `sector_peer_count` `data_type: integer`.
  - `tests/tooling/test_schema_copies_agree.py` (item 17): parses the `mart_stock_cards` columns and
    `data_type` from `_marts.yml`, `EXPORT_COLUMNS`, and the final table definition from the migrations (the
    `create table public.mart_stock_cards` after the last `drop table`, plus every
    `add column if not exists` on it in file order). Asserts: the exported columns are a subset of the mart
    and of the table; the table has exactly the exported columns plus `id` and `exported_at` (a second named
    allowlist, `DATABASE_ONLY`); the only mart columns not exported are a named
    allowlist (`info_ebitda`, `stmt_free_cash_flow`, `stmt_stockholders_equity`, each with its reason); each
    column's contract type maps to its Postgres type (`varchar`-`text`, `double`-`numeric`, `bigint`,
    `integer`, `boolean`, `date`). Self-tests on small inline fixtures prove each assertion fires.
  - `tests/tooling/test_migration_ledger.py` (item 19): the backticked `NNN_*.sql` names in the "Migrations
    on disk" table of `docs/supabase_setup.md` equal the files in `supabase/migrations/`; self-tests on
    fixtures. The prose sentence "Every file in `supabase/migrations/` has a row here." is removed, because
    the test now states it.

done_when:
  - `dbt build` (via `python scripts/bootstrap.py --verify`) passes with the integer cast and contract.
  - Both new test files pass, and each assertion fails when its input is broken (mutation: rename a column
    in a fixture, change a type, drop a ledger row, add an unlisted file).
  - `git grep -n "sector_peer_count" -- docs dbt_analytics/models/5_marts scripts supabase` shows `integer`
    or no type in every place that states one.
  - `pytest tests -q` passes; `docs/context_budget.yml` is unchanged unless `docs/data_contract.md` changes.
  - Item 18 is filed as its own issue and #52's checklist ticks items 16, 17, 19 only.

known_limits:
  - The migration parser reads `create table` and `add column if not exists` on `public.mart_stock_cards`
    and the one generic cap-drop in 019 (numeric stays numeric). A later migration that changes a column in
    another way (rename, drop, retype) is not parsed: the test fails on any `alter column`, `drop column`,
    `rename` or constraint change it sees on a `public.`-qualified `alter table`, and on any DO block that
    mentions the table other than the precision-cap drop of 019, naming the file. Quoted or unqualified
    table names are not read.
  - Types are compared by family, not by precision; `numeric(18,6)` in 002 and plain `numeric` after 019
    both count as `numeric`.

regression_checklist:
  - No exported column, label, verdict or card number changes; the mart column type of `sector_peer_count`
    changes from `bigint` to `integer`, the Postgres column was already `integer`.
  - The existing export tests (`tests/tooling/test_export_to_supabase.py`) and the dbt unit tests pass.
