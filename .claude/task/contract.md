# Task contract
> DISPOSABLE. **Owns:** THIS task's objective, `scope_paths`, reserved decisions and
> `done_when`.
> **Never:** anything that outlives the task. Overwritten by the next task.

objective: Owner feedback (in chat): documents and code comments had accumulated
  date-stamped, decision-history narrative -- the same fact restated 3-5 times across code
  comments, docstrings, tests, and `docs/data_contract.md` (the upsert-clobbering root cause,
  the MR #22 benchmark expansion, a 2026-09-14 UI decision). This directly violates
  `engineering_standards.md` §1.2/§1.3 ("no dates, timestamps, approval markers... a comment
  states what is true now; git records when and who") -- a rule that already existed but had
  no enforcement, so review time never caught it. Built `scripts/check_no_narrative_dates.py`
  to make the category impossible to reintroduce silently, wired into both pre-commit and CI
  (Tier A), matching this repo's own `check_context_budget.py` precedent for how a written
  rule becomes an enforced one. Two review rounds caught real gaps in the first pass: (1) the
  checker's initial `supabase/migrations/` exemption claimed migrations are "never edited
  after merge" -- disproved by this repo's own git history (`018_atomic_card_export.sql` was
  edited by a later commit) -- so the exemption was removed and the two real violations it had
  been hiding (`013_net_cash.sql`, `017_sector_benchmark_financial_operating.sql`) fixed; (2)
  `docs/ui/*.md` uses a `**Scope:**`/`**Authority:**` header instead of `> DURABLE.`, so those
  files were invisible to the checker's markdown scan despite `check_context_budget.py`
  already governing them at the same tier -- fixed by scoping the checker to that directory
  unconditionally, which surfaced and fixed 4 more real violations (`card_metric_cell.md`,
  `design_system.md`, `discover_list.md`) plus one real information-loss regression in
  `frontend/app.py` (a fix had stripped a genuine `_DECK_TTL_SECONDS` 15-60 minute bound along
  with the date it was wrongly bundled with -- restored). This is Phase 1 of a larger
  repo-cleanup plan; later phases (GitLab issue tracking, CI/YAML hygiene, doc architecture)
  are separate, later tasks.

scope_paths:
  - scripts/check_no_narrative_dates.py
  - tests/tooling/test_check_no_narrative_dates.py
  - .pre-commit-config.yaml
  - .gitlab-ci.yml
  - docs/engineering_standards.md
  - docs/data_contract.md
  - docs/operations_guide.md
  - docs/ui/card_metric_cell.md
  - docs/ui/design_system.md
  - docs/ui/discover_list.md
  - dbt_analytics/models/2_base/yfinance/base_yf__constituents.sql
  - dbt_analytics/models/4_intermediate/int_stock__sector_benchmarks.sql
  - supabase/migrations/013_net_cash.sql
  - supabase/migrations/017_sector_benchmark_financial_operating.sql
  - frontend/app.py
  - frontend/card_copy.py
  - frontend/styles.py
  - scripts/generate_assessments.py
  - tests/frontend/test_app_e2e.py
  - tests/frontend/test_card_copy.py
  - tests/frontend/test_card_ui.py
  - tests/frontend/test_styles.py
  - tests/ingestion/test_market_onboarding.py
  - tests/tooling/test_export_to_supabase.py
  - tests/tooling/test_generate_assessments.py
  - .claude/task/contract.md
  - .claude/task/review.md
  - .claude/active_work.md

decisions_reserved: none -- a mechanical hygiene fix of an already-written, already-approved
  rule, not a new rule or a product/content decision. The mechanism itself (a new pre-commit +
  CI check) was scoped and approved in the owner's plan-mode review before this branch existed.

done_when:
  - `python scripts/check_no_narrative_dates.py` passes clean against the full repo tree,
    with no directory or header-convention blind spot left unexamined.
  - `pytest tests/ -q` green (includes the 16 guard tests, one added in round 2 to prove
    migrations are no longer exempt).
  - Every fix states the durable technical fact; no fix left a sentence that reads worse or
    loses real information solely because a date was stripped (the one round-2 regression
    found and fixed).
  - `.pre-commit-config.yaml` and `.gitlab-ci.yml` both run the new check alongside
    `check_context_budget.py`.
  - No em-dash/en-dash introduced on any touched line; no dbt build regression on the two
    touched SQL models (`base_yf__constituents`, `int_stock__sector_benchmarks`).

impact_map: comment/docstring/doc text only across the fixed files -- no behavior change, no
  schema change, no test assertion changed (test bodies untouched, only their docstrings/
  comments). Two new files (the checker + its test). Two config files gain one new step each,
  same shape as the existing `check_context_budget.py` step. `supabase/migrations/` is no
  longer exempted -- scanned like any other SQL, since migrations are demonstrably editable
  after merge in this repo. The two edited migration files (013, 017) only had comment text
  changed; the DDL/DML statements themselves are untouched.
