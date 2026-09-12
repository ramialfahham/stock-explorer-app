# Task contract
> DISPOSABLE. **Owns:** THIS task's objective, `scope_paths`, reserved decisions and
> `done_when`.
> **Never:** anything that outlives the task. Overwritten by the next one.

objective: Three owner decisions from MR !131 and !132, taken in chat: two catalogue
  `applicability` sentences reworded; the playground tabs drop the bold heading that
  repeated the tab name.

scope_paths:
  - dbt_analytics/seeds/metric_catalogue.csv
  - frontend/metrics.json
  - frontend/metric_school.py
  - tests/tooling/test_metric_catalogue.py
  - tests/frontend/test_metric_school.py
  - .claude/task/contract.md
  - .claude/task/review.md
  - .claude/active_work.md

decisions_reserved:
  - Owner-set wording (chosen from options presented in chat, option A each):
    `statement_roe_pct`: "Means something different for banks." becomes "For a bank, high
    ROE mostly reflects regulated leverage, not a financing choice; compare banks with
    banks."
    `working_capital`: "businesses with no turnover" becomes "businesses with little or no
    revenue".
  - Owner-set composition: the playground tab name carries the metric label; the bold
    heading inside each tab, which repeated it, is removed.

done_when:
  - The two sentences replaced, CSV rewritten through the csv module and re-parsed at 21
    columns per row; only those two rows differ.
  - `frontend/metrics.json` regenerated; `test_regenerated_json_matches_committed` passes.
  - The pinned `working_capital` phrase in `test_metric_catalogue.py` follows the new text;
    `test_metrics_withheld_from_financials_never_say_banks` still passes (ROE is shown for
    financials, so its bank sentence is allowed).
  - No `st.markdown` heading inside a playground tab; the AppTest asserts no markdown on
    the page and binds each tab to its metric through its input labels instead.
  - `pytest tests/ -q` green.

impact_map: Two catalogue strings and their JSON export (no screen renders `applicability`);
  four lines removed from the playground render path. No formula, format, `applies_to` or
  eligibility change.
