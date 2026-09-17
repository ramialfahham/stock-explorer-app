# Task contract
> DISPOSABLE. **Owns:** THIS task's objective, `scope_paths`, reserved decisions and
> `done_when`.
> **Never:** anything that outlives the task. Overwritten by the next task.

objective: Closes #5. Adds one rule to `.claude/working-agreement.md` §2 formalizing
  re-review re-dispatch scoping: only re-invoke a reviewer whose own routing-matched files
  changed since their last PASS on this task, not the full required set every round. This
  is process guidance for how the agent runs review cycles, not application code or a
  product decision -- no fresh owner call needed, since it formalizes the ad hoc judgment
  call this session already used correctly (e.g. issues #16, #19's later rounds).

  Issue #5 raised two further threads. One is resolved without a code change (recorded as
  a GitLab note on the issue, not repeated in this contract): the "discipline gap" (a fix
  landing in one place while the same claim stays wrong elsewhere) is already covered by
  an existing working-agreement.md rule ("grep the repo for the claim, not the file you
  were told about," added after MR !115's six wasted rounds).

  The second thread, "routing granularity by change significance," was explicitly flagged
  in the issue as needing the owner's call ("Flagging for the owner's call, not proposing
  an answer here"). An earlier version of this contract closed it by citing two
  prior-session incidents as equivalent evidence; a review round correctly rejected that
  as the "it's analogous to X" reasoning working-agreement.md SS6 forbids for this class
  of call, so the question was reopened (GitLab issue #5) and asked directly. Owner's
  answer: keep path-only routing, no significance heuristic -- `review_routing.json` is
  not changed. No new mechanism built.

scope_paths:
  - .claude/working-agreement.md
  - .claude/task/contract.md
  - .claude/task/review.md

decisions_reserved: none -- the one open question issue #5 reserved for the owner
  (routing granularity) was asked directly and answered: keep path-only routing.

done_when:
  - `.claude/working-agreement.md` §2 states the re-dispatch scoping rule.
  - `python scripts/check_context_budget.py` passes (this file's budget is tight, 9000
    bytes).

impact_map: one paragraph in one durable doc. No application code, no schema, no CI
  change. Purely how the agent conducts its own review cycles going forward.
