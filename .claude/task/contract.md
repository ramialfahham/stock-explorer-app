# Task contract
> DISPOSABLE. **Owns:** THIS task's objective, `scope_paths`, reserved decisions and
> `done_when`.
> **Never:** anything that outlives the task. Overwritten by the next task.

objective: Bring SQL comments under `dbt_analytics/` in line with
  `docs/engineering_standards.md` §1.2 (why not what, one sentence, no multi-line blocks, no
  history). Comments only: no SQL token changes, so compiled models are unchanged. First of
  two slices; the frontend layer is its own MR.

scope_paths:
  - dbt_analytics/models/4_intermediate/int_stock__card_metrics.sql
  - dbt_analytics/models/4_intermediate/int_stock__sector_benchmarks.sql
  - dbt_analytics/models/5_marts/mart_stock_cards.sql
  - dbt_analytics/models/2_base/yfinance/base_yf__constituents.sql
  - dbt_analytics/tests/assert_eligible_mart_rows_have_all_metrics.sql
  - dbt_analytics/tests/assert_metric_fill_floor.sql
  - dbt_analytics/tests/assert_percent_scale_passthroughs.sql
  - .claude/task/contract.md
  - .claude/task/review.md
  - .claude/active_work.md

decisions_reserved: none -- §1.2 already codifies the target; no metric, label or output
  changes.

done_when:
  - Every edited comment is at most two lines and one sentence, states why, carries no history.
  - Diff with comments stripped is empty (`git diff -w` on non-comment lines), and
    `dbt compile` output matches `main`'s once comments are stripped.
  - `scripts/check_no_em_dash.py`, `scripts/check_no_narrative_dates.py`,
    `scripts/check_dbt_sql_structure.py` pass.
  - Review cycle run per `.claude/review_routing.json`, committed, MR opened. Not merged.
