# Task contract
> DISPOSABLE. **Owns:** THIS task's objective, `scope_paths`, reserved decisions and
> `done_when`.
> **Never:** anything that outlives the task. Overwritten by the next task.

objective: Owner asked for a short "about this project" note in the README framing it as
  an upskilling project with a clearly defined scope, worded so it doesn't sound modest or
  apologetic but also doesn't imply something larger was originally planned. Wording went
  through several rounds directly with the owner in chat; the final text below is theirs to
  approve, not mine to originate -- added verbatim as agreed.

scope_paths:
  - README.md
  - .claude/task/contract.md
  - .claude/task/review.md

decisions_reserved: none -- the exact wording was agreed with the owner in chat before this
  task started; nothing left to decide.

done_when:
  - README.md has the agreed "About this project" line placed right after the existing
    intro paragraph, before the badges.
  - `check_no_em_dash.py` and `check_context_budget.py` pass.
  - scope-auditor PASS (README.md is not routed to any content-specific reviewer per
    `.claude/review_routing.json`; only the "always" reviewer applies).

impact_map: README.md only. No code, no data, no CI change.
