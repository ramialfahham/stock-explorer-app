# Task contract
> DISPOSABLE. **Owner:** THIS task's objective, `scope_paths`, reserved decisions and
> `done_when`.
> **Never:** anything that outlives the task. Overwritten by the next task.

objective: Works #75 (DOC-3 defects 32 and 33 of the quality-baseline audit re-run; the owner calls 34 to 52 stay
  untouched). `docs/streamlit_deploy.md` says the card has three headline metrics with two more under "More
  metrics (scroll)", which `docs/north_star.md` and `docs/ui/card_metric_cell.md` contradict and the frontend does
  not render; `docs/data_contract.md` lists `yf_fundamentals.parquet` as "Planned" under a "Phase B baseline" heading
  although ingestion writes it on every run, and its Freshness table has a "News (Phase 2) | Daily | Separate
  workflow" row for a workflow that does not exist (headlines are fetched on demand in the Saved tab, as
  `docs/operations_guide.md` says); `docs/project_context.md` repeats "(Phase B)". One rule: a doc states what the
  code does now, with no phase labels for work that has shipped.

scope_paths:
  - docs/streamlit_deploy.md
  - docs/data_contract.md
  - docs/project_context.md
  - .claude/active_work.md
  - .claude/task/contract.md
  - .claude/task/review.md

decisions_reserved: None open. Both defects are false claims with a documented true version elsewhere (the audit's
  own proposed fixes); no product, metric, naming or permanent decision. The owner calls 34 to 52 are not touched.

changes:
  - `docs/streamlit_deploy.md`: the UX notes sentence about three headline metrics and "More metrics (scroll)"
    becomes a pointer to `north_star.md` section "The card: fundamentals by company type". The next paragraph (Save
    is stored in the browser) stays.
  - `docs/data_contract.md`: the two raw-parquet tables ("Current (Phase B baseline)" and "Planned (fundamentals)")
    become one table of the three files under one heading, rows unchanged; the "News (Phase 2)" row of the Freshness
    table is deleted.
  - `docs/project_context.md`: "and (Phase B) `yf_fundamentals.parquet`" becomes "and `yf_fundamentals.parquet`".
  - `.claude/active_work.md`: current facts.

done_when:
  - `git grep -n -E "Phase B|Planned \(fundamentals\)|News \(Phase 2\)|More metrics|three headline metrics" -- docs
    frontend scripts tests` finds nothing.
  - `git grep -n "yf_fundamentals.parquet" -- docs/data_contract.md docs/project_context.md` still finds the file named
    in both documents.
  - `pytest tests -q` passes (it includes the doc-path and docs-indexed checks); `python scripts/check_context_budget.py`
    passes.

known_limits:
  - Other phase labels outside this defect ("Phase 2 checklist" in `docs/supabase_setup.md`, the "Phase 2 backlog" in
    `docs/north_star.md`, "Metric-layer Phase 2" in `scripts/audit_mart_vs_yfinance.py`) name a checklist, a backlog
    and a past stage of other work; they are not claims about whether a file exists and are left as they are.
  - The Freshness table loses its News row and gains no replacement; `docs/operations_guide.md` line 51 already
    states how Saved-tab headlines are fetched.

regression_checklist:
  - No other row, heading or sentence of the three docs changes.
  - `tests/tooling/test_schema_copies_agree.py` still finds its heading and table in `docs/data_contract.md`.
