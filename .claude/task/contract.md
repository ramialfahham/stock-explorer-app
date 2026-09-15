# Task contract
> DISPOSABLE. **Owns:** THIS task's objective, `scope_paths`, reserved decisions and
> `done_when`.
> **Never:** anything that outlives the task. Overwritten by the next task.

objective: MR !155 (`docs/mart-stock-cards-table-heading`) has a real merge conflict against
  `main`: two other MRs from the same portfolio-grade push (!156, item 10's crash-risk close;
  !158, `accepted_range` sanity guards) merged first, and all four branches touched the same
  disposable state files (`.claude/active_work.md`, `.claude/task/contract.md`,
  `.claude/task/review.md`). Resolving: `.claude/task/contract.md`/`review.md` take this
  branch's own version (disposable, overwritten by whichever task merges last, per the
  working agreement). `.claude/active_work.md` needed a real content merge -- MR !155's own
  edit (dropping the stale "doc wording, three reviewers noted" line, since this MR is that
  fix) combined with main's now-merged `accepted_range`/item 10 closures, without losing
  either side. `docs/data_contract.md` auto-merged cleanly (the two changes touch different
  sections). `dbt_analytics/models/5_marts/_marts.yml` and `docs/context_budget.yml` are pure
  pass-through from `main` (the `accepted_range` work's already-reviewed and already-merged
  content, MR !158) -- untouched by this resolution, just newly present in this branch's
  history. (A prior round of this same resolution called this work "item 4"; that was a
  mislabeling -- the file's own numbered list already uses "item 4" for an unrelated,
  pre-existing UX bug-fix item -- caught by equity-analyst-reviewer and fixed here and on MR
  !157's identical conflict.)

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
  - `.claude/active_work.md` correctly reflects both sides: MR !155's own change and main's
    already-merged `accepted_range`/item 10 closures, with nothing lost or duplicated.
  - `docs/data_contract.md`'s two changes (MR !155's heading fix, main's `accepted_range`
    documentation) both present and uncorrupted.
  - `dbt_analytics/models/5_marts/_marts.yml` and `docs/context_budget.yml` match `main`
    exactly (pure pass-through, nothing this branch should have changed).
  - `pytest tests/ -q` and `pytest tests/tooling/test_check_context_budget.py -q` green.
  - No em-dash/en-dash introduced on any line this resolution touched.

impact_map: no new logic, no new decision. The only genuinely new content is the merged
  prose in `.claude/active_work.md`; everything else in the diff (relative to this branch's
  pre-merge tip) is content already reviewed and merged into `main` on its own branch.
