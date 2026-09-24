# Task contract
> DISPOSABLE. **Owns:** THIS task's objective, `scope_paths`, reserved decisions and
> `done_when`.
> **Never:** anything that outlives the task. Overwritten by the next task.

objective: Closes #26 -- the repo owns its Claude Code guardrails (hooks, reviewer roles), so a
  fresh clone runs the review gate, pre-push gate, branch discipline and handover with nothing
  installed under the home folder.

scope_paths:
  - .claude/hooks/_command_utils.py
  - .claude/hooks/branch_discipline.py
  - .claude/hooks/commit_review_gate.py
  - .claude/hooks/pre_push_gate.py
  - .claude/hooks/handover_in.py
  - .claude/agents/platform-reviewer.md
  - .claude/agents/scope-auditor.md
  - .claude/agents/analytics-engineer-reviewer.md
  - .claude/agents/data-engineer-reviewer.md
  - .claude/settings.json
  - .claude/review_routing.json
  - .claude/working-agreement.md
  - .claude/active_work.md
  - tests/tooling/claude_hooks/
  - CLAUDE.md
  - README.md
  - docs/working_agreement.md
  - .claude/task/contract.md
  - .claude/task/review.md

decisions_reserved: settled by the owner in-thread before implementation -- decision rule is the
  tool/community convention unless a written repo-specific reason says otherwise; the repo owns
  its guardrails (no runtime dependency on dbt-agent-kit or claude-project-kit); copy only the
  four wired hooks plus their imports; platform-reviewer replaces cto-reviewer; credential-file
  deny rules; hook matcher stays `Bash` (PowerShell is out of scope).

done_when:
  - `.claude/settings.json` references only `${CLAUDE_PROJECT_DIR}/.claude/hooks/*.py`, and every
    referenced script exists (enforced by a test).
  - handover cap 32000 bytes and the worktree handling (leading `cd`, then the event's `cwd`,
    each resolved to its git toplevel; a `cd` target may be Git Bash `/c/...`, `~/...` or
    relative) are each covered by a test. `$VAR` targets and `git -C` are a follow-up issue.
  - `review_routing.json` names only reviewers with a role file in `.claude/agents/`.
  - In a new Claude Code session on this branch: a Bash tool call runs; the handover is injected;
    `git commit` without a matching `review.md` is blocked.
  - `pytest tests/`, `check_no_em_dash.py`, `check_no_narrative_dates.py`,
    `check_context_budget.py`, `check_docs_indexed.py` pass; review cycle run; MR opened with
    the kit commit SHA in the commit message. Not merged.

amendments:
  - scope_paths gained `docs/working_agreement.md` (it also called the kit a plugin).
  - Round 1: scope-auditor PASS; platform-reviewer FAIL on one behaviour finding (no test for
    the leading-`cd` root in commit_review_gate.py) plus six wording fixes (stale references to
    kit-only files and plugin paths, wrong test run paths, branch_discipline's fail-open
    sentence). Round 2 reviews the fixes.
  - Round 2: scope-auditor PASS; platform-reviewer FAIL on one behaviour finding present since
    round 1 (the worktree fix lacked the old copies' event-`cwd` layer; done_when had narrowed
    to "leading `cd`") plus four wording fixes (`_staged_diff` comment, test_hooks_import
    docstring, a test name, "(Bash tool only)" in the working agreement). Round 3 reviews them.
  - Round 3: scope-auditor PASS; platform-reviewer FAIL on two behaviour findings (leading-`cd`
    tests sent no event `cwd`, so the cd-over-cwd order was untested; the CLAUDE_PROJECT_DIR
    fallback was not resolved to the toplevel, so `--diff-hash` from a subdirectory printed an
    empty-diff hash) plus two wording fixes. Owner answered "go" to a round 4 past the cap.
  - Round 4: scope-auditor PASS; platform-reviewer ESCALATE (a Git Bash `/c/...`, `~` or
    `$VAR` cd target, or `git -C`, is judged against the wrong checkout) plus three wording
    fixes. Owner answered: handle `/c/...`, `~` and relative targets now with tests; `$VAR`
    and `git -C` go to a follow-up issue; run round 5 past the cap.
  - Round 5: scope-auditor PASS; platform-reviewer FAIL on one behaviour finding new in round 5
    (no test that command_root joins a relative `cd` target to the event `cwd`) plus three
    wording fixes (two test docstrings, the handover cap comment).
