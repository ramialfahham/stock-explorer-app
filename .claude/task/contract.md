# Task contract
> DISPOSABLE. **Owns:** THIS task's objective, `scope_paths`, reserved decisions and
> `done_when`.
> **Never:** anything that outlives the task. Overwritten by the next task.

objective: MR !157 (`growth-copy-remove-noisy-framing`) has a real merge conflict against
  `main`: two other MRs from the same portfolio-grade push (!156, item 10's crash-risk close;
  !158, `accepted_range` sanity guards) merged first, and all four branches touched the same
  disposable state files (`.claude/task/contract.md`, `.claude/task/review.md`) and (for three
  of the four) `.claude/active_work.md`. Resolving: `.claude/task/contract.md`/`review.md`
  take this branch's own version (disposable, overwritten by whichever task merges last, per
  the working agreement). `.claude/active_work.md` auto-merged with no conflict this time (the
  three edits touch different paragraphs); collapsed the now-stale "Smaller open items... MRs
  open... none merged yet" line and the full `accepted_range` paragraph (now merged content,
  detail already in `docs/data_contract.md`) to one or two lines each, matching this file's
  own documented convention, the same collapse already applied when resolving MR !155's
  identical conflict. `docs/data_contract.md` auto-merged cleanly (different sections).
  `dbt_analytics/models/5_marts/_marts.yml` and `docs/context_budget.yml` are pure pass-through
  from `main` (the `accepted_range` work's already-reviewed and already-merged content, MR
  !158) -- untouched by this resolution.

scope_paths:
  - .claude/active_work.md
  - .claude/task/contract.md
  - .claude/task/review.md
  - docs/data_contract.md
  - dbt_analytics/models/5_marts/_marts.yml
  - docs/context_budget.yml

decisions_reserved: none -- a merge-conflict resolution, no new decision made.

done_when:
  - No conflict markers remain in any file.
  - `.claude/active_work.md` reflects current reality (which MRs merged, which are still open
    and why) with nothing lost, duplicated, or stale.
  - `dbt_analytics/models/5_marts/_marts.yml` and `docs/context_budget.yml` match `main`
    exactly (pure pass-through).
  - `pytest tests/ -q` and `pytest tests/tooling/test_check_context_budget.py -q` green.
  - No em-dash/en-dash introduced on any line this resolution touched.

impact_map: no new logic, no new decision. The only genuinely new content is the merged/
  collapsed prose in `.claude/active_work.md`; everything else in the diff (relative to this
  branch's pre-merge tip) is content already reviewed and merged into `main` on its own
  branch.
