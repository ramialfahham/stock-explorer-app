# Task contract

objective: Extend the range-mark benchmark feature from 4 to 9 metrics -- the remaining
  operating and financial metrics in the catalogue, per the owner-approved "11-metric benchmark
  expansion" follow-up to MR #22, scoped down during this task from the original 11 (see
  amendments) after finding the pre-revenue portion would ship as dead code.

  Today `benchmarkable: true` covers only `ebit_margin_pct`, `revenue_growth_yoy_pct`,
  `net_debt_to_ebitda`, `fcf_margin_pct` (all operating; `revenue_growth_yoy_pct` also applies
  to financial and is already benchmarked there today, incidentally). This task adds 5 more:
  - **Operating-only**: `debt_to_equity`, `current_ratio_stmt` (both currently
    supporting/tie-breaker axes in `_verdict_operating`, not core).
  - **Operating and financial**: `statement_roe_pct` -- `applies_to: operating|financial`
    already, and already shown on operating cards today via `INPUT_FIELDS_BY_TYPE["operating"]`
    (`scripts/assessment_rules.py`); this task only flips its `benchmarkable` flag, so the range
    mark newly appears on BOTH card types wherever peer count clears 8, not financial cards only.
  - **Financial-only**: `net_margin_pct`, `roa_pct`.

  Pre-revenue's 4 metrics (`net_cash`, `working_capital`, `cash_runway_months`,
  `burn_rate_monthly`) are explicitly OUT of scope: only 3 pre-revenue-type companies exist in
  the entire app today (verified against live production, 2026-09-03), split across two
  sectors, and the range mark requires 8+ sector peers to render at all -- pre-revenue
  benchmarking is buildable but could never actually show for anyone at current market
  coverage. Owner explicitly chose the 5-metric scope over the original 9-metric (5 + 4
  pre-revenue) one for this reason.

  `BENCHMARK_METRICS` (`frontend/card_copy.py`) is already catalogue-driven (built from every
  metric where `benchmarkable: true`, no hardcoded list), and `benchmark_range()` already
  derives its `sector_min_<metric>`/`sector_q1_<metric>`/etc. keys generically from the metric
  id parameter -- verified by reading both during scoping. **No frontend code changes are
  needed at all**; flipping the 5 catalogue flags and populating the corresponding mart/export
  columns is sufficient for these 5 metrics to render range marks (including the outlier-aware
  Tukey-fence clamp and off-scale arrow MR !87 already built, which apply automatically to any
  benchmarked metric, not specifically the original 4).

