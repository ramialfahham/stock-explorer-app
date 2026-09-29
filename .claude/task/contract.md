# Task contract
> DISPOSABLE. **Owns:** THIS task's objective, `scope_paths`, reserved decisions and
> `done_when`.
> **Never:** anything that outlives the task. Overwritten by the next task.

objective: Closes #27 -- a commit by Claude Code is judged in the checkout git really acts
  on, however the command is spelled (`cd`, `git -C`, `$VAR`, worktree, PowerShell), by
  running the review gate as a git pre-commit hook; pushes to `main` are refused server-side.

scope_paths:
  - .claude/hooks/_command_utils.py
  - .claude/hooks/branch_discipline.py
  - .claude/hooks/commit_review_gate.py
  - .claude/hooks/powershell_git_guard.py
  - .claude/settings.json
  - .pre-commit-config.yaml
  - scripts/bootstrap.py
  - tests/tooling/claude_hooks/
  - tests/tooling/test_bootstrap.py
  - .claude/working-agreement.md
  - CLAUDE.md
  - .claude/active_work.md
  - .claude/task/contract.md
  - .claude/task/review.md

decisions_reserved: settled by the owner in-thread before implementation --
  Approach (option B): the review gate runs as a git pre-commit hook (`review-gate`, via
  pre-commit), only when `CLAUDECODE=1`; the owner's commits are unaffected. This replaces the
  text-parsing of `cd`/`git -C`/`$VAR` targets, so issue items 1 and 2 are met by git itself.
  D1: pushes to `main` are refused by GitLab (owner sets `main` to "Allowed to push: No one");
  no pre-push hook. D2: Claude-side hooks catch the usual spellings of a hook bypass
  (`--no-verify` and its prefixes, a commit short-flag bundle with `n`, `core.hooksPath`,
  `SKIP`, any `CLAUDECODE` change), not a command written to evade them; the MR review and
  GitLab protection are the backstop. PowerShell (option C narrowed by B): the PowerShell guard
  refuses only bypasses; git hooks gate PowerShell commits. Option A: quoted values keep their
  slot, so `git commit -m "msg" file.py` is refused by the pathspec rule. D3: scope includes
  `scripts/bootstrap.py` (`--verify` skips the gate, which guards commits, not files) and
  `CLAUDE.md`; shell redirections (`2>&1`) are not pathspecs, as on `main`.

done_when:
  - A real git commit through the `review-gate` hook via `git -C` from another folder is
    refused without a matching review.md and passes with one; commits without `CLAUDECODE=1`
    pass; a helper import error does not block a commit (tests).
  - `hook_bypass` refuses the listed bypasses in Bash and PowerShell spellings and passes
    `git log -n 5` and heredoc/quoted message text that mentions them (tests).
  - Working agreement §2/§3 and CLAUDE.md describe where each check runs, within budget.
  - GitLab `main` is "Allowed to push: No one" before commit (owner action, read back).
  - `python scripts/bootstrap.py --verify` passes; review cycle run; MR opened. Not merged.

amendments:
  - Rounds 1-2 reviewed the replaced text-parsing approach; round 3 reviewed B's first cut
    (both FAIL: bypass spellings, the pre-push hook's escapes and side effects, the stash
    hiding an unstaged review.md, git-hook modes failing closed, an invisible note, wording).
    Owner answered D1-D3 and approved round 4 past the cap.
  - Round 4: scope-auditor PASS (wording fixes); platform-reviewer FAIL on three false results
    inside D2/option A: PowerShell `Env:\NAME` not caught; a here-string message with an
    apostrophe read as a bypass; `-m"x"`-style attached values refused (a regression from the
    option-A placeholder). Fixed with tests. Following D1 (no pre-push hook), pushes are no
    longer scanned for bypasses: they skip nothing. Wording fixes from both reviewers applied.
  - Round 5: scope-auditor PASS (wording fixes, applied); platform-reviewer FAIL on four
    narrow cases inside D2: quoted PowerShell env names (`SetEnvironmentVariable('CLAUDECODE'`,
    `"Env:\SKIP"`) missed; `-mfinal`/`-uno` read as `-n`; `git config --get|--unset
    core.hooksPath` refused; a `claudecode` folder in a path refused. Fixed with tests
    (SKIP/CLAUDECODE now count on an assignment, an env-drive reference, `-u` or `unset`).
  - Owner (option B for round 6): round 6 verifies the round-5 fixes and looks for
    regressions; a new, previously unseen bypass spelling is filed as a follow-up issue
    instead of failing the round (D2); a false block of a normal commit or a design problem
    still fails it.
  - Round 6: both FAIL on one false block from round 5's fix (a quoted message mentioning
    `'Env:SKIP'` refused); fixed by counting a quoted name only right after a PowerShell
    set/remove call. platform-reviewer also: read-only `git config core.hooksPath`, `get`,
    `unset` refused (fixed: only a set counts), and a comment wording fix (applied). New
    bypass spellings filed as follow-up issue #29, per the owner's round-6 rule.
  - Owner: the review process itself is defective (a process issue follows separately).
    This MR finishes with one fixed-checklist verification round: each listed item is PASS or
    FAIL, nothing outside the list is in scope, no file changes while it runs; anything new
    goes to #29.
  - Fixed-checklist check: scope-auditor PASS (5/5); platform-reviewer 5/6, item 4 failed on a
    PowerShell here-string sent to the Bash hook. Fixed (quote stripping now removes
    here-string bodies, with a test); confirmation of that one fix only.
