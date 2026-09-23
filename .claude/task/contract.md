# Task contract
> DISPOSABLE. **Owns:** THIS task's objective, `scope_paths`, reserved decisions and
> `done_when`.
> **Never:** anything that outlives the task. Overwritten by the next task.

objective: Closes GitLab issue #23, re-scoped against the now-merged issue #24 fix (MR
  !209). All ~50 `sector_median/min/max/q1/q3_*` columns in `int_stock__sector_benchmarks`
  (and their passthroughs in `mart_stock_cards`) still say "Null when: sector_peer_count <
  8" -- stale now that #24 changed the actual gate to each metric's own per-metric
  non-null (post-filter) count (`n_<metric>` in `int_stock__sector_benchmarks.sql`'s
  `sector_medians` CTE), not `sector_peer_count`.

  The fix makes the true rule UNIFORM across all 10 metrics: null when fewer than 8 of the
  sector's eligible peers have a non-null value for that specific metric -- which can be
  fewer than `sector_peer_count` for a documented, metric-specific reason:
  - `forward_pe`, `debt_to_equity`, `current_ratio_stmt`, `roa_pct`: not required by
    either company_type's eligibility gate.
  - `ebit_margin_pct`/`revenue_growth_yoy_pct`/`net_debt_to_ebitda`/`fcf_margin_pct`: gate
    operating eligibility only -- not required in a financial-type sector.
  - `net_margin_pct`/`statement_roe_pct`: gate financial eligibility only -- not required
    in an operating-type sector.
  - `debt_to_equity`/`statement_roe_pct` additionally exclude peers with negative
    stockholders' equity (model SQL comment, unchanged by #24).

  Also: `mart_stock_cards.sector_peer_count`'s description names "sector unknown or no
  benchmark row" but not the dominant, by-design cause -- the join excludes every
  `pre_revenue` row. This part is independent of #24, was true before and after.

  Fix: rewrite each affected column's "Null when" clause in both
  `dbt_analytics/models/4_intermediate/_intermediate.yml`
  (`int_stock__sector_benchmarks`) and `dbt_analytics/models/5_marts/_marts.yml`
  (`mart_stock_cards` passthroughs, plus `sector_peer_count`) to name the real,
  per-metric condition. Business-meaning wording, unit annotations, and existing
  cross-references (card range mark, outlier-aware display clamp, Gemini feedback point 5,
  "no card renders this" for forward_pe) are left untouched -- only the null-when clause
  changes.

scope_paths:
  - dbt_analytics/models/4_intermediate/_intermediate.yml
  - dbt_analytics/models/5_marts/_marts.yml
  - .claude/task/contract.md
  - .claude/task/review.md
  - .claude/active_work.md

decisions_reserved: none -- documentation-accuracy fix against already-merged SQL (#24),
  same method the owner already approved for the 32-column enforcement-gap task (!207). No
  SQL, test, or threshold change.

done_when:
  - Every `sector_median/min/max/q1/q3_*` column description in both YAML files states
    its actual null condition (per-metric coverage count vs. sector_peer_count, why that
    count can fall short by company_type gating, and/or the positive-equity filter, as
    applicable) -- not a blanket restatement of "sector_peer_count < 8".
  - `mart_stock_cards.sector_peer_count`'s description names the pre_revenue join
    exclusion as the dominant cause, not just "sector unknown or no benchmark row".
  - `scripts/check_dbt_documentation.py`'s `check_null_when_documented` still passes (no
    checker behavior change -- this task is content only).
  - `dbt parse`/`dbt docs generate --project-dir dbt_analytics --profiles-dir .` still
    parses the YAML cleanly.
  - Review cycle run (`scope-auditor`, `analytics-engineer-reviewer` per
    `.claude/review_routing.json`'s `dbt_analytics/*.yml` + `always` rules), `review.md`
    written, committed on a new branch, MR opened. Not merged -- owner's action.
