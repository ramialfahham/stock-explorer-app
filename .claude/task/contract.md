# Task contract
> DISPOSABLE. **Owns:** THIS task's objective, `scope_paths`, reserved decisions and
> `done_when`.
> **Never:** anything that outlives the task. Overwritten by the next task.

objective: Closes #21. Adds one rule to `.claude/working-agreement.md` §1: before
  restating an owner-flagged or "unconfirmed" claim from `.claude/active_work.md`,
  re-check it against the live source if a cheap check exists, instead of repeating the
  file's text as current. Prompted by issue #3 (ANTHROPIC_API_KEY) sitting marked
  "unconfirmed" for a session after it was actually already set -- nothing ever
  re-verified it. This is process guidance for how the agent reads its own handover file,
  not application code or a product decision -- no fresh owner call needed, it extends a
  principle the file already states for git ("trust `git log main` over a stale
  handover") to state outside git.

scope_paths:
  - .claude/working-agreement.md
  - .claude/task/contract.md
  - .claude/task/review.md
  - docs/context_budget.yml

decisions_reserved: none -- the owner explicitly asked for the cheap (rule, not
  automated-mechanism) version of this fix; the heavier option (a script/CI job) was
  named and declined.

done_when:
  - `.claude/working-agreement.md` §1 states the verify-before-restating rule.
  - `python scripts/check_context_budget.py` passes (budget raised 9000 -> 9200 after one
    trim pass, the checker's own sanctioned remedy).

impact_map: one paragraph in one durable doc. No application code, no schema, no CI
  change. Purely how the agent reads its own handover file going forward.
