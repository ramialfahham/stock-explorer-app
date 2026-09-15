# Task contract
> DISPOSABLE. **Owns:** THIS task's objective, `scope_paths`, reserved decisions and
> `done_when`.
> **Never:** anything that outlives the task. Overwritten by the next task.

objective: Phase 2 of the owner-approved six-phase repo-cleanup plan (plan-mode review,
  2026-09-15). Two more written-but-unenforced rules get mechanical guards:
  1. **Em-dash rule** (`engineering_standards.md` §1.3): previously "nothing enforces it;
     it holds at review time only." Added `scripts/check_no_em_dash.py`, which diffs
     (staged locally, MR-target-branch merge-base in CI) rather than scanning the whole
     tree, since the rule is specifically about lines added or edited, not pre-existing ones
     -- a genuinely new mechanism, not a rerun of Phase 1's `check_no_narrative_dates.py`
     pattern, which whole-tree-scans unconditionally regardless of pipeline trigger. It
     caught a real self-violation while being built (an em-dash written directly into its
     own source instead of the intended U+2014 escape) and a second one in this task's own
     `CLAUDE.md` edit -- both fixed. cto-reviewer's round-1 review caught that the first CI
     design failed OPEN (silently skipped, exit 0) on every `push`-to-`main` and `web`
     pipeline -- the steady-state for two of `validate:full`'s three real triggers, not an
     edge case -- since `CI_MERGE_REQUEST_TARGET_BRANCH_NAME` is only set on merge-request
     pipelines. Fixed: added a `CI_COMMIT_BEFORE_SHA` fallback for push pipelines (guarded
     against the all-zero sentinel for a branch's first push), and changed the genuinely
     undeterminable case (a `web`-triggered manual run, a shallow clone missing history) to
     fail CLOSED instead of open, since a CI job that cannot tell what changed must not
     report green.
  2. **Doc-index completeness**: `CLAUDE.md` calls itself "the map... which file owns what,"
     but only 7 of 26 `docs/*.md`/`docs/ui/*.md` files had a line there. Added
     `scripts/check_docs_indexed.py`, mirroring `check_context_budget.py`'s "governed file
     with no entry fails" pattern. Since a new gate must ship already passing (the same
     principle Phase 1 followed), `CLAUDE.md`'s index is rebuilt to cover all 26 files in
     this same task, not deferred to Phase 6 as the plan file originally sketched --
     Phase 6's own doc-index item is now just keeping it current as later phases
     rename/delete files, not building it from nothing.
  Also fixed: `.claude/review_routing.json`'s own `_comment_guard_paths` field carried a
  date and an MR reference (the exact pattern Phase 1's checker targets, but JSON isn't a
  scanned file type by design -- a structural mismatch, not a checker bug) -- reworded by
  hand to state the current routing rationale without the date/MR-reference.

scope_paths:
  - scripts/check_no_em_dash.py
  - scripts/check_docs_indexed.py
  - tests/tooling/test_check_no_em_dash.py
  - tests/tooling/test_check_docs_indexed.py
  - .pre-commit-config.yaml
  - .gitlab-ci.yml
  - CLAUDE.md
  - docs/context_budget.yml
  - .claude/review_routing.json
  - .claude/task/contract.md
  - .claude/task/review.md
  - .claude/active_work.md

decisions_reserved: none -- mechanical enforcement of two already-written rules
  (`engineering_standards.md` §1.3, `CLAUDE.md`'s own "which file owns what" claim), plus a
  one-time wording fix to an already-approved routing-comment field. The mechanisms
  themselves were scoped and approved in the owner's plan-mode review before this branch
  existed.

done_when:
  - `python scripts/check_no_em_dash.py` passes against the staged diff; its 14 unit tests
    (hunk-header line tracking, context-vs-added distinction, multi-file diffs, the
    MR-target-branch and `CI_COMMIT_BEFORE_SHA` CI fallbacks against real git repos, and the
    fail-closed-in-CI / pass-locally split) all pass.
  - `python scripts/check_docs_indexed.py` passes against the full repo tree; its 11 unit
    tests pass.
  - `python scripts/check_no_narrative_dates.py` and `check_context_budget.py` still pass
    (unaffected by this task, checked for regression).
  - `pytest tests/ -q` green (776: 751 from Phase 1 + 25 new guard tests).
  - `.pre-commit-config.yaml` and `.gitlab-ci.yml` both run the two new checks alongside the
    existing two.
  - `.claude/review_routing.json` is still valid JSON; every routing pattern still matches
    what it matched before (wording-only change to one comment field).
  - No em-dash/en-dash introduced on any touched line (the two self-caught instances fixed).
  - The em-dash CI path fails closed, not open, when it cannot determine what changed --
    cto-reviewer's round-1 finding.

impact_map: two new guard scripts + their tests -- no behavior change to the application, no
  schema change. `CLAUDE.md` grows from 7 to 26 indexed docs (content-neutral -- links and
  one-line descriptions, not a rewrite of what each doc says); its budget raised 5000 -> 6500
  to fit. `.claude/review_routing.json`: one comment field reworded, routing patterns
  (`always`, `paths`, `artifact_only`, `artifact_only_never`) byte-identical.
