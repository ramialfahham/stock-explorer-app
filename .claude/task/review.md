# Review

diff_sha256: 4c43b7eb7d8896a8ab0c451266d6ef9a9ea5b7e5cc04e477aa46e3605bb0b1a9

One review round. Required reviewer per routing (`.claude/review_routing.json`): scope-auditor
(always). No other pattern in the routing matches this file set (a new `docs/backlog/*.md` file
plus `.claude/active_work.md` and `.claude/task/contract.md`), so no other reviewer is required.

**Reviewer dispatch:** the plugin's reviewer agent types are not registered as dispatchable in
this session, so scope-auditor ran as a general-purpose agent instructed to read its own role
file verbatim first. Cold, blinded, read-only input; the staged index was frozen to a patch file
and sha256 before dispatch and never moved while the reviewer was running.

**Final verdict (round 1, the commit gate):** scope-auditor PASS.

## What this is

Scopes the landing-page/onboarding rework as its own backlog item, per the owner's request. The
owner's original complaint bundled two problems: the one-card-mechanism/filters-with-no-visible-
effect problem (already fixed, `feat/discover-filter-list-focus`, MR !58) and the landing page/
onboarding experience itself (not fixed, not decided). Adds
`docs/backlog/landing_onboarding_rework.md`, matching the shape of the earlier
`name_vs_yfinance_audit_guard.md` scoping doc: current state read directly from the code, the
owner's complaint quoted verbatim, open product questions listed, candidate directions sketched
without ranking or recommending one. Corrects `.claude/active_work.md`'s existing forward
reference (left by the Discover task) to point at the new doc instead of describing it as
unlinked prose. Documentation only: no code, no CI, no new dependency.

## Round-by-round findings and fixes

**Round 1**: passed clean. scope-auditor independently re-derived every factual claim in the new
doc from the actual source (`frontend/landing.py`'s gating logic, the post-dismissal render
order via `frontend/app.py`, the locked "All markets · All sectors" default in `north_star.md`,
the "Active user paradox" quote against `docs/ux_principles_finanz_lern_apps.md`, the overflow
menu's replay button) rather than accepting the doc's claims on plausibility, and confirmed no
open question was answered on the owner's behalf: every candidate direction is presented
neutrally, with tradeoffs on both sides, not ranked or recommended.

## scope-auditor
VERDICT: PASS
risks_checked:
- Every factual claim about current code (`render_landing()`'s gating logic, the four
  already-corrected bullets, post-dismissal render order down to the alphabetical sort key, the
  locked north_star default scope, the "Active user paradox" quote, the replay button's code
  path) checked against the actual source, not assumed.
- No owner-reserved product/UX decision was silently made: scanned all added lines for
  recommendation language and found none directing toward a specific direction; the three
  candidate directions are labeled as candidates, and the one that would touch a locked
  north_star rule is explicitly flagged as needing its own separate sign-off rather than adopted.
- `.claude/active_work.md`'s edit is a correction of the exact pre-existing forward reference
  left by the already-merged Discover task, not new unrelated content; the relative link
  resolves to the file this patch adds.
- Scope: exactly the three files in the contract's `scope_paths` were touched; no frontend, dbt,
  or CI file in the diff.
- No em/en dash on any added line, scanned programmatically across the full patch.
- Both hash checks passed: the frozen patch's sha256 and a fresh
  `git diff --staged --no-renames --no-abbrev | sha256sum` on the branch are identical; a
  byte-level diff between the frozen file and a freshly regenerated one also came back
  identical, confirming the staged index did not move during review.
