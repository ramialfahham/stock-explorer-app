# Task contract
> DISPOSABLE. **Owns:** THIS task's objective, `scope_paths`, reserved decisions and
> `done_when`.
> **Never:** anything that outlives the task. Overwritten by the next task.

objective: Owner asked to rename the repo from `stock-swipe-app` to `stock-explorer-app`
  (the app no longer has anything to do with swiping). Done outside this repo's own git
  history: GitLab project renamed (`rami.al-fahham/stock-explorer-app`, canonical, feeds
  Render's auto-deploy and the CI schedule), GitHub mirror renamed to match, local `gitlab`
  remote URL updated, push-mirror sync re-verified working (GitHub's redirect covers the
  still-old embedded mirror URL for now -- the owner needs to repoint it via GitLab's UI
  themselves since it holds an access token this session never had).

  This task is the in-repo follow-through: every live reference to the old repo slug
  (`stock-swipe-app`) or the old product name (`Stock Swipe App`, pre-dating this session's
  already-established "Stock Explorer" product name in `docs/north_star.md`) grepped and
  fixed, per working-agreement.md SS2 ("grep the repo for the claim, not the file you were
  told about"). Two files deliberately left untouched:
  `docs/handover_2026-08-18.md` and `docs/handover_2026-09-03.md` -- point-in-time archives
  per this repo's own docs-index rule, not living docs, never edited for a later rename.

  Round 1 review found two real gaps, both fixed before round 2: scope-auditor caught
  `CLAUDE.md`'s title landing as "Stock Explorer App" while every other file in the same
  diff dropped "App" to match `docs/north_star.md`'s canonical product name -- an internal
  inconsistency within this same rename sweep. cto-reviewer separately noted
  `.gitlab-ci.yml`'s `mkdir -p /tmp/stock-swipe-raw` (a CI temp-dir name derived from the
  old slug, outside the original grep pattern's `-app` suffix) -- added to scope and fixed.

scope_paths:
  - README.md
  - CLAUDE.md
  - .claude/review_routing.json
  - docs/north_star.md
  - docs/streamlit_deploy.md
  - docs/supabase_setup.md
  - docs/project_context.md
  - docs/operations_guide.md
  - docs/development_workflow.md
  - docs/data_contract.md
  - docs/market_registry.yml
  - dbt_analytics/README.md
  - ingestion/constituents/refresh.py
  - supabase/migrations/001_initial_schema.sql
  - supabase/migrations/002_fundamentals_mart.sql
  - .gitlab-ci.yml
  - .claude/task/contract.md
  - .claude/task/review.md

decisions_reserved: none -- the owner gave the rename instruction directly; this task is
  pure mechanical follow-through (find every stale reference, point it at the new name),
  no new product/naming decision made here.

done_when:
  - `grep -rn "stock-swipe-app\|Stock Swipe"` across the repo (excluding the two frozen
    archive docs and .venv/binary caches) returns nothing.
  - `docs/north_star.md`'s repo-name line reflects the actual current state, not a stale
    "may remain" note.
  - `check_no_em_dash.py` and `check_context_budget.py` pass.
  - `pytest tests/tooling/test_check_docs_indexed.py tests/tooling/test_check_context_budget.py
    tests/tooling/test_check_no_em_dash.py tests/ingestion/test_constituent_seeds.py` pass
    (the last one covers `ingestion/constituents/refresh.py`, the one code file touched).
  - Required reviewers per `.claude/review_routing.json`: scope-auditor (always),
    cto-reviewer (`.claude/review_routing.json` itself), data-engineer-reviewer
    (`ingestion/*`, `supabase/*`), analytics-engineer-reviewer (`*.sql`) -- all PASS.

impact_map: doc/title/comment text only, plus one User-Agent string constant in
  `ingestion/constituents/refresh.py` (no behavior change, just the string value). No
  schema, data, or CI-mechanism change -- the two `.sql` files are already-applied
  migrations, edited only in their header comment.
