# Review

diff_sha256: 8cc7928143f41d9538a4aa30611f6e134aad403bd8ea0ec0593d5477e3262498

Three review rounds. Required reviewers per routing (`.claude/review_routing.json`):
scope-auditor (always), cto-reviewer (`frontend/*`, `tests/*`). No dbt or `docs/data_contract.md`
file in this diff, so analytics-engineer-reviewer and equity-analyst-reviewer are not required.

**Reviewer dispatch:** the plugin's reviewer agent types are not registered as dispatchable in
this session, so each ran as a general-purpose agent instructed to read its own role file
verbatim first. Cold, blinded, read-only input; the staged index was frozen to a patch file and
sha256 before every dispatch and never moved while reviewers were running.

**Final verdicts (round 3, the commit gate):** scope-auditor PASS, cto-reviewer PASS.

## What this is

Deletes the app's first-run landing screen entirely, per explicit owner decision after
reviewing a live mockup: no shrunk version, no replacement gate, no hints added anywhere.
First launch now goes straight into Discover. The brand and tagline the old screen carried are
already permanent in the header; the one thing on it that wasn't shown anywhere else, "Not
investment advice," becomes a permanent caption there instead of a one-time screen the owner
noted was "completely wasted." Full decision trail, including the owner's explicit rejection of
coach-marks/hints on standard controls as condescending, is in
`docs/backlog/landing_onboarding_rework.md`.

Deletes `frontend/landing.py` and six now-dead functions in `frontend/browser_storage.py`
(`onboarding_ready`, `is_onboarding_dismissed`, `dismiss_onboarding`, `request_landing`,
`_load_onboarding_from_manager`, plus the now-orphaned `_parse_bool`), the overflow menu's "How
Stock Explorer works" button, and the `.ss-landing*` CSS block. Splits `_render_brand_header()`
into a pure `brand_header_html()` (now unit-tested in new `tests/frontend/test_app.py`) plus a
thin wrapper, matching this codebase's existing `build_row_html()`/`render_row_list()`
convention; this required guarding `frontend/app.py`'s previously-unconditional module-level
`main()` call, verified live against both the dev launch config and the real deployed entrypoint
(`streamlit_app.py`).

## Round-by-round findings and fixes

**Round 1**: both required reviewers independently FAILED on the same root cause, an
orchestrator mistake, not a design defect. A single `git add` invocation listing twelve
pathspecs included `frontend/landing.py`, which had already been deleted via a standalone
`git rm` earlier in the session; git's `add` validates every pathspec before staging any of
them, so the one invalid path silently aborted the entire command and staged nothing new. The
frozen patch therefore contained only the 40-line `landing.py` deletion from the earlier `git rm`,
while all ~10 files with the actual substantive work sat unstaged or untracked. Committing
exactly what was staged would have shipped `frontend/app.py` still importing the just-deleted
`landing` module, crashing both the dev launch config and the real deployed entrypoint
(`streamlit_app.py`) at import time. cto-reviewer additionally found two em-dash violations in
`docs/ui/discover_header.md` (a newly-authored table row and a pre-existing row re-emitted as an
added line by renumbering). Fixed: re-staged correctly with `git add -u` plus an explicit add
for the one new file, and both em-dash instances corrected.

**Round 2**: the staging fix and the em-dash fix both verified clean by both reviewers.
cto-reviewer then found a second, unrelated, more substantive problem: the round-1 fix's own
follow-through in `docs/backlog/landing_onboarding_rework.md` had resolved the open question
"What 'getting to the cards where learning content is located' should become, concretely" as
answered (reasoning: the existing card content already proves itself on tap, so no scaffolding
was needed), directly contradicting this same task's own contract, whose `done_when` explicitly
named that exact question as one that must stay open and unresolved. This was a real overreach:
reading the owner's actual decision ("no hints on standard controls, delete the landing screen")
as also settling a second, un-asked question ("is the row-to-card path good enough"), the kind of
unilateral rule-extension the working agreement's §6 reserves to the owner. round-2
scope-auditor, reviewing the identical patch, did not catch this. Fixed: the question restored
to "still open" with reasoning for why it's genuinely separate from what was decided; the
contract and handover both updated to record the finding honestly rather than silently correct it.

**Round 3**: both reviewers re-verified the round-2 fix independently and skeptically,
specifically checking that the resolution wasn't smuggled back in under different wording
elsewhere in the doc (it wasn't), that no new instance of the same anti-pattern appeared in this
round's diff (none did), and that the earlier rounds' fixes hadn't regressed (they hadn't:
frontend/test files were byte-identical to the already-passing round-2 state). Both passed clean.

## scope-auditor
VERDICT: PASS
risks_checked:
- The exact round-2 regression (the backlog doc quietly resolving "getting to the cards")
  reappearing under different wording: checked every section of the doc (Decision, Summary,
  Candidate directions, Open questions): it stays open, with no restatement of the resolution
  anywhere else.
- The doc's two other now-resolved questions ("Replay path," "New mechanism") are mechanical,
  verifiable consequences of the actual owner decision, not the same class of overreach:
  checked each against the decision text directly.
- A full-repo doc-sync sweep beyond the contract's own named grep terms (`north_star.md`, all of
  `docs/ui/`, `data_contract.md`, `project_context.md`, other backlog docs, handover docs) found
  no stale reference to the deleted mechanism anywhere.
- The round-2 staging fix stayed intact: `git diff --staged --stat` for `frontend/`/`tests/`
  matches the patch's file-by-file line counts exactly; no gap reintroduced.
- `render.yaml`'s `startCommand` and `.claude/launch.json`'s dev config both structurally match
  the contract's dual-entrypoint claim about `streamlit_app.py` and the `__main__` guard.
- No em/en dash on any of the patch's 811 lines, scanned programmatically.
- Both hash checks passed: the frozen patch's sha256 and a fresh
  `git diff --staged --no-renames --no-abbrev | sha256sum` on the branch are identical.

## cto-reviewer
VERDICT: PASS
risks_checked:
- Its own round-2 finding, re-verified independently: the "getting to the cards" question is
  unstruck, under a heading literally titled "Still open, not touched by this decision," phrased
  as genuinely unanswered, not hedged language that quietly implies resolution.
- Re-read the full round-3 diff with fresh eyes for any new instance of a product/UX decision
  presented as settled without owner sign-off: found none; the other changed docs are mechanical
  recounts (button count, block numbering), not judgments.
- Diffed round-2's patch against round-3's byte-for-byte: only the three doc files claimed
  changed; every frontend and test file is identical to the already-reviewed, already-passing
  round-2 state, so no regression is possible.
- `pytest -q` run fresh in the repo's own `.venv`: 418 passed, matching the contract exactly.
- No em/en dash on any of the 306 added lines in round 2, or the full patch in round 3, scanned
  programmatically both times.
- Both hash checks passed each round.
