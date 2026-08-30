# Review

diff_sha256: d3c5715dbb75be81ae454e278dacd63a7f7f4c120cc9e6f69077a31d6e06945d

One review round. Required reviewer per routing (`.claude/review_routing.json`): scope-auditor
(always). No other pattern in the routing matches this file set (a new `docs/backlog/*.md` file
plus `.claude/active_work.md` and `.claude/task/contract.md`), so no other reviewer is required.

**Reviewer dispatch:** the plugin's reviewer agent types are not registered as dispatchable in
this session, so scope-auditor ran as a general-purpose agent instructed to read its own role
file verbatim first. Cold, blinded, read-only input; the staged index was frozen to a patch file
and sha256 before dispatch and never moved while the reviewer was running.

**Final verdict (round 1, the commit gate):** scope-auditor PASS.

## What this is

Scopes Discover's first-time default scope as its own backlog item, per the owner's request.
The question was flagged in `docs/backlog/landing_onboarding_rework.md`'s "Still open" list as
deliberately not answered by `feat/kill-landing-screen`'s decision to delete the landing screen.
Adds `docs/backlog/discover_first_time_default.md`, matching the shape of the two earlier
scoping docs this session (`name_vs_yfinance_audit_guard.md`, `landing_onboarding_rework.md`):
current mechanism read directly from the code, open questions listed, candidate directions
sketched without ranking or recommending one. The doc's central finding: `feat/kill-landing-screen`
deleted `onboarding_dismissed`, the only piece of state that ever distinguished a returning
visitor from a first-time one, even though that flag was never wired to the Discover default
itself, so any "first-time only" version of a new default needs a signal that doesn't currently
exist anywhere in the codebase. Corrects `docs/backlog/landing_onboarding_rework.md`'s forward
reference to point at the new doc, and fixes a leftover stale status header in
`.claude/active_work.md` (the prior task's MR entry still said "MR !61 OPEN" after the MR had
already been merged and the branch cleaned up). Documentation only: no code, no CI, no new
dependency.

## Round-by-round findings and fixes

**Round 1**: passed clean. scope-auditor independently re-derived the doc's central technical
claim by diffing the pre-deletion version of `frontend/app.py` and `frontend/browser_storage.py`
against the current one, confirming `onboarding_dismissed` was genuinely the only other
localStorage-persisted key besides `interactions` and was never referenced by
`default_market_filter()` or `explore_market` anywhere. Given this session's history of two
prior reviewer catches where a similar scoping doc silently resolved an owner-reserved question,
the reviewer was asked to give that risk particular scrutiny: it read every candidate direction
and confirmed each carries an explicit tradeoff with no option presented as a recommendation,
and confirmed the one borderline phrase in the doc (that a uniform-default option is "much
cheaper... worth considering") stays inside a still-open question rather than answering it. Also
verified the "MR !61 OPEN" to "MR !61 MERGED" correction against actual git history (the merge
commit and the absence of any remaining `feat/kill-landing-screen` branch), not just internal
document consistency.

## scope-auditor
VERDICT: PASS
risks_checked:
- Every factual code claim in the new doc verified against live source and against a diff of the
  pre-deletion `frontend/app.py`/`frontend/browser_storage.py`: `default_market_filter()`
  unconditionally returns `ALL_MARKETS` with no branching logic anywhere; `EXPLORE_DEFAULTS_VERSION`
  is a session-state cache-bust mechanism, not a per-visitor flag; `onboarding_dismissed` was the
  only other localStorage-persisted key besides `interactions` and was never referenced by the
  Discover-default code path.
- No owner-reserved product/UX decision was silently made, checked with particular scrutiny
  given two prior catches of this exact pattern this session: all four candidate directions
  carry an explicit downside, none is ranked or recommended, and the contract's own
  decisions_reserved section reserves the same set of questions the doc leaves open.
- `docs/backlog/landing_onboarding_rework.md`'s edit is a pure one-line forward-reference
  correction, not new unrelated content; the relative link resolves to the file this same patch
  adds.
- `.claude/active_work.md`'s "MR !61 OPEN" to "MR !61 MERGED" correction is factually accurate,
  verified against actual git history (the merge commit, and no remaining branch), not just
  internal document consistency.
- Scope: exactly the four files in the contract's `scope_paths` were touched; no code, test, CI,
  or dependency file in the diff.
- No em/en dash on any added line, scanned programmatically across the full patch.
- Both hash checks passed: the frozen patch's sha256 and a fresh
  `git diff --staged --no-renames --no-abbrev | sha256sum` on the branch are identical, confirming
  the staged index did not move during review.
