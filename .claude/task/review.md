# Review — Agent-setup hygiene branch (chore/agent-setup-hygiene)

diff_sha256: 6e0a116fae7734cab349a286914c52665934a636e22c86ac511164a53efddeaf

**Change under review (4 files):** force-load `.claude/working-agreement.md` from
`CLAUDE.md` via `@`-import instead of a passive pointer; pin `.mcp.json`'s `dbt-mcp`
server to `==1.22.1`; trim `.claude/active_work.md` to fit `handover_in.py`'s
SessionStart injection cap and correct its stale "MR open" status for Slice 5b/6a (both
already merged into `main`) and an unverified "in production" claim; archive the full
pre-trim history losslessly to `docs/handover_2026-08-18.md`.

**Outcome: both required reviewers PASS after three rounds** (two rounds with real,
substantive findings — not process noise). See `.claude/task/contract.md`'s `amendments`
for the full round-by-round record.

## What the three rounds actually found and fixed

1. **scope-auditor FAIL (round 1)** — the global `~/.claude/settings.json` hook
   registration (`commit_review_gate.py`, `pre_push_gate.py`, `handover_in.py`, plus the
   `MAX_BYTES` 16000→32000 bump) was narrated in `active_work.md` as already-done fact
   with no `decisions_reserved` acknowledgment or recorded authority — an owner-level,
   global-blast-radius action per `.claude/working-agreement.md` §6. Fixed: `contract.md`
   amended to name the action explicitly and record that it was authorized by the owner,
   action-by-action, in-session (not a repo-trackable artifact, since it's user-global
   config, not project config).
2. **cto-reviewer FAIL (round 1)** — `docs/handover_2026-08-18.md` was referenced by
   `active_work.md`'s new archive pointer but was untracked/unstaged, meaning a commit at
   that point would leave the link pointing at a file absent from the commit. The archive
   doc's header also wrongly stated the injection cap as "16KB" when the live, actually
   wired hook (`~/.claude/hooks/handover_in.py`) has `MAX_BYTES = 32000` — only two
   dormant source copies (plugin cache, plugin marketplace) still say 16000. Fixed: the
   file was `git add`-ed for real and `review_input.patch` regenerated from
   `git diff --staged`; the header reworded to state 16000 was the cap "at the time the
   overflow was diagnosed," note the raise to 32000, and point to a new
   Context/open-items bullet in `active_work.md` naming all three cap locations and their
   values (a real drift risk: a future plugin reinstall from either dormant copy would
   silently revert the cap).
3. **scope-auditor FAIL (round 2)** — `active_work.md`'s Current-task section claimed the
   merged Router/health-verdict/Haiku-read work "are in production," contradicted by the
   same file's own Infra section (Streamlit deploy path from GitLab unresolved, CI/CD
   variables/pipeline schedule unverified). "Merged into main" was being conflated with
   "live for real users." Fixed: reworded to "are complete and merged, code-wise. Whether
   they're actually live for real users is a separate, unconfirmed question — see the
   Infra section for the unresolved Streamlit deploy path and unverified CI/CD
   variables."
4. **Round 3 — both PASS** against the final staged diff. cto-reviewer additionally
   verified: the dbt-mcp pin resolves on PyPI and matches what was already being
   resolved (not a version bump in disguise); the archive doc is a byte-exact, unaltered
   snapshot of the pre-trim file; no secrets anywhere in the diff; no hook/CI/plugin files
   touched in-repo. scope-auditor additionally verified: scope is exactly the 4 contracted
   files and matches `review_routing.json`'s routing; the "in production" fix didn't
   relocate the same overstatement elsewhere in the file.

## scope-auditor
VERDICT: PASS
risks_checked:
- Scope exactness — diffed the actual staged tree (`git diff --cached --stat`) against
  `contract.md`'s `scope_paths` and against `.claude/review_routing.json`'s routing
  rules; the 4 changed files match exactly, and the required-reviewer set
  (scope-auditor + cto-reviewer) is correctly triggered by `.mcp.json`, not just
  asserted in `done_when`.
- Archive fidelity — diffed `docs/handover_2026-08-18.md` against
  `git show <merge-base>:.claude/active_work.md` byte-for-byte; the archive is a
  faithful, unaltered snapshot, and its stated file-size rationale (34KB old / 17KB new
  / 16000→32000 cap) checks out against real `wc -c` output rather than being asserted
  prose.

## cto-reviewer
VERDICT: PASS
risks_checked:
- New mechanisms — checked `.mcp.json` (version pin only, no new server/tools/env) and
  `CLAUDE.md`'s `@`-import (native existing Claude Code feature per the contract's own
  justification, not a new external mechanism) — held.
- Secrets — grepped the full staged diff for key/secret/token/password/bearer patterns;
  every match is a variable name in prose, never a value — held.
- Diff scope — `git diff --staged --stat` shows exactly the 4 contracted files, and the
  staged tree is byte-identical to `review_input.patch` — held.
- Guard integrity — no hook, CI, or plugin files touched in-repo; the global
  hook-registration change is correctly kept out of `scope_paths` and matches the
  contract's authorization narrative — held.
