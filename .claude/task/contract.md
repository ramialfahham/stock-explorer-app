# Task contract
> DISPOSABLE. **Owner:** THIS task's objective, `scope_paths`, reserved decisions and
> `done_when`.
> **Never:** anything that outlives the task. Overwritten by the next task.

objective: Works #75 (documentation items 38 to 52 of the second quality-baseline audit re-run), #70 (ING-3), #79 (DOC-3) and
  #18 (DOC-1 saved_list). One rule: a durable doc states the current rule or fact, once, and is not a log, a count that
  is stated several ways, or a to-do; every copy of a changed claim is fixed, in docs, code comments and tests alike.

scope_paths:
  - docs/data_contract.md
  - docs/project_context.md
  - docs/development_workflow.md
  - docs/operations_guide.md
  - docs/supabase_setup.md
  - docs/metric_layer.md
  - docs/constituent_sources.yml
  - docs/ux_principles_finanz_lern_apps.md
  - docs/ui/card_metric_cell.md
  - docs/ui/design_system.md
  - docs/ui/discover_header.md
  - docs/ui/discover_list.md
  - docs/ui/saved_list.md
  - .claude/working-agreement.md
  - .env.example
  - scripts/apply_supabase_migrations.py
  - scripts/print_supabase_pooler_config.py
  - ingestion/yfinance/ingest.py
  - tests/ingestion/test_ingest_resume.py
  - tests/tooling/test_apply_supabase_migrations.py
  - tests/tooling/test_metric_catalogue.py
  - .claude/active_work.md
  - .claude/task/contract.md
  - .claude/task/review.md

decisions_reserved: Answered 2026-10-28 ("defaults"). (1) The Management API pooler lookup in
  `scripts/apply_supabase_migrations.py`: delete the branch and its doc passages. (1b) Answered A on
  2026-10-28: the local helper `scripts/print_supabase_pooler_config.py` imported the deleted function and is deleted
  with `SUPABASE_ACCESS_TOKEN`. (2) `.claude/working-agreement.md`:
  delete the sentence "Every one of those six rounds was the same failure". (3) `docs/constituent_sources.yml` ch_smi
  note: state current facts without dates and file the open question as an issue (issue 85). (4)
  `frontend/metrics.json` seed columns `importance_tier` and `basis_column` (tracked #57): left in place, no change in
  this task. The other items follow the audit's proposed fix.

changes:
  - `scripts/apply_supabase_migrations.py`: the `GITHUB_ACTIONS` Management API lookup, its `SUPABASE_ACCESS_TOKEN` read,
    the "GitHub secret" hint and the now unused imports are deleted; `tests/tooling/test_apply_supabase_migrations.py`
    pins the remaining resolution order. `docs/supabase_setup.md`, `docs/operations_guide.md` and `.env.example` drop the
    403 and Management API passages, the access token row and the helper script; `SUPABASE_ACCESS_TOKEN` is removed with
    `scripts/print_supabase_pooler_config.py`, whose only job was the deleted lookup.
  - `ingestion/yfinance/ingest.py`: the checkpoint write runs before the ok/empty counters, and a failed write drops the
    row, so a ticker is counted once; `tests/ingestion/test_ingest_resume.py` covers it.
  - `docs/operations_guide.md` "Production architecture" is the one list of the `data-pipeline` steps and matches
    `.gitlab-ci.yml`; `docs/development_workflow.md` links to it; the "Expect:" line points at it.
  - `docs/data_contract.md`: no currency count, no market list, daily prices on the 1st and 15th schedule, incident and
    measurement logs and the "considered and declined twice" history removed (back under its byte budget).
  - `docs/project_context.md`: real model names; dbt reads parquet through `raw_parquet_union`.
  - Jobs that use the credentials: three named in `docs/operations_guide.md` and `docs/supabase_setup.md`.
  - `docs/ux_principles_finanz_lern_apps.md` links the UX gate instead of copying it; the "Removed:" lines and the
    rejected-option clause are gone from the UI specs; review-round history and measurement logs removed from
    `docs/ui/card_metric_cell.md`, `docs/ui/design_system.md` and `docs/ui/discover_list.md`.
  - `docs/ui/saved_list.md` states only what Saved v1 contains; `docs/north_star.md` owns compare.
  - `docs/metric_layer.md`: origin sentences and the "Scope / follow-ups" section deleted;
    `tests/tooling/test_metric_catalogue.py` docstring loses the origin sentence.
  - `docs/constituent_sources.yml`, `.claude/working-agreement.md`: as in decisions_reserved.

done_when:
  - `git grep -n -i -E "spans 6 currencies|GITHUB_ACTIONS|HTTP 403|base_yf__daily_prices|fct_daily_price|int_stock__price_changes|Surprise me worldwide|six rounds|5,726 rows|carried=853|Phase 1 \(this layer\)|Fixed 2026-08-28|audited 2026-08-28|round 2 of this task|Never .Compare" -- . ':!.claude/task' ':!.claude/active_work.md' ':!tests/fixtures'` finds nothing.
  - `pytest tests -q` passes; `check_context_budget.py`, `check_docs_indexed.py` and `check_no_em_dash.py` pass.
  - The new tests fail on the old code (ingest write failure counted twice).

known_limits:
  - The Management API deletion is not exercised against a live Supabase project; the `supabase-migrate` job on `main`
    runs `apply_supabase_migrations.py` with `SUPABASE_DB_HOST`, the first resolution step, which this change leaves as it was.
  - Measured ranges still in `docs/data_contract.md` (for example the fill-floor and dividend-yield ranges) are not part
    of this task.

regression_checklist:
  - The resolution order in `resolve_database_url` is host, then full URI, then direct host.
  - Every doc linked from `CLAUDE.md` is still linked; `docs/data_contract.md` is under 68,400 bytes.
  - The accepted_range bounds in `docs/data_contract.md` are unchanged.
