# Review

> DISPOSABLE. **Owns:** THIS task's reviewer verdicts and the staged-diff hash they were
> given against.
> **Never:** a rule. Overwritten by the next task.

diff_sha256: f5051f01dd09aeaf796398e6f2f1aee6565c138ebae8679a7d4d0d0f04a210a2

Two reviewers, by routing: scope-auditor (`always`), cto-reviewer (`scripts/*`, `tests/*`,
`.gitlab-ci.yml`, `docs/context_budget.yml`, `.claude/review_routing.json`). Two rounds.

## What shipped

Phase 2 of the owner-approved repo-cleanup plan. Two more written-but-unenforced rules get
mechanical guards:

1. **Em-dash rule** (`engineering_standards.md` §1.3): added `scripts/check_no_em_dash.py`,
   diffing rather than whole-tree-scanning (locally: staged diff; in CI: MR-target-branch
   merge-base, falling back to `CI_COMMIT_BEFORE_SHA` for push pipelines), since the rule is
   about lines added or edited, not pre-existing ones. Caught two real self-violations while
   being built (an em-dash written directly into its own source instead of the intended
   escape, and one in this task's own `CLAUDE.md` edit) -- both fixed.
2. **Doc-index completeness**: added `scripts/check_docs_indexed.py` -- every `docs/*.md`/
   `docs/ui/*.md` file must be linked from `CLAUDE.md`. `CLAUDE.md`'s index was rebuilt from
   7 to 26 files so the new gate ships already passing, matching Phase 1's own precedent for
   how a new gate should land. Budget raised 5000 -> 6500 to fit.

Also fixed: `.claude/review_routing.json`'s own `_comment_guard_paths` field carried a date
and an MR reference, the exact pattern Phase 1's checker targets, invisible to it because
JSON isn't a scanned file type (a structural mismatch, not a checker bug) -- reworded by hand.

735 pre-existing tests, 15 from Phase 1, plus 25 new this phase: 776 total.

## Round 1

scope-auditor: PASS. Confirmed all 26 docs genuinely linked (spot-checked against the actual
file list), `.claude/review_routing.json`'s routing rules byte-identical apart from the one
comment field, both em-dash self-violations actually fixed.

cto-reviewer: FAIL, a real and substantive finding. `check_no_em_dash.py`'s CI-side diff
logic failed OPEN (silently skipped, exit 0) whenever `CI_MERGE_REQUEST_TARGET_BRANCH_NAME`
wasn't set -- the steady-state for `push`-to-`main` and `web`-triggered pipelines, two of
`validate:full`'s three real triggers, not an edge case. Also flagged the contract's claim
that this mechanism "matches Phase 1's precedent" was false -- Phase 1's
`check_no_narrative_dates.py` does unconditional whole-tree scanning with no diff/CI-fetch
logic at all; this is a genuinely new, unprecedented mechanism that needed its own scrutiny.

## Fix between rounds

- Added a `CI_COMMIT_BEFORE_SHA` fallback for push pipelines, guarded against the all-zero
  sentinel GitLab uses for a branch's first push, with a fetch-and-retry for a shallow clone
  missing that commit.
- Changed the genuinely-undeterminable case (no MR target, no usable before-SHA -- a
  `web`-triggered manual run, or a shallow clone missing history) from failing open to
  failing CLOSED: `main()` returns 1 in that case when `CI` is set, 0 only when running
  locally with nothing staged (benign, not a security gap).
- Reworded the contract's objective to drop the false precedent claim and record the finding
  and fix accurately.
- Added 6 new tests against real throwaway git repos (not mocks): MR-target merge-base,
  `CI_COMMIT_BEFORE_SHA` fallback, all-zero-SHA rejection, the fully-undeterminable case, and
  `main()`'s fail-closed-in-CI vs. pass-locally split.

## Round 2

cto-reviewer: PASS. Ran the two new pre-commit hooks through the actual `pre-commit` binary
(not just read the YAML), independently re-scanned the diff for em-dashes in a standalone
script, traced every code path in the new CI-fallback logic for a silent-green case and found
none, confirmed the contract's precedent claim is now accurate.

scope-auditor: PASS. Confirmed the fix's scope was correctly narrow (only the em-dash
checker, its tests, and the contract changed since round 1), 776 tests, all four guard
scripts green.

## scope-auditor

VERDICT: PASS

## cto-reviewer

VERDICT: PASS

## Owner decisions

None new -- the mechanisms themselves were scoped and approved in plan-mode review before
this branch existed.
