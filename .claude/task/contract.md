# Task contract
> DISPOSABLE. **Owns:** THIS task's objective, `scope_paths`, reserved decisions and
> `done_when`.
> **Never:** anything that outlives the task. Overwritten by the next task.

objective: `.mailmap` (owner's portfolio order; no issue). Every commit shows one author
  identity in `git log`, `git shortlog` and `git blame`.

scope_paths:
  - .mailmap
  - .claude/active_work.md
  - .claude/task/contract.md
  - .claude/task/review.md
  - .claude/task/review_input.patch

decisions_reserved: settled by the owner in-thread before implementation --
  Canonical identity (option B): `Rami Al-Fahham <rami.fahham@googlemail.com>`, the current
  git config, so new commits need no mapping. `rami.fahham@gmail.com` and the GitHub noreply
  address (both names) map to it.

known_limits: none.

regression_checklist:
  - `git shortlog -sne --all` shows exactly one author.

done_when:
  - `git shortlog -sne --all` lists one author, `Rami Al-Fahham <rami.fahham@googlemail.com>`,
    with every commit.
  - Pre-commit checks pass; review cycle run; MR opened. Not merged.

amendments:
