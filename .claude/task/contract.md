# Task contract
> DISPOSABLE. **Owns:** THIS task's objective, `scope_paths`, reserved decisions and
> `done_when`.
> **Never:** anything that outlives the task. Overwritten by the next task.

objective: `docs/data_contract.md`'s "Supabase export -- `mart_stock_cards`" heading states
  the Postgres TABLE's three-column grain, `(market_code, ticker, snapshot_date)`, under a
  heading naming only the shared dbt-model/table name -- ambiguous now that the dbt MODEL's
  own description (`dbt_analytics/models/5_marts/_marts.yml`) explicitly declares a narrower
  grain, `(market_code, ticker)` at each market's latest snapshot only, and contrasts it with
  the accumulating Postgres table. Three reviewers flagged this in an earlier MR, never fixed.
  Owner decision: add the word "table" to the heading, per that earlier finding's exact fix.

scope_paths:
  - docs/data_contract.md
  - .claude/task/contract.md
  - .claude/task/review.md
  - .claude/active_work.md

decisions_reserved: none -- a doc-accuracy fix per an already-recorded owner-approved finding,
  not a new decision.

done_when:
  - The heading reads "## Supabase export -- `mart_stock_cards` table".
  - The Grain line explicitly distinguishes the table's grain from the dbt model's own
    (narrower) grain, pointing at the model's own description for the model-side detail.
  - `pytest tests/ -q` green; no test hardcodes the old heading text.

impact_map: `docs/data_contract.md` only -- prose accuracy fix, no schema or code change.
