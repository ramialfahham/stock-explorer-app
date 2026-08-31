# Review

diff_sha256: b0f4d402e0a4189c4dade042ee12037589e0512aea57c64ac6636df96b110363

Eight review rounds. Required reviewers per routing (`.claude/review_routing.json`):
scope-auditor (always), cto-reviewer (`frontend/*`, `tests/*`). No dbt or `docs/data_contract.md`
file in this diff, so analytics-engineer-reviewer and equity-analyst-reviewer are not required.

**Reviewer dispatch:** the plugin's reviewer agent types are not registered as dispatchable in
this session, so each ran as a general-purpose agent instructed to read its own role file
verbatim first. Cold, blinded, read-only input; the staged index was frozen to a patch file and
sha256 before every dispatch and never moved while reviewers were running.

**Final verdicts (round 8, the commit gate):** scope-auditor PASS, cto-reviewer PASS.

## What this is

Fixes the Discover list's severe click-registration slowness (owner: "Clicking on an element in
the list and nothing happens... Usability is zero") by paginating the list, per owner decision:
pagination, 30 rows per page (`DISCOVER_PAGE_SIZE` in `frontend/app.py`). The pool is sliced
after the existing filter/sort step, before it reaches `row_ui.render_rich_row_list` -- no
change to the row primitive's tap-target mechanics, pool computation, filtering, or sort order.
Live-verified: 40 buttons / 942 DOM nodes mounted (down from ~931 / ~20,600).

Also fixes an additionally-discovered CSS scoping bug in `frontend/styles.py`: the row-tap-target
rule from MR !67 scoped itself via a bare `:has(.ss-row)`, which matches at any descendant depth,
not just the nearest -- so it also matched the big stVerticalBlock wrapping the entire list, and
the new pagination buttons (the first other `st.button()` ever sharing that wrapper) silently
inherited `position: absolute; inset: 0` meant only for each row's own tap target, stretching to
~2780px tall. Fixed by tightening five selectors to a direct-child
`:has(> [data-testid="stElementContainer"] .ss-row)` form, matching a pattern already used
correctly elsewhere in the same file. Two new regression-guard tests added.

## Round-by-round findings and fixes

**Round 1**: scope-auditor ESCALATED (see below); cto-reviewer PASSED clean, independently
verifying re-run/interruption safety of the new `discover_page` session-state and the CSS
selector fix's correctness by tracing Streamlit's actual DOM structure.

**Round 2**: scope-auditor FAILED -- the owner's "Ship as-is" answer to round 1's escalation
existed only in chat, not recorded in any repo artifact a cold reviewer could check. Fixed:
recorded in `.claude/task/contract.md`, `docs/backlog/discover_list_performance.md`, and
`.claude/active_work.md`, all dated and quoted. cto-reviewer passed clean.

**Round 3**: scope-auditor FAILED -- `docs/north_star.md`'s "Browse" row still described the
pre-pagination behavior ("shows a scrollable list of every match"), not in scope_paths, not
updated. Fixed and added to scope_paths. cto-reviewer passed clean.

**Round 4**: scope-auditor FAILED -- a repo-wide sweep (prompted by round 3's miss) found two
more docs with the identical stale phrasing: `README.md` and
`docs/ux_principles_finanz_lern_apps.md`. Fixed. cto-reviewer passed clean.

**Round 5**: scope-auditor FAILED on three points: (a) the new handover entry's own heading said
"reviewed" while its body said review was still in progress; (b) the MR !67 handover entry
wasn't annotated with a forward cross-reference to the CSS-scoping gap found in that same rule,
breaking this file's own established annotation convention; (c) `contract.md` used an undefined
"CPO ANSWER" label in prose, when this repo's actual convention (confirmed via git history) is
that "CPO ANSWER:" is a fixed marker used only as a heading inside `review.md`'s escalation
sections, never in general prose, which always says "owner." All three fixed. cto-reviewer
passed clean (twice affected by a harness false-positive on a "settings.json" text pattern in
its own checklist prose, unrelated to any actual file in the diff).

**Round 6**: scope-auditor FAILED -- inserting the new pagination entry near the top of
`active_work.md` flipped three "above"/"below" cross-references elsewhere in the file that were
correct before the insertion. Fixed. cto-reviewer passed clean.

**Round 7**: scope-auditor FAILED on a fourth instance of the same defect class, found via an
explicit end-to-end sweep this round was asked to do: the "Discover list performance" section's
own header and "Next concrete action" paragraph still framed pagination as "not yet approved,"
with a backwards pointer, even though this branch is the one that got approval and shipped it.
Fixed, and rewriting that section surfaced two more unrelated stale "MR open, awaiting merge"
statuses (MR !53, MR !64) via a targeted grep, both verified against `git log --merges` and
corrected to "merged." cto-reviewer passed clean.

**Round 8**: both reviewers independently re-verified every MR-status claim against
`git log --oneline --merges main`, confirmed no further "awaiting merge" staleness remains
repo-wide, confirmed the CSS fix's mechanism by hand-tracing the DOM structure rather than
trusting the diff's prose, and explicitly judged (per the task's own prompt) whether further
`active_work.md` expansion was itself scope creep -- concluded it wasn't, since fixes stayed
narrowly targeted to the exact defect class each round found, and the file's own SIZE WARNING
already defers a full archival pass as separate, owner-scheduled work. Both PASS.

