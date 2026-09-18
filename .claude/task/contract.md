# Task contract
> DISPOSABLE. **Owns:** THIS task's objective, `scope_paths`, reserved decisions and
> `done_when`.
> **Never:** anything that outlives the task. Overwritten by the next task.

objective: Update `.claude/working-agreement.md` SS3 to record a settled owner decision:
  the GitHub account is recovered (previously suspended, which is why this repo moved to
  GitLab-only), and the owner decided -- for this project specifically, not as a
  standing rule for every project -- that GitLab stays canonical (all agent work, CI,
  branches, MRs) with a one-way push mirror to GitHub for portfolio visibility, set up by
  the owner directly in GitLab's UI (needs a GitHub credential, not agent-executable).
  This resolves the rule's own "revisit only if that account is recovered" trigger, which
  has now fired.

scope_paths:
  - .claude/working-agreement.md
  - .claude/active_work.md
  - .claude/task/contract.md
  - .claude/task/review.md

decisions_reserved: none -- the owner made this call directly in chat.

done_when:
  - SS3 no longer frames GitLab-only as conditional on GitHub being suspended (that
    condition resolved); states instead that GitLab is canonical by settled choice, with
    GitHub as a one-way mirror.
  - "Do not add an origin remote or push to one" stays, re-grounded in the real current
    reason (pushing directly would fight or duplicate the mirror, not because the account
    is unreachable).
  - `python scripts/check_no_em_dash.py` passes.

impact_map: one paragraph in one durable doc. No code, no CI, no mirror actually
  configured (that's the owner's own GitLab UI + GitHub token, outside this repo's git
  history entirely).
