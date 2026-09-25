# Task contract
> DISPOSABLE. **Owns:** THIS task's objective, `scope_paths`, reserved decisions and
> `done_when`.
> **Never:** anything that outlives the task. Overwritten by the next task.

objective: Closes #28 -- after `git clone`, one setup command and one proof command that
  passes without credentials; the README says what credentials go where; CI proves the setup
  on a clean machine.

scope_paths:
  - scripts/bootstrap.py
  - scripts/seed_ci_raw_fixtures.py
  - scripts/write_ci_dbt_profile.py
  - tests/tooling/test_bootstrap.py
  - tests/tooling/test_write_ci_dbt_profile.py
  - tests/tooling/test_seed_ci_raw_fixtures.py
  - tests/tooling/test_ci_reachability.py
  - .pre-commit-config.yaml
  - .gitlab-ci.yml
  - .devcontainer/devcontainer.json
  - .env.example
  - .gitignore
  - .streamlit/secrets.toml.example
  - .claude/launch.json
  - frontend/app.py
  - scripts/check_no_narrative_dates.py
  - tests/tooling/test_check_no_narrative_dates.py
  - scripts/check_no_em_dash.py
  - requirements-dev.txt
  - .mcp.json
  - README.md
  - docs/development_workflow.md
  - docs/streamlit_deploy.md
  - docs/supabase_setup.md
  - docs/engineering_standards.md
  - .claude/active_work.md
  - .claude/task/contract.md
  - .claude/task/review.md

decisions_reserved: settled by the owner before implementation (issue #28 "Decisions taken"):
  tool/community convention unless a written repo-specific reason says otherwise; upstream
  gitleaks pre-commit hook at a pinned version, CI image pinned to the same tag; remote renamed
  `origin` -> `gitlab` by setup; no interactive credentials mode; default tool caches. Anything
  else that adds a mechanism, dependency or CI cost goes back to the owner.

done_when:
  - A fresh clone into a short folder: `python scripts/bootstrap.py` twice (the second run changes
    nothing), then `python scripts/bootstrap.py --verify` passes; output shown in the MR.
  - `tests/tooling/test_bootstrap.py` covers idempotency, never-overwrite, the remote-rename
    condition, no URL or key in output, and that the proof never points at `storage/raw`.
  - CI green on the MR, including `validate:pre-commit` and `setup:clean-clone`;
    `test_ci_reachability.py` passes.
  - `pytest tests/`, `check_no_em_dash.py`, `check_no_narrative_dates.py`,
    `check_context_budget.py`, `check_docs_indexed.py` pass; review cycle run; MR opened. Not
    merged. The proof folder is deleted afterwards.

amendments:
  - Owner chose option A: delete `.streamlit/secrets.toml.example` and change the missing-key
    error in `frontend/app.py` to "Set them in .env (see README "Getting started")."; scope
    gained `frontend/app.py`. UX PR gate: copy-only change, no layout.
  - A CI clone keeps `origin` (scripts/check_no_em_dash.py fetches the MR base from it); only
    developer clones are renamed to `gitlab`.
  - Round 1: scope-auditor PASS (one wording fix); platform-reviewer FAIL on three behaviour
    findings: the in-project pre-commit cache made no-narrative-dates scan pip's own files;
    `.gitlab-ci.yml` missing from `.setup_paths`; removing `check-yaml --unsafe` was out of
    scope (reverted). Owner approved widening scope to `check_no_narrative_dates.py` (exclude
    `.cache`) and its test, `check_no_em_dash.py` and `requirements-dev.txt` (stale comments),
    and the `.gitlab-ci.yml` trigger.
