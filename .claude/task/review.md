# Review

> DISPOSABLE. **Owns:** THIS task's reviewer verdicts and the staged-diff hash they were
> given against.
> **Never:** a rule. Overwritten by the next task.

diff_sha256: ab3a907f5eac302de87063c618df49c7c891bbe1e38347a344e403e4186ede2b

Two reviewers, by routing: scope-auditor (`always`), cto-reviewer (`scripts/*`, `tests/*`).
One round.

## What shipped

Issue #8. `scripts/sync_dbt_vars.py` raises `BlockNotFound` when `dbt_project.yml` has no
`active_market_codes` block; `main` prints the reason and "nothing written" on stderr and
exits 1, where it printed "already in sync" and exited 0. Three tests over temp files; the
missing-block test fails against the old script. 689 tests.

## scope-auditor

VERDICT: PASS

## cto-reviewer

VERDICT: PASS

## Owner decisions

None. No caller chains on the script's exit status (`.gitlab-ci.yml` does not run it;
`check_registry_var_sync.py` only names it).
