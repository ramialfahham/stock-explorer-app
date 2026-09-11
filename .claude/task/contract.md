# Task contract
> DISPOSABLE. **Owns:** THIS task's objective, `scope_paths`, reserved decisions and
> `done_when`.
> **Never:** anything that outlives the task. Overwritten by the next one.

objective: Put a byte budget on every context file and make CI fail when one is exceeded or
  when a context file exists with no budget, so growth and new files become visible, reviewed
  decisions instead of drift.

  Owner-approved after MR !119 measured the ownership pass at net +1,222 bytes: a convention
  nobody enforces will drift again, and a budget stops recurrence where a sweep removes text
  once.

scope_paths:
  - docs/context_budget.yml
  - scripts/check_context_budget.py
  - tests/tooling/test_check_context_budget.py
  - .gitlab-ci.yml
  - .pre-commit-config.yaml
  - .claude/review_routing.json
  - docs/engineering_standards.md
  - docs/development_workflow.md
  - .claude/task/contract.md
  - .claude/task/review.md
  - .claude/active_work.md

decisions_reserved:
  - The mechanism itself (a new CI step) is §6 and was asked and answered: yes.
  - The budget numbers. Proposed: each governed file's current size rounded UP to the next
    1,000 bytes, plus 1,000. Archives (`docs/handover_*.md`) get their current size rounded up
    and no headroom, because an archive is not written to. `.claude/active_work.md` gets 32,000,
    the cap `handover_in.py` already enforces. `.claude/task/contract.md` and `review.md` get a
    flat 8,000 each: they are rewritten per task, so their current size says nothing. Several
    recent committed reviews exceeded 8,000 bytes (`git log -- .claude/task/review.md`, sizes via
    `git cat-file -s`). 8,000 is kept knowing that: a review that long is the narrative §2
    forbids, and the budget is meant to refuse it. When it fires, the review blocks its own
    commit and the fix is to trim the review, not to raise the number. Size is measured with
    CRLF collapsed to LF, so Windows pre-commit and Linux CI agree. Raising any budget is an
    edit to `docs/context_budget.yml`, which routes to cto-reviewer, so every increase is
    reviewed.
  - Which files are governed. Proposed: `CLAUDE.md`, `.claude/*.md`, `.claude/task/*.md`,
    `docs/*.md`, `docs/ui/*.md`. Fail closed: a Markdown file matching those globs with no
    budget entry fails the check, and a budget entry whose file does not exist fails it too.

done_when:
  - `python scripts/check_context_budget.py` exits 0 on the tree as committed and prints one line
    per file over budget or unbudgeted, with the size and the budget, when it fails.
  - Mutation-proven in `tests/tooling`: a file one byte over its budget fails; a governed file
    with no entry fails; an entry with no file fails; a file exactly at budget passes.
  - The check runs in `validate:full` before the dbt steps and as a `repo: local` pre-commit
    hook, so it fails on the developer's machine before it fails in CI.
  - `docs/context_budget.yml` routes to cto-reviewer in `.claude/review_routing.json`.
  - `docs/engineering_standards.md` §1.3 states the rule in one paragraph: to grow a context
    file past its budget, raise the budget in the same MR and say why in the MR description.

impact_map: New CI step and pre-commit hook; no data, schema or frontend change. The risk is a
  budget set so tight that the next honest edit to a doc fails CI for the wrong reason, which is
  why every non-archive budget carries at least 1,000 bytes of headroom.
