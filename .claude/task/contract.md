# Task contract
> DISPOSABLE. **Owns:** THIS task's objective, `scope_paths`, reserved decisions and
> `done_when`.
> **Never:** anything that outlives the task. Overwritten by the next task.

objective: Phase 4 of the owner-approved six-phase repo-cleanup plan
  (`C:\Users\Rami\.claude\plans\spicy-frolicking-bachman.md`): CI/config hygiene, 5 items, all
  fully specified in the plan file with no owner decision left open.

  1. **Dedupe the `~/.dbt/profiles.yml` heredoc.** Verified 3 near-identical copies in
     `.gitlab-ci.yml` (`validate:full`, `data-pipeline`, `dev-schema-check`), differing only
     in `path:`. New `scripts/write_ci_dbt_profile.py --path <path>` replaces each
     `mkdir -p "$HOME/.dbt"` + heredoc pair with one line.
  2. **Delete `scripts/check_not_on_main.py`.** Confirmed genuinely unused: grep found only
     `.gitlab-ci.yml`'s own stale comment (claiming it "keeps its local pre-commit role,"
     false -- `.pre-commit-config.yaml` already uses the generic `no-commit-to-branch` hook
     instead) and this task's own disposable files. No test file exists for it. Comment
     rewritten to state why `validate:branch-guard` doesn't reuse its branch-detection
     approach (detached HEAD in an MR checkout), without the now-false pre-commit claim.
  3. **Remove `.claude/review_routing.json`'s dead `"*schema.yml"` entry.** Verified it
     matches zero tracked files (`_marts.yml`/`_core.yml`/etc. are already covered by
     `"dbt_analytics/*.yml"`). `"*hooks/*"` left as-is per the plan (not this cleanup's call).
  4. **Pin `pytest` in `requirements-dev.txt`.** Added `pytest==9.1.1` (the version already
     installed and in use). Also changed `.gitlab-ci.yml`'s `pip install pytest` (unpinned, ad
     hoc) to `pip install pytest==9.1.1` so CI actually uses the pinned version, not just local
     dev -- the plan's stated problem ("CI installs it ad hoc and unpinned") isn't fixed by
     only adding the pin locally.
  5. **Pin `frontend/requirements.txt`'s floating `httpx>=0.27.0`.** Checked git history for a
     documented transitive-compatibility reason first (none found -- it's been floating since
     an early commit with no explanation). Per the plan's own fallback, pinned to the version
     currently resolved: `httpx==0.28.1`.

scope_paths:
  - .gitlab-ci.yml
  - scripts/write_ci_dbt_profile.py
  - tests/tooling/test_write_ci_dbt_profile.py
  - scripts/check_not_on_main.py
  - .claude/review_routing.json
  - requirements-dev.txt
  - frontend/requirements.txt
  - .claude/active_work.md
  - .claude/task/contract.md
  - .claude/task/review.md

decisions_reserved: none -- all 5 items and their resolution (including the httpx
  pin-vs-document fallback) are already specified in the owner-approved plan file; this task
  applies them, it does not choose among unresolved options.

done_when:
  - `scripts/write_ci_dbt_profile.py` replaces all 3 heredocs; each CI job's `path:` value is
    unchanged from today (`/tmp/stock_data_ci.db`, `storage/stock_data.db`,
    `/tmp/stock_data_dev_check.db`).
  - `scripts/write_ci_dbt_profile.py`'s own tests pass (writes correct YAML, creates the
    target directory if missing).
  - `scripts/check_not_on_main.py` deleted; `.gitlab-ci.yml`'s comment above
    `validate:branch-guard` no longer claims it has a live pre-commit role.
  - `.claude/review_routing.json` has no `"*schema.yml"` entry; still valid JSON; every
    remaining pattern still matches what it matched before.
  - `requirements-dev.txt` declares `pytest==9.1.1`; `.gitlab-ci.yml`'s `validate:full`
    installs that exact pin instead of unpinned `pytest`.
  - `frontend/requirements.txt`'s `httpx` line is `==0.28.1`, not `>=0.27.0`.
  - `pytest tests/ -q` green, no regression from the 776-test baseline (plus the new
    `write_ci_dbt_profile.py` tests).
  - `python scripts/check_docs_indexed.py`, `check_context_budget.py`,
    `check_no_narrative_dates.py`, `check_no_em_dash.py` (staged diff) all pass.
  - `.gitlab-ci.yml` is still valid YAML (parse-checked) and every job's script list is
    behaviorally identical except the profile-writing lines.

impact_map: CI config + dependency-pin + tooling-script change; no application code, dbt
  model, or schema change. `.gitlab-ci.yml` shrinks (3 heredocs -> 3 one-liners, ~24 lines
  removed). No new external dependency -- `write_ci_dbt_profile.py` uses only the stdlib.
