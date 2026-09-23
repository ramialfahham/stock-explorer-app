# Task contract
> DISPOSABLE. **Owns:** THIS task's objective, `scope_paths`, reserved decisions and
> `done_when`.
> **Never:** anything that outlives the task. Overwritten by the next task.

objective: Closes GitLab issue #24. `int_stock__sector_benchmarks.sql` gates every
  metric's `median`/`min`/`max`/`quantile_cont` on `sector_peer_count >= 8` -- the count of
  card-eligible peers in the sector, not the count of those peers that actually have a
  non-null value for the specific metric being aggregated. SQL aggregates silently skip
  nulls, so a metric with almost no real coverage (never eligibility-gated:
  `forward_pe`/`debt_to_equity`/`current_ratio_stmt`/`roa_pct`; gated for the other
  company_type only: the other 6 metrics in a sector of the type that doesn't require
  them; or excluded by the negative-equity filter on `debt_to_equity`/`statement_roe_pct`)
  can still render, implying a robust 8+-peer benchmark while resting on far fewer real
  values. Found while scoping issue #23 (deferred, doc-only, now superseded by this fix --
  owner decision 2026-09-23: do the SQL fix first, land accurate docs against the
  corrected behavior rather than against the flawed one).

  Fix (owner-approved design, same conversation): compute each metric's own post-filter
  non-null count (`count(metric)`, or `count(case when <existing filter> then metric
  end)` for the two negative-equity-filtered metrics) alongside its existing aggregates in
  `sector_medians`, and gate that metric's stats in `combined` on ITS OWN count meeting
  `peer_threshold`, not on `sector_peer_count`. `sector_peer_count` itself is unchanged --
  it stays a plain `count(*)` of the sector's peer group, still exposed as-is, no longer
  used as a stand-in for per-metric coverage.

scope_paths:
  - dbt_analytics/models/4_intermediate/int_stock__sector_benchmarks.sql
  - dbt_analytics/models/4_intermediate/_intermediate_unit_tests.yml
  - .claude/task/contract.md
  - .claude/task/review.md
  - .claude/active_work.md

decisions_reserved: none for this branch -- the metric-definition change itself (gate
  per-metric coverage instead of sector membership) was escalated and approved by the
  owner in-thread before this contract was written. Not in scope, left open in issue #24
  for a future decision: whether to expose each metric's coverage count as its own column,
  and whether any metric should use a threshold other than 8.

done_when:
  - Every one of the 10 benchmarked metrics' `median`/`min`/`max`/`q1`/`q3` (`forward_pe`
    has no q1/q3) is null unless that metric's OWN non-null (post-filter) peer count meets
    `peer_threshold` -- not gated on `sector_peer_count`.
  - `sector_peer_count` itself is unchanged: still `count(*)` over the eligible peer group,
    still always non-null, not used in any of the 10 metrics' gating logic.
  - The existing `sector_benchmarks_excludes_negative_equity_peer_from_debt_to_equity_and_roe`
    unit test is corrected for the fixed gate: its original 8-peer/7-clean fixture now
    correctly expects null (7 < 8 real values after the exclusion filter, previously hidden
    by gating on the unfiltered `sector_peer_count` instead) -- split into two cases so the
    exclusion-ordering assertion (min/median/Q1/Q3 correctly exclude the contaminant) still
    has its own passing scenario with a 9th, positive-equity peer restoring per-metric
    coverage to 8.
  - New unit test proves the core defect is fixed: a sector with `sector_peer_count >= 8`
    where a never-gated metric (e.g. `forward_pe`) has fewer than 8 real values renders
    that metric's stats null while a fully-covered metric in the same sector still
    computes.
  - `dbt build --project-dir dbt_analytics --profiles-dir .` and `dbt test
    --project-dir dbt_analytics --profiles-dir .` (unit tests + existing data_tests) pass
    clean.
  - Review cycle run (`scope-auditor`, `analytics-engineer-reviewer` per
    `.claude/review_routing.json`'s `*.sql`/`dbt_analytics/*.yml` + `always` rules),
    `review.md` written, committed on branch `fix/sector-benchmark-per-metric-coverage-gate`,
    MR opened. Not merged -- owner's action.

not_in_scope: issue #23's doc-only fix (superseded here, will be re-scoped once this
  lands, against the corrected gate). Exposing per-metric coverage counts downstream.
  Changing `peer_threshold` itself. Any mart/frontend change -- this model's OUTPUT SHAPE
  (column list) does not change, only which cells are null.