## scope-auditor -- round 1 (ESCALATE, resolved)
VERDICT: ESCALATE
questions:
- The contract's `decisions_reserved` section classified the specific pagination control shape
  (Previous/Next labels, "Page N of M" text, hide-vs-disable on a single-page pool) as "an
  implementation detail of the approved direction... not a new product decision," but
  `docs/backlog/discover_list_performance.md`'s own Open Questions section states the opposite:
  this class of call is "a real product/UX decision... not something to default silently."
  Should the specific control shape have its own separate owner sign-off, beyond the abstract
  pagination/page-size decision?
- `docs/working_agreement.md`'s UX PR gate requires a mobile wireframe for new layout patterns in
  Discover chrome; the diff added Previous/Next controls but the existing ASCII wireframe in
  `docs/ui/discover_list.md` wasn't updated to depict them. Does a text-only layout-rule entry
  satisfy the gate's intent, or does the literal wireframe need updating?

CPO ANSWER: Both resolved. (1) Owner was shown the built control shape directly and asked "Good
to ship as-is?"; answered "Ship as-is." No change made as a result of this question; the answer
is recorded in `.claude/task/contract.md`'s `decisions_reserved`, `docs/backlog/
discover_list_performance.md`'s Open Questions, and `.claude/active_work.md`'s "Discover list
paginated" entry, all dated 2026-08-31. (2) The wireframe was updated: `docs/ui/discover_list.md`'s
"List row wireframe (480px)" now depicts the Previous/Next footer and the hide-on-single-page
behavior, with a matching new "Footer (pagination)" prose paragraph.

## scope-auditor -- round 8 (final)
VERDICT: PASS
risks_checked:
- MR merge-status claims added across the diff are not fabricated: independently ran
  `git log --oneline --merges main` and confirmed every "MR ... merged" edit in
  `.claude/active_work.md` (MR !53, !64, !68, !69) matches a real merge commit.
- Self-check completeness on the defect class round 7 failed on: grepped the whole file for
  `awaiting merge` and `MR !\d+ open`/`OPEN` post-diff -- zero hits of the stale-merge-status
  kind; the few remaining "OPEN"/"still open" mentions are genuinely unresolved work items, not
  stale merge claims.
- Scope containment: every file in the diff matches `contract.md`'s `scope_paths`; the
  `frontend/styles.py`/`tests/frontend/test_styles.py` amendment has a concrete, verifiable
  cause, not silent creep.
- No owner-level decision taken silently: pagination approach, page size, and the control shape
  are each explicitly recorded as owner-approved, consistently across all three artifacts; the
  diff does not reopen `docs/backlog/discover_first_time_default.md`'s decision (the full pool
  stays reachable via Next, unfiltered by default).
- Ran the test suite directly rather than trusting the claim: `pytest tests/frontend` -- 175
  passed. Scanned every added line in the raw patch for em/en dash -- none found.
- Hand-traced the CSS fix's claimed mechanism: confirmed the pagination buttons' own
  stVerticalBlock has no `.ss-row` as a direct-child descendant, so the tightened selector
  correctly excludes them post-fix -- a real fix of the described mechanism, not a cosmetic
  rename.
- Explicitly judged whether further `active_work.md` expansion was itself scope creep, per this
  round's own prompt: concluded it wasn't -- fixes stayed narrowly targeted to the exact defect
  class each round found, and the file's own SIZE WARNING already defers a full archival pass as
  separate, owner-scheduled work.

## cto-reviewer -- round 8 (final)
VERDICT: PASS
risks_checked:
- New mechanism / dependency creep: pagination adds one module constant and three functions,
  all built from primitives already used elsewhere in `frontend/app.py`
  (`st.session_state`, `st.button`, `st.columns`, `st.rerun`). No new import, package, service,
  or lifecycle hook.
- Re-run / interruption safety: `_discover_page_slice` clamps `page` against the pool's current
  length on every call, not trusted from a prior run -- confirmed by 6 targeted tests and a
  fresh full-suite run: 428 passed, 0 failed.
- Scope integrity: `git diff --stat HEAD` lists exactly the files in `scope_paths`;
  `frontend/row_ui.py` shows zero diff, matching the contract's claim that tap-target mechanics
  were untouched.
- CSS selector fix correctness: counted 6 total instances of the corrected direct-child form (5
  newly tightened + 1 pre-existing correct hover rule), 0 remaining bare-form instances --
  matches the two new regression-guard tests exactly.
- Factual accuracy of this round's specific handover edits: grepped `git log --all --merges` for
  all four MR-status corrections made this round -- all four are real merge commits into `main`.
- Style/hard-rule compliance: scripted check of every added line for em/en dash -- zero matches.