scope_paths:
  - dbt_analytics/seeds/metric_catalogue.csv
  - frontend/metrics.json (generated from the catalogue by
    scripts/export_metric_definitions_json.py; regenerated, not hand-edited)
  - dbt_analytics/models/4_intermediate/int_stock__sector_benchmarks.sql
  - dbt_analytics/models/4_intermediate/_intermediate.yml
  - dbt_analytics/models/5_marts/mart_stock_cards.sql
  - dbt_analytics/models/5_marts/_marts.yml
  - frontend/card_copy.py (comment-only: three now-stale "4 benchmarkable" references found by
    analytics-engineer-reviewer's round-1 pass, corrected to 9; no logic change)
  - tests/frontend/test_card_copy.py (comment-only: two more of the same stale "4 benchmarkable"
    references, in a sibling file, found by cto-reviewer's round-2 pass; already in scope_paths
    below for other reasons, noted here since this is why it changed)
  - supabase/migrations/*.sql (one new migration file)
  - scripts/export_to_supabase.py
  - tests/tooling/test_*.py (dbt-adjacent Python tests, if any touch these columns or the
    catalogue's benchmarkable count -- verify, don't assume unaffected)
  - tests/frontend/test_card_copy.py
  - tests/frontend/test_card_ui.py
  - docs/data_contract.md
  - docs/ui/card_metric_cell.md
  - .claude/task/contract.md
  - .claude/task/review.md
  - .claude/active_work.md

decisions_reserved: two arose and were both answered directly by the owner. (1) The
  5-vs-9-metric scope question ("just the 5 that would show"). (2) Mid-review: whether to extend
  the negative-equity sign-inversion guard (originally built only for verdict-color computation)
  into the new sector-benchmark aggregates for `debt_to_equity`/`statement_roe_pct` specifically
  -- a metric-specific exception the original done_when had explicitly ruled out, caught
  independently by two reviewers, escalated per working-agreement.md §7 rather than decided by
  analogy, and approved by the owner ("go") after a first attempt at asking was too
  jargon-heavy and was rightly rejected. See amendments below for the full reasoning. Nothing
  else in this task touches wording, a new mechanism, or anything else §6 reserves.

done_when:
  - `dbt_analytics/seeds/metric_catalogue.csv`: `benchmarkable` flipped to `true` for
    `debt_to_equity`, `current_ratio_stmt`, `statement_roe_pct`, `net_margin_pct`, `roa_pct`.
    No other column changed for these rows.
  - `dbt_analytics/models/4_intermediate/int_stock__sector_benchmarks.sql`: for each of the 5
    newly-benchmarkable metrics, the same 5-statistic set the existing 4 metrics already get
    (`sector_median_<metric>`, `sector_min_<metric>`, `sector_max_<metric>`,
    `sector_q1_<metric>`, `sector_q3_<metric>`, the last two via `quantile_cont(<metric>, 0.25
    | 0.75)`), gated through the identical `sector_peer_count >= 8` CASE-null pattern the
    existing columns use -- same threshold, no new number invented. 25 new columns total (5
    metrics x 5 statistics). **Amended mid-review** (see amendments below): `debt_to_equity`
    and `statement_roe_pct` additionally exclude any peer with non-positive
    `stmt_stockholders_equity` from those 2 metrics' own 5 statistics specifically -- a
    metric-specific exception the original done_when explicitly ruled out, added after two
    independent reviewers caught the same correctness defect. The other 3 new metrics
    (`current_ratio_stmt`, `net_margin_pct`, `roa_pct`) carry no such exception; their
    denominators can't go negative in this data.
  - `dbt_analytics/models/4_intermediate/_intermediate.yml`: column descriptions for all 25 new
    columns, matching the existing description style/verbosity for their sibling columns. The
    existing `sector_benchmarks_min_le_median_le_max` expression test extended to cover the 5
    new metrics' `min <= q1 <= median <= q3 <= max` chain, same pattern MR !87 used for the
    original 4. The null-together `dbt_utils.expression_is_true` test's expression extended to
    include all 25 new columns. A new or extended unit test proves at least one of the 5 new
    metrics' quartile computation against literal hand-computed numbers (not derived from the
    formula under test), reusing the exact verification approach and DuckDB `quantile_cont`
    values already confirmed correct in MR !87's `sector_benchmarks_computes_quartiles_with_real_spread`
    test -- does not need to re-derive that math, just apply it to a new metric column.
    **Amended mid-review**: a new mutation-style unit test
    (`sector_benchmarks_excludes_negative_equity_peer_from_debt_to_equity_and_roe`) proves the
    `debt_to_equity`/`statement_roe_pct` equity-sign guard above actually excludes a
    contaminated peer's value from those 2 metrics' aggregates while still counting that peer
    toward `sector_peer_count` -- would fail without the guard, not just a formatting check.
  - `dbt_analytics/models/5_marts/mart_stock_cards.sql`: the 25 new columns selected through
    from `int_stock__sector_benchmarks`, same pattern as the existing columns.
  - `dbt_analytics/models/5_marts/_marts.yml`: matching column descriptions at the mart layer.
  - `supabase/migrations/`: one new migration file (following `012_sector_benchmark_min_max.sql`
    and MR !87's `016_sector_benchmark_quartiles.sql` pattern) adding the 25 new nullable
    numeric columns to `mart_stock_cards`.
  - `scripts/export_to_supabase.py`: the 25 new column names added to `EXPORT_COLUMNS`.
  - Tests: mirror MR !87's `test_export_columns_include_sector_quartiles` /
    `test_export_columns_include_sector_min_max` pattern, extended to assert the 5 new metrics'
    columns are present (and, if useful, that pre-revenue's 4 metrics are still absent --
    documents the scope boundary in a test, not just prose).
  - `docs/data_contract.md`: the "Median for each benchmarked metric (4; forward_pe is no
    longer one)" line and its sibling min/max/q1/q3 lines updated to the new count and metric
    list; the exported-schema table gets the 25 new column rows (mirroring how MR !87 added its
    8).
  - `docs/ui/card_metric_cell.md`: "Only the 4 metrics with `benchmarkable: true`... get a range
    mark today... financial and pre-revenue metrics aren't benchmarked yet, a separate
    follow-up" updated to name all 9 now-benchmarked metrics and state plainly that pre-revenue
    remains deliberately out of scope (peer-count reasoning from this contract, in brief) rather
    than "not done yet." The "not just the 4 with a range mark" line nearby updated to the new
    count too.
  - `pytest` and `dbt build`/`dbt test` both green. No verdict-computation change anywhere --
    `scripts/assessment_rules.py` untouched (these 5 metrics' role in `_verdict_operating`/
    `_verdict_financial` as supporting/core axes is completely unaffected; this task only adds
    a DISPLAY comparison, same separation MR !87 already established).
  - No em dash or en dash on any added line.

impact_map:
  - Every operating and financial card showing `debt_to_equity`, `current_ratio_stmt`,
    `statement_roe_pct`, `net_margin_pct`, or `roa_pct` gains a range mark for that metric where
    its sector has 8+ eligible peers (869 operating-eligible, 166 financial-eligible companies
    live today -- real peer depth, unlike pre-revenue's 3). Purely additive to the card face:
    no existing rendered element changes, `_metric_range_unavailable_html()`'s placeholder
    simply stops appearing for these 5 metrics wherever peer depth clears the threshold.
  - New dbt aggregate columns computed from the same `int_stock__card_metrics` eligible-peer
    rows already feeding the existing benchmark columns -- no new upstream dependency.
    Negligible incremental runtime: 25 more aggregate expressions in the same existing
    `GROUP BY market_code, sector`, same cost class as MR !87's 8-column addition.
  - New Supabase migration (additive, nullable columns, no backfill) and an
    `export_to_supabase.py` column-list update, same shape as MR !87.
  - No `frontend/*` file changes -- verified during scoping that `BENCHMARK_METRICS` and
    `benchmark_range()` are already fully catalogue-driven and metric-agnostic. If this
    assumption turns out wrong during implementation (e.g. a hardcoded metric list surfaces
    somewhere not found during scoping), that is a scope surprise to flag immediately, not
    silently work around.
  - No verdict-computation change -- these 5 metrics already feed `_verdict_operating`/
    `_verdict_financial` today as supporting or core axes; only their DISPLAY (a sector range
    mark) is new.
  - Since this touches nothing under `frontend/`, `docs/working_agreement.md`'s UX PR gate
    likely does not apply in the usual code-review sense, but the card face's visual RESULT
    changes (new range marks appear) -- worth a post-merge live check (a few real cards showing
    the new marks) even though no frontend code is touched, matching this task's own "verify
    the catalogue-driven claim held" caution above.

amendments:
  - Scoped down from the original "11-metric... financial + pre-revenue, 2 more operating"
    follow-up to 5 metrics (2 operating + 3 financial), excluding pre-revenue's 4 entirely.
    Reason: only 3 pre-revenue companies exist in the app today (verified against live
    production), which can never clear the 8-peer rendering threshold in any sector -- building
    it now would ship a feature that can never actually be seen. Owner decision, in response to
    this finding surfaced during scoping, not decided unilaterally.
  - **Mid-review correctness fix, added after two independent reviewers (cto-reviewer,
    equity-analyst-reviewer) both caught it separately.** `debt_to_equity` and
    `statement_roe_pct` both divide by `stmt_stockholders_equity`, which
    `scripts/assessment_rules.py`'s `_axis_unless_denominator_nonpositive` guard already treats
    as sign-breaking when negative (a genuine loss over negative equity divides out to a
    spuriously POSITIVE, non-extreme percentage -- see that function's own comment block,
    "Gemini feedback point 1," owner-approved earlier this session as MR !73). That guard covers
    only the verdict color. Without an equivalent guard here, a sign-flipped peer's value would
    have flowed straight into these 2 metrics' sector median/min/max/quartiles, silently skewing
    the benchmark shown on every OTHER card in that sector too -- and unlike `net_debt_to_ebitda`'s
    analogous failure mode (an extreme magnitude the existing Tukey-fence outlier clamp already
    catches), a sign-flipped value here looks ordinary, not extreme, so nothing else in this
    task's own test coverage would have caught it. Fixed by excluding peers with non-positive
    `stmt_stockholders_equity` from exactly these 2 metrics' 5 statistics (not from
    `sector_peer_count`, and not from any other metric's aggregate), reusing the same judgment
    the owner already approved for the verdict layer rather than inventing a new one -- this is
    the one place in this task where "no metric-specific exception" (the original done_when) no
    longer holds. `current_ratio_stmt`, `net_margin_pct`, `roa_pct` are unaffected: their
    denominators (current liabilities, revenue, total assets) are structurally non-negative in
    this data.

    **Owner authority, recorded explicitly (per working-agreement.md §6/§7):** reusing an
    already-approved judgment by analogy is not itself authority to extend it to a case it
    didn't cover -- scope-auditor's round-3 review correctly held the line on this even after
    the reasoning above was fully disclosed. Escalated in plain language (the first attempt was
    jargon-heavy and rejected outright by the owner); the owner approved shipping the fix
    ("go") over the alternative of shipping the 5 metrics unguarded and filing this as a
    separate known-issue follow-up. This amendment's technical claims were independently
    re-verified as correct by cto-reviewer and equity-analyst-reviewer before the owner decided
    -- the escalation was about authority to extend the rule, not about whether the fix works.
