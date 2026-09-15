# Task contract
> DISPOSABLE. **Owns:** THIS task's objective, `scope_paths`, reserved decisions and
> `done_when`.
> **Never:** anything that outlives the task. Overwritten by the next task.

objective: MR !157 (`growth-copy-remove-noisy-framing`) had its first merge conflict against
  `main` resolved (previous round), but `main` moved again before it could be merged: MR !155
  (the doc-wording nit) merged in the meantime, touching the same disposable state files this
  branch also touches. `git merge gitlab/main --no-edit` surfaced a second round of conflicts
  in `.claude/active_work.md`, `.claude/task/contract.md`, `.claude/task/review.md`.
  `.claude/task/contract.md`/`review.md` resolved to this branch's own version again (same
  convention as every prior round). `.claude/active_work.md` needed a real merge: updated the
  "Smaller open items" summary to reflect !155 now genuinely merged (three of four items done,
  only this branch's own !157 still open), and dropped the now-stale "Doc wording, three
  reviewers noted, not fixed" note (main's side already removed it, correctly, since !155
  fixed exactly that) while keeping the collapsed `accepted_range` side-finding. Added !155 to
  the "Merged this pass" list. `docs/data_contract.md` auto-merged cleanly.

scope_paths:
  - .claude/active_work.md
  - .claude/task/contract.md
  - .claude/task/review.md
  - docs/data_contract.md

decisions_reserved: none -- a merge-conflict resolution, no new decision made.

done_when:
  - No conflict markers remain in any file.
  - `.claude/active_work.md` reflects current reality: !155, !156, !158 merged; !157 still
    open and why.
  - `docs/data_contract.md` matches `main` exactly (pure pass-through, this branch never
    touches it).
  - `pytest tests/ -q` and `pytest tests/tooling/test_check_context_budget.py -q` green.
  - No em-dash/en-dash introduced on any line this resolution touched.

impact_map: no new logic, no new decision. Only genuinely new content is the merged prose in
  `.claude/active_work.md`; everything else in the diff (relative to this branch's pre-merge
  tip) is content already reviewed and merged into `main` on its own branch.
