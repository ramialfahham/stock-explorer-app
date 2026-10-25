# Task contract
> DISPOSABLE. **Owner:** THIS task's objective, `scope_paths`, reserved decisions and
> `done_when`.
> **Never:** anything that outlives the task. Overwritten by the next task.

objective: Works #72 (the four dbt defects of the quality-baseline audit re-run; items 14, 16, 18, 19 are owner
  calls and stay untouched). `dim_stock` fails the Reuse condition of `docs/layering.md` and carries `sector`
  and `currency` that the fact table already has, so two `coalesce` calls in `int_stock__card_metrics` can never
  change a value; the `dim_stock` and `int_stock__card_metrics` "Used by" lines are wrong; three descriptions
  say "each at its market's latest snapshot_date" while the model keeps each ticker's own latest snapshot; and
  `docs/engineering_standards.md` section 1.2 says "no multi-line comment blocks" while 13 of the 14 two-line
  comment blocks in the dbt SQL are one sentence wrapped. One rule over every case: a description states what the
  code does, a rule says what the code already is, and a documented claim that a tool can check is checked.

scope_paths:
  - dbt_analytics/models/3_core/dim_stock.sql
  - dbt_analytics/models/3_core/_core.yml
  - dbt_analytics/models/4_intermediate/int_stock__card_metrics.sql
  - dbt_analytics/models/4_intermediate/_intermediate.yml
  - dbt_analytics/models/4_intermediate/_intermediate_unit_tests.yml
  - dbt_analytics/models/5_marts/_marts.yml
  - dbt_analytics/tests/assert_dividend_yield_suspects.sql
  - docs/layering.md
  - docs/engineering_standards.md
  - docs/data_contract.md
  - scripts/check_dbt_documentation.py
  - tests/tooling/test_check_dbt_documentation.py
  - .claude/active_work.md
  - .claude/task/contract.md
  - .claude/task/review.md

decisions_reserved: Answered by the owner in chat. Defect 10: keep `dim_stock` (A); amend the Reuse condition of
  `docs/layering.md` so a single-consumer entity table that is the one place an entity's key and display name are
  resolved may be a dimension, and drop the redundant `sector` and `currency` from it and the two coalesces.
  Defect 11: correct both "Used by" lines AND extend `scripts/check_dbt_documentation.py` to compare every
  model's "Used by" line with the models that depend on it (B). Defect 12: the descriptions follow the code, "each
  at its latest snapshot_date" (A); no filter is added. Defect 13: section 1.2 is reworded so one sentence may
  wrap (A), and a comment with two full sentences is cut to one. The owner-call items 14, 16, 18, 19 are not
  touched. No change to a mart column, a card number or an export column.

changes:
  - Defect 10: `dim_stock.sql` keeps `market_code`, `ticker`, `company_name` (seed name over yfinance
    `longName`); `sector` and `currency` leave it and its `_core.yml` block. `int_stock__card_metrics.sql` uses
    `s.info_sector` and `s.info_currency` directly and still joins `stocks` for `company_name`. The 19 unit-test
    `dim_stock` inputs lose `sector` and `currency`. Every description and comment that mentions
    `coalesce(info_sector, dim_stock.sector)` or "dim_stock has no sector" is restated (`_intermediate.yml`,
    `_marts.yml`, `_core.yml`, `docs/data_contract.md`). `docs/layering.md` condition 2 becomes: "Reuse. Its
    attributes are shared across more than one fact or mart, or it is a single-consumer entity table that is the
    one place where an entity's key and display name are resolved."
  - Defect 11: "Used by" of `dim_stock` (`int_stock__card_metrics` only) and `int_stock__card_metrics` (adds
    `mart_stock_eligibility_gaps`). New `check_used_by_matches_dependencies(manifest, errors)` in
    `scripts/check_dbt_documentation.py`: for each project model whose description has a `**Used by:**`
    line, the model names in that line must equal the project models that depend on it; models without the line
    (staging, base) are skipped; non-model consumers named in the line are ignored. Called from `main()`.
  - Defect 12: the grain lines in `_intermediate.yml` and `_marts.yml` (`mart_stock_cards`), and the sentence in
    `docs/data_contract.md` about the dbt model's grain, say "each at its latest snapshot_date".
  - Defect 13: `docs/engineering_standards.md` section 1.2: "One sentence per comment, which may wrap onto more
    than one line." `assert_dividend_yield_suspects.sql` (the one block with two full sentences) becomes one
    sentence.
  - `.claude/active_work.md`: current facts (audit issues, this branch, the #71 state).

done_when:
  - `git grep -n -E "dim_stock\.(sector|currency)|st\.(sector|currency)|dim_stock has no" -- dbt_analytics docs scripts tests ':!dbt_analytics/target' ':!dbt_analytics/logs'`
    finds nothing.
  - `python scripts/bootstrap.py --verify` passes (dbt build with the unit tests, including the 19 changed
    `dim_stock` inputs), and `python scripts/check_real_fixture_mart.py` shows the real-fixture golden mart
    unchanged (`git diff --stat tests/fixtures/real/golden_mart.csv` empty).
  - `git grep -n -E "market's latest snapshot|each market's latest" -- dbt_analytics/models docs` finds only the
    `card_assessments` grain in `docs/data_contract.md` (a different table) or nothing.
  - New tests, mutation-checked: a Used-by line naming a model that does not depend on it fails; a dependent model
    missing from the line fails; a line naming only non-model consumers passes; a model without the line is
    skipped; the real manifest passes.
  - No block of two `--` comment lines in `dbt_analytics/` holds two full sentences (`[.!?]\s+[A-Za-z_]` across
    the joined block), by the same scan as in the audit.
  - `pytest tests -q` passes; `python scripts/check_context_budget.py` passes.

known_limits:
  - The Used-by check compares model names only; a Used-by line may name an export, a script or the frontend.
  - A comment block counts as one sentence when it has no full stop followed by a new sentence; semicolons join
    clauses within a sentence.
  - Model names in prose after a Used-by list count as named; a bold marker inside the list ends the match.
  - The Reuse amendment is a rule text change: it ships with this merge request for the owner to merge.

regression_checklist:
  - Every card number, eligibility flag and column of the mart is unchanged (golden mart, dbt unit tests).
  - The other staging, base, core, intermediate and mart descriptions are untouched.
  - `scripts/check_dbt_documentation.py` keeps every existing check and its exit behaviour.
