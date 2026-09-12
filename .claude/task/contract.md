# Task contract
> DISPOSABLE. **Owns:** THIS task's objective, `scope_paths`, reserved decisions and
> `done_when`.
> **Never:** anything that outlives the task. Overwritten by the next one.

objective: Normalise fraction-scale `dividendYield` rows to percent on read, count the
  suspects every run, and stop six descriptions stating the percent convention as
  unconditional. Issue #10.

  Measured on production, latest snapshot per ticker, 910 cards with a yield: five rows sit
  below 0.05 (0.0036, 0.0216, 0.0387, 0.0426, 0.0468), all with four significant decimals
  where Yahoo's genuine percent values carry two; the next value up is 0.06. No real yield
  sits below 0.05%, so the boundary separates the two populations on today's data.

scope_paths:
  - dbt_analytics/models/4_intermediate/int_stock__card_metrics.sql
  - dbt_analytics/models/4_intermediate/_intermediate.yml
  - dbt_analytics/models/sources.yml
  - dbt_analytics/models/1_staging/yfinance/_yfinance_staging.yml
  - dbt_analytics/models/2_base/yfinance/_yfinance_base.yml
  - dbt_analytics/models/3_core/_core.yml
  - dbt_analytics/models/5_marts/_marts.yml
  - dbt_analytics/tests/assert_dividend_yield_suspects.sql
  - dbt_analytics/tests/_tests.yml
  - dbt_analytics/tests/assert_percent_scale_passthroughs.sql
  - docs/data_contract.md
  - docs/context_budget.yml
  - .claude/task/contract.md
  - .claude/task/review.md
  - .claude/active_work.md

decisions_reserved:
  - Correct on read, reject, or leave: owner chose correct on read, at the 0.05 boundary.
    Below it the value is multiplied by 100; at or above it passes through. That is a
    definition change for `dividend_yield_pct` and is written into `docs/data_contract.md`,
    with its two known failure modes named: a genuine sub-0.05% yield would be scaled up, and
    a fraction-scale row for a 5%+ payer would pass through 100x too small. Neither exists in
    the data the rule was set on.
  - The raw column is untouched: staging, base and core carry Yahoo's value as it arrives.
  - The wholesale-flip guard for this metric now reads the raw value, not the corrected one,
    so it still fails the build on a provider units flip; the correction would otherwise have
    absorbed the flip for every yield under 5%. Not a new mechanism: the same test, pointed at
    the column it needs.
  - NOT done, a follow-up if the owner wants it: a stronger per-row discriminator. The five
    fraction rows carry four significant decimals where Yahoo's percent values carry two;
    a decimals rule would catch a fraction row at any yield but would mis-scale a genuine
    percent that ever arrived with four decimals. Definition territory (§6).

done_when:
  - `int_stock__card_metrics` applies the rule; a dbt unit test feeds 0.0387 and 3.5 and
    expects 3.87 and 3.5.
  - A singular test at `severity: warn` lists every row whose raw `info_dividend_yield` is
    below 0.05, so each run counts the suspects; the CI fixtures raise no warning.
  - The six descriptions and `docs/data_contract.md` state the rule; the eight stale "not in
    the Supabase export" claims in `_intermediate.yml` for columns that are exported are
    corrected to each column's real status.
  - The percent-scale guard reads the raw dividend value; a simulated wholesale flip on the
    built fact table fails it.
  - `dbt build` green locally; `check_dbt_tests.py`, `check_dbt_sql_structure.py`, sqlfluff.

impact_map: `docs/data_contract.md`'s budget rises from 58,000 to 59,000 bytes: the file was
  210 bytes under its budget at HEAD and this rule, its failure modes and the guard note are
  contract text that belongs there (net +601 bytes after tightening). Five production rows
  change value on the next scheduled run (x100). The column
  is exported and stored but rendered nowhere and read by no eligibility or verdict rule, so
  no card changes. The percent-scale guard's median band is unaffected.
