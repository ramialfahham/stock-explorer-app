# Task contract
> DISPOSABLE. **Owns:** THIS task's objective, `scope_paths`, reserved decisions and
> `done_when`.
> **Never:** anything that outlives the task. Overwritten by the next task.

objective: `revenue_growth_yoy_pct`'s catalogue copy told readers "one quarter can be noisy,
  so look for a pattern over time" -- but `compute_verdict`'s own growth gate
  (`GROWTH_DECLINE_THRESHOLD_PCT = 0.0`, `scripts/assessment_rules.py`) reacts to ANY
  single-quarter year-over-year decline, no tolerance band, by deliberate design: the owner
  already rejected a -5% tolerance proposed on exactly this "single quarter is noisy"
  argument, on the grounds that a year-over-year comparison already removes seasonal noise.
  The copy told readers to discount the very signal the app's own rule treats as real. Owner
  decision: soften/remove the "noisy... look for a pattern" framing, replacing it with the
  genuine, still-valid caveats a YoY decline can carry (divestment, FX translation, contract
  timing, an unusually strong year-ago quarter) -- reasons a decline might not reflect
  ongoing demand, without telling the reader to wait and see.

scope_paths:
  - dbt_analytics/seeds/metric_catalogue.csv
  - frontend/metrics.json
  - .claude/task/contract.md
  - .claude/task/review.md
  - .claude/active_work.md

decisions_reserved: none -- the exact replacement wording is the owner's, from the same
  chat that made the softening call; not further negotiated here.

done_when:
  - `metric_catalogue.csv`'s `revenue_growth_yoy_pct` row (`interpretation` and `learn`
    fields) no longer tells the reader a decline can be noise to wait out; states the real,
    verdict-consistent caveats instead.
  - `frontend/metrics.json` regenerated from the seed via
    `scripts/export_metric_definitions_json.py` (never hand-edited) and matches.
  - The seed re-parses with the same row/field count as before the edit (CSV quoting risk).
  - `dbt parse --project-dir dbt_analytics --profiles-dir .` succeeds.
  - No other file in the repo still carries the old "noisy... pattern over time" framing as
    user-facing copy (grep swept; code comments describing the PAST rejected -5% proposal are
    historical record, not user-facing copy, and stay as-is).
  - `pytest tests/ -q` green, including the metric-definitions no-drift lock test.

impact_map: Card-face and learn-panel copy for one metric (`revenue_growth_yoy_pct`) only --
  no verdict-rule change, no schema change, no new dependency.
