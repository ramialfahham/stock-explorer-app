# Task contract
> DISPOSABLE. **Owns:** THIS task's objective, `scope_paths`, reserved decisions and
> `done_when`.
> **Never:** anything that outlives the task. Overwritten by the next task.

objective: `.claude/active_work.md` item 4 left a question open since MR A2: whether
  `accepted_range` sanity tests belong on the card metrics prone to near-zero-denominator
  explosion, and if so, at what severity. Owner decided (in chat, 2026-09-15): a wide sanity
  guard at `severity: warn`, backed by measured production extremes, not a definitional
  hard-null bound. Added `dbt_utils.accepted_range` to eight metrics with a known or plausible
  explosion mode (`ebit_margin_pct`, `revenue_growth_yoy_pct`, `net_debt_to_ebitda`,
  `fcf_margin_pct`, `debt_to_equity`, `statement_roe_pct`, `net_margin_pct`,
  `cash_runway_months`) in `dbt_analytics/models/5_marts/_marts.yml`, bounds set from a full
  paginated export of `mart_stock_cards` (5,726 rows, 2026-09-15) so every measured real
  value, including DYL's known pre-revenue extremes, passes with room to spare. Two gaps were
  caught by analytics-engineer-reviewer across two review rounds, both because the initial
  selection method -- a keyword grep over the catalogue's `applicability` field -- only finds
  a caveat written in prose, not an unguarded division in the model SQL itself: `net_margin_pct`
  (shares `fcf_margin_pct`'s revenue denominator and catalogue caveat, gates financial-card
  eligibility) was missing from round 1; `cash_runway_months` (divides by unfloored
  `-computed_fcf` in `int_stock__card_metrics.sql`, rendered on the pre-revenue card) was
  missing from round 2 -- a real, live case: LLOY (`uk_ftse100`) measures 1093.1 months
  (~91 years) against SRE's (`us_sp500`) 0.06. `roa_pct`, `current_ratio_stmt`, and the two
  exported-but-unrendered fields `price_to_tangible_book`/`net_cash_to_market_cap` were
  checked against the same production export and excluded: the first two measured modest and
  bounded, the latter two are documented dead columns no card renders. All reasoning is
  recorded in `docs/data_contract.md` so it doesn't need re-litigating.

scope_paths:
  - dbt_analytics/models/5_marts/_marts.yml
  - docs/data_contract.md
  - docs/context_budget.yml
  - .claude/active_work.md
  - .claude/task/contract.md
  - .claude/task/review.md

decisions_reserved:
  - Wide sanity guard (`severity: warn`) over a definitional hard-null bound. Owner's call, in
    chat, 2026-09-15 -- already settled, not open in this task.

done_when:
  - All eight metrics carry `dbt_utils.accepted_range` with `config: {severity: warn}` and
    bounds documented in `docs/data_contract.md`, each measured against the full exported
    history; excluded candidates (`roa_pct`, `current_ratio_stmt`,
    `price_to_tangible_book`, `net_cash_to_market_cap`) have their exclusion reasoning
    recorded there too.
  - `dbt build --project-dir dbt_analytics --profiles-dir . --select mart_stock_cards
    --full-refresh` passes clean (0 warn, 0 error) against local fixtures.
  - A mutation test (temporarily narrowing one bound until fixture data trips `WARN`, then
    restoring it) proves the guard actually fires, not just that it's present.
  - `.claude/active_work.md` item 4 closed; the IAG anomaly recorded as a side finding, not
    root-caused, out of scope for this task.
  - `pytest tests/ -q` and `pytest tests/tooling/test_check_context_budget.py -q` green; no
    em-dash/en-dash introduced on any touched line.

impact_map: dbt test config only, `severity: warn` -- non-blocking, does not fail CI or null
  any card value. `docs/context_budget.yml`'s budget for `docs/data_contract.md` raised four
  times across this task's review rounds (60000 -> 61000 -> 62000 -> 63000 -> 64000) to fit
  the growing documentation as each reviewer-caught defect (two coverage gaps, one population
  mislabeling) was fixed and written up, per that file's own documented raise-and-say-why
  process (already used once earlier this session for the same file, before this task
  started). cto-reviewer flagged in round 3 that this should be the last raise for this task;
  the round-4 bump to 64000 (rather than the exact 63,081 measured) is deliberately rounded up
  for headroom, per that same feedback. No code path, no other model, no other metric touched.
