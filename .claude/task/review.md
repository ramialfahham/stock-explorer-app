# Review — Agent-setup hygiene branch (chore/agent-setup-hygiene), commit 3

diff_sha256: 1bd49a48a58a2908008d393eba16028c2c9f45e0e034a90eb8f7fa8b79757998

**Change under review (1 file):** harden `.claude/review_routing.json` with 4 new
`paths` entries — `.claude/settings.json`, `.claude/agents/*`, `.claude/review_routing.json`
itself, and `.gitlab-ci.yml` — all routed to the existing `cto-reviewer` role. Modeled
on football-data-pipeline's more mature routing, at the owner's direct request after
seeing that sibling project catch a class of gap this repo's routing didn't.

Deliberately NOT ported: football-data-pipeline's `hash_exclude_paths`/`protected_override`
mechanism (needs code changes to `commit_review_gate.py`, not a config change — the shared
hook only reads `always`/`paths`/`artifact_only`/`artifact_only_never`) and its
`platform-reviewer`/`bi-analyst-reviewer` role split (would introduce new reviewer roles
this repo doesn't have). Both flagged to the owner as separate, larger options — not
decided here.

**Outcome: scope-auditor + cto-reviewer PASS after three rounds** (rounds 7 and 8 both
real findings, not process noise — see `.claude/task/contract.md`'s amendments for the
full record).

## What rounds 7-9 found and fixed

1. **Round 7 FAIL, both reviewers independently, same root issue** — rationale ported
   from football-data-pipeline without verifying it holds in this repo. (a)
   `.claude/agents/*`'s comment claimed it protects "the adversary" (cto-reviewer,
   scope-auditor, etc.); verified false — this repo's `.claude/agents/` contains only
   `equity-analyst-reviewer.md`, the other four roles live entirely outside the repo in
   the dbt-agent-kit plugin's `agents/` dir, invisible to any repo-scoped gate. (b) the
   self-referential `review_routing.json` route claimed a same-commit weaken-and-exploit
   gets "caught by the reviewer it's trying to route around"; verified false —
   `commit_review_gate.py` reads the file from its current staged state with no baseline
   pinning. Fixed: comment rewritten to state both limitations honestly — the routing
   rules themselves are unchanged and still worthwhile, only the documentation of what
   they accomplish was corrected.
2. **Round 8 FAIL (scope-auditor)** — the fix comment's own opening sentence claimed the
   problem was "corrected twice by review... both rounds caught claims," but only round 7
   had happened when that sentence was written — the same self-referential-drift defect
   class as rounds 1, 2, and 5 of this branch's first commit, reintroduced inside the text
   written to fix a different instance of it. cto-reviewer independently PASSed the same
   diff (re-verified both round-7 facts, held). Fixed: reworded to accurately describe
   only round 7's single round, two claims, both reviewers failing independently.
3. **Round 9 — both PASS.** Every factual claim in the comment (file locations, plugin
   paths, hook behavior, CI file existence) independently re-verified against the live
   filesystem and hook source by both reviewers, not re-read as prose.

## scope-auditor (final round)
VERDICT: PASS
risks_checked:
- The corrected round-log sentence's factual accuracy against `contract.md`'s actual
  round-7 entry — matches exactly, no premature/false claim about review outcomes,
  unlike the round-8 defect it replaces.
- Every checkable factual claim in the comment (`.claude/agents/` contents, the four
  reviewer roles' plugin-only location, `.github` non-existence, `.gitlab-ci.yml`
  existence, and `commit_review_gate.py`'s no-baseline-pinning behavior) verified
  directly against the filesystem and live hook source — all held, none fabricated.

## cto-reviewer (final round)
VERDICT: PASS
risks_checked:
- New mechanism / boring technology: confirmed the diff introduces no new dependency,
  hook, lifecycle step, or reviewer role — it only adds four `paths` patterns to the
  existing fnmatch-based routing table, all pointing at the pre-existing `cto-reviewer`
  role.
- Guard integrity / factual accuracy: verified every concrete claim in
  `_comment_guard_paths` against live state — `.claude/settings.json` contents,
  `.gitlab-ci.yml` presence, `.claude/agents/` contents, the four reviewer roles' actual
  location outside the repo, and `commit_review_gate.py`'s lack of baseline pinning — all
  held true.
- Fail-open/closed class: re-read `commit_review_gate.py`'s `main()` — still wraps
  `_gate()` in a bare `except Exception: return 0`, so the guardrail hook this routing
  file feeds remains fail-open; this diff does not touch or weaken that.

---

## Prior rounds (commits 1-2 of this branch — kept for context)

Commit 1 (`fab79de`, diff_sha256 `6e0a116fae7734cab349a286914c52665934a636e22c86ac511164a53efddeaf`):
three rounds, two with real findings (unauthorized-looking global hook note, unstaged
archive file, stale cap claim, "in production" overstatement).

Commit 2 (`7cbc467`, diff_sha256 `ff0a49bc4c82e5480c624cd4b11316d2c7ba1e3ac441422261627b36535cdfff`):
three more rounds, two with real findings (stale "wired globally" claim, undercounted
commit history).

Full detail of both is in `.claude/task/contract.md`'s amendments log, since this file
only carries the latest commit's full detail going forward.
