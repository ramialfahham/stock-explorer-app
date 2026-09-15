# Task contract
> DISPOSABLE. **Owns:** THIS task's objective, `scope_paths`, reserved decisions and
> `done_when`.
> **Never:** anything that outlives the task. Overwritten by the next task.

objective: `.claude/working-agreement.md` governs every agent action in this repo (the
  Explore-Plan-Confirm-Implement-Verify protocol, branch rules, decision rights) yet had no
  required reviewer beyond `always` (scope-auditor) -- a gap MR !116 itself exposed, since its
  only blocking correctness finding came from the reviewer routing did not require at the
  time. Owner decided (in chat, 2026-09-15): close this one gap only. The other two gaps
  recorded alongside it in `.claude/active_work.md` item 0 -- editing the dbt-agent-kit
  plugin's own `CONTRACT_TEMPLATE.md`/`REVIEW_TEMPLATE.md` (a separate repo entirely), and
  extending `~/.claude/hooks/branch_discipline.py` to also block `glab mr merge` (a
  machine-shared file affecting every project) -- are explicitly declined, not deferred: past
  global-file edits have broken sibling projects before, and the owner does not want that risk
  taken here.

scope_paths:
  - .claude/review_routing.json
  - .claude/task/contract.md
  - .claude/task/review.md
  - .claude/active_work.md

decisions_reserved:
  - Close only the review_routing.json gap; explicitly decline the other two MR !116
    sub-items (plugin templates, global merge-guard). Owner's call, in chat, 2026-09-15.

done_when:
  - `.claude/working-agreement.md` is a key in `review_routing.json`'s `paths`, routed to
    `["cto-reviewer"]`, matching the authority class of the other guard paths
    (`.claude/settings.json`, `*hooks/*`, `.claude/review_routing.json` itself).
  - The `_comment_guard_paths` rationale comment documents why, matching this file's own
    established convention of explaining every guard path inline.
  - `.claude/active_work.md`'s item 0 records (b) and (a) as declined, not left open, so a
    future session does not keep re-raising them.
  - `pytest tests/ -q` green; `.claude/review_routing.json` is still valid JSON.

impact_map: `.claude/review_routing.json` only -- a project-local config file, no code change,
  no cross-project reach. The two declined sub-items (plugin templates, global hook) are
  explicitly out of scope, not silently narrowed.
