# Review — Agent-setup hygiene branch (chore/agent-setup-hygiene), commit 2

diff_sha256: ff0a49bc4c82e5480c624cd4b11316d2c7ba1e3ac441422261627b36535cdfff

**Change under review (2 files):** wire `commit_review_gate.py`, `pre_push_gate.py`, and
`handover_in.py` into THIS repo's own `.claude/settings.json` (project-scoped), and
correct `active_work.md`'s self-narration to match — it still described the hooks as
"wired globally" and undercounted the branch's own commit history.

This supersedes an earlier, already-reviewed-and-passed attempt (rounds 1-3, recorded
below) that wired the same three hooks into the GLOBAL `~/.claude/settings.json` instead.
That global wiring broke a different, unrelated project (football-data-pipeline) — its
own review-gate hashing logic excludes bookkeeping paths the global hook doesn't know
about, so the two gates computed different hashes for the same commit and the global one
could block commits the project's own review had already passed. The owner reverted the
global wiring immediately on discovering this. This diff re-wires the exact same,
unmodified hook scripts project-scoped instead, which cannot leak into any other
project's session by construction.

**Outcome: scope-auditor PASS after three more rounds** (rounds 4 and 5 both real
findings, not process noise — see `.claude/task/contract.md`'s amendments for the full
record). `.claude/settings.json` does not match any `cto-reviewer` path in
`.claude/review_routing.json`, so scope-auditor is the only required reviewer for this
specific diff.

## What rounds 4-6 found and fixed

1. **Round 4 FAIL, finding 1** — `active_work.md` still said the hooks were "wired
   globally... as of 2026-08-18," directly contradicting this diff's own premise. Fixed:
   reworded to describe the project-scoped wiring and the global-revert history.
2. **Round 4 FAIL, finding 2** — `contract.md`'s `decisions_reserved` authorized *where*
   the hooks fire (global vs. project) but never addressed *whether to commit the wiring
   file to git at all* — a distinct axis from what was previously authorized, since this
   is the first time `.claude/settings.json` (as opposed to the pre-existing, gitignored
   `.claude/settings.local.json`) is tracked in this repo, and the hook commands reference
   a machine-specific `$HOME` path that wouldn't resolve if this repo were cloned
   elsewhere. Escalated directly to the owner via `AskUserQuestion` rather than decided by
   the agent; owner chose to commit it (tracked), accepting the portability caveat.
3. **Round 5 FAIL** — fixing finding 1 above left a stale claim sitting right next to it:
   `active_work.md`'s Next-concrete-actions item 4 said the branch had "Two commits,"
   already undercounted (a third had landed) and about to be wrong again (this commit
   makes a fourth). Same self-referential-drift defect class that failed rounds 1 and 2 of
   this task's first commit. Fixed structurally, not just re-counted: removed the
   hardcoded commit list/hashes, pointing to `git log`/the MR instead; also corrected "MR
   not yet opened" to "MR #5 open" (also stale).
4. **Round 6 — PASS.** Verified live via `glab`, not just re-reading prose: MR #5's
   state/URL match exactly, and the file's other MR references (#3, #4) were
   independently checked and both confirmed genuinely merged. Confirmed the global
   settings.json really doesn't wire these three hooks anymore, and the new
   project-scoped `.claude/settings.json` really does.

## scope-auditor (final round)
VERDICT: PASS
risks_checked:
- MR #5's existence/state/URL, and the file's other MR references (#3, #4) — verified
  live against GitLab via `glab`, not just asserted prose; all matched exactly, no
  staleness found anywhere in the file.
- Scope and decisions_reserved compliance — diffed the actual staged files against
  `contract.md`'s `scope_paths` (exact match) and against `.claude/review_routing.json`'s
  path patterns (no cto-reviewer route triggers, confirming the contract's `done_when`
  claim); confirmed no owner-level decision is made silently in this round's diff, since
  the project-scoped wiring and commit-it decisions are already recorded with owner
  authorization in the contract's amendments log.

---

## Prior rounds (commit 1 of this branch, `fab79de` — kept for context)

diff_sha256 (commit 1): `6e0a116fae7734cab349a286914c52665934a636e22c86ac511164a53efddeaf`

Three rounds (scope-auditor + cto-reviewer), two with real findings: an
unauthorized-looking global hook-registration note with no recorded owner authority
(fixed by naming the authorization explicitly), an archive file referenced but never
staged (fixed), a stale "16KB cap" claim after the cap was raised to 32000 (fixed), and
an "in production" overstatement for merged-but-unverified-live work (fixed). Both
reviewers PASS on the final round. Full detail was in this file's previous revision;
see `.claude/task/contract.md`'s amendments log for the complete record, since this file
only carries the latest round's full detail going forward.
