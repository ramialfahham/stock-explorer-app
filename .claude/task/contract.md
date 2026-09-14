# Task contract
> DISPOSABLE. **Owns:** THIS task's objective, `scope_paths`, reserved decisions and
> `done_when`.
> **Never:** anything that outlives the task. Overwritten by the next task.

objective: `docs/data_contract.md`'s card-metrics section restated every catalogue row by
  hand and drifted from the seed three times in a month. Owner chose A: generate the table
  from the seed and lock it with a test, as `frontend/metrics.json` already is.

scope_paths:
  - scripts/render_metric_table.py
  - docs/data_contract.md
  - docs/metric_layer.md
  - tests/tooling/test_metric_catalogue.py
  - dbt_analytics/models/4_intermediate/int_stock__card_metrics.sql
  - .claude/task/contract.md
  - .claude/task/review.md
  - .claude/active_work.md

decisions_reserved:
  - Generate rather than delete: owner, in chat, option A over B.
  - The table's columns are the seed's own fields (id, label, `applies_to`, formula spec,
    format, direction), no editorial text. The model's fallbacks and scaling stay described
    in the prose after the table because the seed does not hold them.
  - The formulas of the 13 data-only intermediates (not in the seed) are no longer restated:
    owner, in chat, after the scope-auditor flagged it as a step beyond option A (drop over
    keep-as-prose). The model is their only definition; the contract lists their names,
    guarded by a test that each name is a model column and none is catalogued. Two "why"
    notes that had lived only in that prose (why `fcf_yield_pct` uses Yahoo's trailing FCF;
    why `interest_coverage` takes `abs()`) move beside their formulas in the model. The
    `dividend_yield_pct` scale rule stays as prose: it is about the raw data.

done_when:
  - `scripts/render_metric_table.py` rewrites the block between the two markers from the seed;
    `--check` exits 1 when the block is stale and 0 when current; the doc's line endings are
    preserved on both a CRLF and an LF checkout (unit test over temp docs; `read_text` would
    have stripped the CRs, proven by mutation); `|` in a cell is escaped (unit test).
  - `test_data_contract_metric_table_matches_seed` fails on a hand edit inside the block;
    `test_data_contract_data_only_list_names_real_uncatalogued_columns` fails on a name the
    model does not compute or one that is catalogued (both proven by mutation).
  - No formula of a catalogued metric is stated in the contract outside the generated block.
  - `docs/metric_layer.md` names the render script in "Adding a metric" and the new lock in
    "Tests verify and guard".
  - `pytest tests/ -q` green; `check_context_budget.py` passes.

impact_map: Docs and one generator script; no dbt, export or frontend change.
