# Task contract
> DISPOSABLE. **Owns:** THIS task's objective, `scope_paths`, reserved decisions and
> `done_when`.
> **Never:** anything that outlives the task. Overwritten by the next task.

objective: Phase 5 of the owner-approved six-phase repo-cleanup plan
  (`C:\Users\Rami\.claude\plans\spicy-frolicking-bachman.md`): dbt YAML structure, 2 items.

  1. **Split `dbt_analytics/models/4_intermediate/_intermediate.yml`** (1,430 lines) into
     `_intermediate.yml` (563 lines, `version`/`models`) and a new
     `_intermediate_unit_tests.yml` (866 lines, `unit_tests`), matching the `_core.yml` /
     `_core_unit_tests.yml` and `_yfinance_base.yml` / `_yfinance_base_unit_tests.yml` split
     already used elsewhere. Verified byte-identical at split time (PyYAML diff of the
     `models`/`unit_tests` values). The em-dash guard then caught 3 pre-existing em-dashes in
     moved comment lines -- never flagged in the original (untouched lines aren't violations)
     but flagged once relocated, since `git diff --no-renames` (both this checker and the
     commit gate use it) sees a new file's content as fully added regardless of origin. Fixed
     rather than exempted, since the content violates the rule's intent either way. `dbt parse`
     and `dbt test --select test_type:unit` (27/27 PASS, 0 errors) confirm the split is sound.

  2. **Asymmetric `accepted_range` coverage, corrected scope.** The plan names 8 metrics as
     uncovered (`current_ratio_stmt`, `price_to_tangible_book`, `roa_pct`,
     `dividend_yield_pct`, `net_cash_to_market_cap`, `net_cash`, `working_capital`,
     `burn_rate_monthly`). On inspection, `docs/data_contract.md` already carries evidenced
     "checked and left out" reasoning for 4 of them (`current_ratio_stmt`,
     `price_to_tangible_book`, `roa_pct`, `net_cash_to_market_cap`), written during the
     earlier `accepted_range` work (MR !158) -- the plan text predates that entry. Only 4 were
     genuinely unaddressed: `dividend_yield_pct`, `net_cash`, `working_capital`,
     `burn_rate_monthly`. Owner explicitly approved a read-only production query
     (`mart_stock_cards`, via the existing `.env` credentials `apply_supabase_migrations.py`
     already uses) to measure these, after the auto-mode classifier blocked the first
     attempt as a "Production Reads" action -- see the AskUserQuestion this session.

     Measured against the full exported history (5,726 rows): `dividend_yield_pct`
     0.0036% to 18.6% (4,946 non-null) -- no explosion pattern, and its real known defect
     (per-row mixed units, issue #10) produces plausible-not-extreme values, so a range guard
     would add no real protection; excluded, same as the dead-column pair above (also
     no-longer-catalogued, unrendered). `net_cash`, `working_capital`, `burn_rate_monthly` are
     NOT near-zero-denominator ratios (subtraction / divide-by-constant-12), so the plan's
     framing of "same denominator-risk shape" doesn't hold -- but all three are computed for
     every `company_type` and rendered/eligibility-gating on `pre_revenue`, the same
     `cash_runway_months` pattern (full-population extremes come from mega-cap JPY companies
     computed outside their intended context; the `pre_revenue`-rendered subset, measured
     separately with a second query, is far narrower). Guards added, bounded to cover the full
     unfiltered population with real headroom: `net_cash` -50T to 100T; `working_capital`
     +-20T; `burn_rate_monthly` 0 to 2.5T (structurally non-negative). Full writeup with both
     measured ranges (full population and `pre_revenue`-only) in `docs/data_contract.md`,
     next to the existing seven/eight-metric entry. `docs/data_contract.md`'s budget raised
     64000 -> 65500 for the real new content, after trimming the addition once already.

scope_paths:
  - dbt_analytics/models/4_intermediate/_intermediate.yml
  - dbt_analytics/models/4_intermediate/_intermediate_unit_tests.yml
  - dbt_analytics/models/5_marts/_marts.yml
  - docs/data_contract.md
  - docs/context_budget.yml
  - .claude/active_work.md
  - .claude/task/contract.md
  - .claude/task/review.md

decisions_reserved: the corrected 4-metric scope (vs. the plan's stated 8) is a factual
  correction backed by grep/doc evidence, not a product decision -- flagged for review, not
  silently applied. The production-read permission itself was the one live decision this
  session, answered by the owner via AskUserQuestion (allow the read-only query). Guard
  bounds are engineering judgment from measured data, following the exact precedent
  (`cash_runway_months`) already in the doc, not a new methodology.

done_when:
  - `dbt_analytics/models/4_intermediate/_intermediate.yml` and
    `_intermediate_unit_tests.yml` together are content-identical to the pre-split file
    (verified via PyYAML value comparison, not just line count), except 3 pre-existing
    em-dashes in comments fixed to `--` per the em-dash guard's own finding.
  - `dbt parse --project-dir dbt_analytics --profiles-dir .` succeeds.
  - `dbt test --select test_type:unit --project-dir dbt_analytics --profiles-dir .` --
    27/27 PASS, 0 errors (same count as before the split).
  - `_marts.yml` has 3 new `dbt_utils.accepted_range` tests (`net_cash`, `working_capital`,
    `burn_rate_monthly`), all `severity: warn`, matching the existing 8 tests' shape.
  - `docs/data_contract.md`'s `accepted_range` section documents all 4 corrected-scope
    metrics with measured evidence: 3 guarded (with full-population and `pre_revenue`-only
    ranges), 1 excluded (`dividend_yield_pct`, with reasoning).
  - `dbt build --project-dir dbt_analytics --profiles-dir .` against CI fixtures succeeds
    with no new test failures (warn-only tests don't fail a build regardless, but the SQL
    must be valid and execute without error).
  - `pytest tests/ -q` green, no regression.
  - `python scripts/check_docs_indexed.py`, `check_context_budget.py`,
    `check_no_narrative_dates.py`, `check_no_em_dash.py` all pass.

impact_map: dbt schema/YAML + docs change; no model SQL, no compute, no column added or
  removed. 3 new warn-only sanity tests on already-existing mart columns -- no behavior
  change to what the app displays or how eligibility is computed. No new dependency, no CI
  change.
