# Task contract
> DISPOSABLE. **Owns:** THIS task's objective, `scope_paths`, reserved decisions and
> `done_when`.
> **Never:** anything that outlives the task. Overwritten by the next task.

objective: Closes #49 (milestone "3 · Professional baseline", dbt standards). The checklist in
  the issue is the source for what and why; this contract holds scope and the checkable "done".

scope_paths:
  - docs/engineering_standards.md
  - dbt_analytics/README.md
  - dbt_analytics/models/1_staging/yfinance/stg_yf__fundamentals.sql
  - dbt_analytics/models/1_staging/yfinance/_yfinance_staging.yml
  - dbt_analytics/models/2_base/yfinance/_yfinance_base.yml
  - dbt_analytics/models/3_core/_core.yml
  - dbt_analytics/models/3_core/fct_fundamentals_snapshot.sql
  - dbt_analytics/models/3_core/dim_stock.sql
  - dbt_analytics/tests/assert_percent_scale_passthroughs.sql
  - dbt_analytics/tests/assert_dividend_yield_suspects.sql
  - dbt_analytics/models/4_intermediate/_intermediate_unit_tests.yml
  - dbt_analytics/models/4_intermediate/int_stock__card_metrics.sql
  - dbt_analytics/seeds/_seeds.yml
  - scripts/check_no_narrative_dates.py
  - tests/tooling/test_check_no_narrative_dates.py
  - docs/quality_criteria.json
  - tests/tooling/test_quality_audit.py
  - .claude/active_work.md
  - .claude/task/contract.md
  - .claude/task/review.md

decisions_reserved: All four answered by the owner in chat. D1 (items 7, 10, 15): amend
  engineering_standards section 1 so names that leave dbt keep their names; rename only the
  internal `stmt_fiscal_period_end`. D2 (item 14): keep `stg_yf__daily_prices`, document it as a
  raw-file check model, amend DBT-3 (criteria v3). D3 (items 12, 13): fix every hit and widen the
  narrative check to dbt `.yml`. D4 (item 11): the uniqueness test stays on `base_yf__fundamentals`
  because it is that model's only model-level test (section 3 and `check_dbt_tests.py` require
  one); section 3 says so. Nothing else is decided here: the optional "one ref per CTE"
  gate extension is not built; no mart, Supabase or frontend name changes.

rules:
  A (naming): section 1 states that the mart names and the columns a mart exposes (including
    `ticker` and `market_code`) are the consumer contract and keep their names; every other name
    follows the table. `stmt_fiscal_period_end` is named `stmt_fiscal_period_end_date` in staging
    and downstream; the raw parquet column keeps its name.
  B (structure): every SQL file under `dbt_analytics/models/` and `dbt_analytics/tests/` has one
    import CTE per ref() and each CTE one purpose (section 1.1); base models do not re-assert a
    uniqueness test staging already asserts on the same grain, unless it is the model's only
    model-level test (section 3).
  C (comments and prose): a `#` or `--` comment in dbt yml/sql states what is true now: no change
    history, no issue/MR reference, no date, no approval marker. A `description:` carries no date
    or approval marker. `check_no_narrative_dates.py` scans dbt `.yml` comments and `description:`
    text for date, MR/PR reference and owner-approved/decision wording.
  D (no dead model): a model nothing reads is allowed only if its description says it exists to
    check raw files; DBT-3 says so.

changes:
  - Items 7, 15: section 1 gets the rule A paragraph; the `dbt_analytics/README.md` layer comment
    for marts matches it.
  - Item 8: `assert_percent_scale_passthroughs.sql` gets import CTEs `fundamentals` and
    `card_metrics`; `metrics` builds the union from those names.
  - Item 9: `dim_stock.sql` gets an import CTE `fundamentals` and a `latest_fundamentals` CTE.
  - Item 10: rename in `stg_yf__fundamentals.sql`, `fct_fundamentals_snapshot.sql` and the three
    yml column entries.
  - Item 11: remove the `unique_combination_of_columns` test from `base_yf__constituents` (it
    keeps its unit tests); keep it on `base_yf__fundamentals`; make the "union" wording true.
  - Item 12 and the same-family hits: rewrite each history comment as one sentence on what the
    test pins now; drop `(issue #N)` from comments.
  - Item 13: delete the dated parenthetical in `_seeds.yml`.
  - Item 14: the description of `stg_yf__daily_prices` says no card reads it and it checks the
    raw price files; `docs/quality_criteria.json` version 3, DBT-3 amended.
  - The narrative check gains `.yml` scanning with tests; handover updated.

done_when:
  - Exact search 1 finds nothing outside the keep list:
    `git grep -nEi "(#|--) .*(\bbefore\b|used to|no longer|the change|headline effect|changed with|issue #|\bMR ?!|\bnow\b|\bold\b|\bformerly\b|\bpreviously\b)" -- 'dbt_analytics/*.yml' 'dbt_analytics/*.sql'`
    Keep list: `_seeds.yml:129` ("before any yfinance" states an ordering that is true now) and
    `int_stock__card_metrics.sql:240` ("since a ..." is not in the pattern; listed only if it
    matches), checked line by line at implementation; any other hit is rewritten.
  - Exact search 2 for the renamed column: `git grep -nw "stmt_fiscal_period_end" -- dbt_analytics docs scripts ingestion`
    hits only raw-column sites. Keep list: `stg_yf__fundamentals.sql` (reads the raw column),
    `dbt_analytics/models/sources.yml`, `docs/data_contract.md` (raw parquet table),
    `scripts/audit_mart_vs_yfinance.py` (raw schema), `ingestion/yfinance/ingest.py`,
    `scripts/seed_ci_raw_fixtures.py`, and the staging yml entry that documents the raw name.
  - Exact search 3: `git grep -nE "owner[- ](approved|decision)|20[0-9]{2}-[0-9]{2}-[0-9]{2}" -- 'dbt_analytics/*.yml'`
    finds only quoted test-data values in `*_unit_tests.yml` (keep list: those files' fixture rows).
  - `python scripts/check_no_narrative_dates.py` passes, and its new test shows it fails on a
    dated `# comment` and a dated `description:` in a temp dbt yml.
  - `pytest tests -q` and `python scripts/bootstrap.py --verify` (dbt build with unit tests)
    pass; mart row counts and the golden mart check are unchanged.
  - No mart, Supabase, export, frontend or ingestion file changes (`git diff --stat` shows none).

known_limits:
  - Exact search 1 is a word heuristic: a history comment worded without those words is not
    caught. The narrative check covers dates, MR/PR references and owner wording only.
  - `(issue #N)` references inside `description:` text and phrases such as "No longer
    catalogued" in descriptions state a current fact and stay.
  - The base models' `deduped` CTEs stay; whether they are still needed is not decided here.
  - `check_dbt_sql_structure.py` is unchanged and cannot see items 8 or 9.
  - Criteria v3 changes DBT-3 only; the other pending criteria edits stay open in the handover.

regression_checklist:
  - Mart schemas, row counts and the golden mart comparison are unchanged.
  - Every dbt model still has at least one model-level test (section 3) after item 11.
  - `check_dbt_documentation.py` (column docs, null-when) still passes for the renamed column.
  - The narrative check still passes on every file it scanned before.
