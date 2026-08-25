# Task contract

objective: Fix the dead sibling-combinator CSS selector bug (same root cause MR #29 fixed
three times near the card footer) for `.ss-action-shell` (the fixed Save/Skip action bar)
and `.ss-nav-row-marker` (the Discover/Saved/Search nav row), plus a second, distinct
wrong-testid bug found in the nav row's segmented-control sub-rules.

scope_paths:
  - frontend/styles.py
  - tests/frontend/test_styles.py
  - .claude/active_work.md
  - .claude/task/contract.md

decisions_reserved:
  - (none) — flagged as a follow-up in MR #29's own Status entry after cto-reviewer spotted
    it there but declined to confirm it live or fold it into that PR; owner approved
    checking it ("go ahead with the CSS check"), then approved fixing what was found ("go
    ahead") after I reported the live-verified scope and severity.

technical_definition: |
  `.ss-action-shell + div[data-testid="stHorizontalBlock"]` — confirmed live: matched zero
  elements (`.ss-action-shell`'s own next sibling is null; the real relationship is one
  level up, `stElementContainer -> stLayoutWrapper`, identical to `.ss-card-footer-shell`).
  Real, user-visible impact, not just cosmetic: the Save/Skip button row was never actually
  `position: fixed` — it rendered as a normal block at the end of the card's scrollable
  content, so reaching Save required scrolling through the entire card (metrics, learn
  panel). This directly contradicted `docs/working_agreement.md`'s own UX-gate checklist
  item, "Save still reachable on Discover." Fixed with the same corrected pattern as the
  footer rules: `[data-testid="stElementContainer"]:has(.ss-action-shell) + [data-testid="stLayoutWrapper"]`.
  Live-verified after the fix: `position: fixed`, and Save's bounding-box top (710px) now
  sits inside a 812px mobile viewport with no scroll needed.

  `.ss-nav-row-marker + div[data-testid="stHorizontalBlock"]` (11 occurrences across the main
  rule, first/last-child rules, segmented-control rules, and a `@media (max-width: 640px)`
  block) — same dead-selector root cause, confirmed live the same way. Less visibly broken
  than the action bar only by coincidence: `st.container(horizontal=True)` (what the nav row
  actually uses, not `st.columns()`) already renders `display:flex; flex-direction:row`
  natively from Streamlit's own default styling, so the top-level layout intent happened to
  hold anyway. The sub-details did not: live-verified 16px `gap` instead of the intended
  `var(--ss-space-1)` (5.6px), and the segmented control not filling its column. Fixed with
  the same `:has()` pattern, but targeting the DESCENDANT `[data-testid="stHorizontalBlock"]`
  inside `stLayoutWrapper` rather than `stLayoutWrapper` itself (confirmed live:
  `stLayoutWrapper`'s direct child is the actual `display:flex` element carrying
  `align-items`/`flex-direction`/`gap` — those are flex-CONTAINER properties, inert unless
  applied to the actual flex element, unlike the footer/action-bar fixes' margin/padding/
  border/position, which work fine on the wrapper itself).

  Second, unrelated bug in the two segmented-control sub-rules: they targeted
  `[data-testid="stSegmentedControl"]`, which does not exist in the installed Streamlit
  version at all (confirmed live — `document.querySelector` returned null; walking the real
  DOM from an actual segmented-control button found `stButtonGroup` instead). Same class of
  mistake as the pre-existing `stLinkButton`/`stBaseLinkButton-secondary` correction already
  in this file. Fixed by replacing the testid; both sub-rules also needed the sibling-prefix
  fix above (both bugs stacked on the same two rules).

  All fixes live-verified via computed styles (not just static analysis) after a full dev
  server restart (module caching had produced false negatives earlier in the parent branch's
  session — restarting the process, not just navigating, avoided a repeat).

  cto-reviewer round 1 independently re-verified the selector correctness claims at the
  Streamlit SOURCE level (extracted and read the actual component code from the installed
  `streamlit==1.57.0` package's minified JS bundle) rather than trusting the live-browser
  claims alone — confirmed `stLayoutWrapper` is a single-child, fixed-`flex-direction:column`
  wrapper with no `gap`/`align-items` props, which is WHY `.ss-nav-row-marker`'s fix correctly
  needs the descendant `stHorizontalBlock` while `.ss-action-shell`'s doesn't (different
  properties: flex-container vs box-model). Also independently found `stButtonGroup` verbatim
  in the shipped `st.segmented_control` component chunk. FAILed anyway, on a real,
  separate finding not about correctness: this is the file's 5th-6th recurrence of the exact
  same dead-selector bug class (3 in MR #29, 2 here) with STILL zero automated test coverage
  for `frontend/styles.py` — a gap this repo's own `active_work.md` already documented during
  Slice 6b and left open across two more merged PRs since. Per working-agreement.md §4
  ("Tests are non-negotiable... output you can't eyeball must be covered by automated
  tests"), added `tests/frontend/test_styles.py`: a static regex check asserting the specific
  broken selector SHAPE (`.marker + div[data-testid=...]`, no `:has()` wrapper) never
  reappears, with a vacuity-guard companion test asserting the corrected shape is still
  actually present (so the negative assertion can't pass by accident if the whole pattern
  disappeared for an unrelated reason). Verified the test genuinely fails against the broken
  form (temporarily reverted one already-fixed rule, confirmed the expected failure message,
  restored it) before keeping it — matching the same discipline `tests/tooling/
  test_ci_reachability.py` documents for itself. This was NOT escalated to the owner as a
  scope question the way the footer-separator/action-bar widenings were: adding required
  test coverage for a file this task is already changing, to meet an already-written,
  non-negotiable project rule, is compliance with an existing decision, not a new one.

explicitly_not_in_scope:
  - Any other pre-existing selector in this file not named above — this task's scope is
    exactly the two markers cto-reviewer flagged in MR #29, verified live, not a fresh
    open-ended sweep of the whole file for more instances of this pattern.
  - Any visual/design value change — every fix keeps the exact declared values (position,
    width, gap, font-size, etc.); the fix makes already-declared values actually apply.

done_when:
  - `.ss-action-shell`'s scoped rule confirmed live to match, with `position: fixed` /
    `bottom: 0` actually computed (not `static`).
  - Save button confirmed reachable within a 375x812 mobile viewport without scrolling.
  - `.ss-nav-row-marker`'s scoped rules confirmed live to match, with `gap` and segmented-
    control width computed at their declared values (not Streamlit's un-overridden defaults).
  - `stButtonGroup` (not `stSegmentedControl`) confirmed live as the real matching testid.
  - No visual overlap/regression between the segmented control and the overflow-menu icon
    button (both confirmed via live bounding-box check).
  - Full test suite passes (`python -m pytest tests/ -q`).
  - `tests/frontend/test_styles.py` exists, passes, and was verified to actually fail
    against the broken selector shape before being kept.
  - `.claude/active_work.md` updated to reflect this is done.

amendments:
  - 2026-08-25 — initial contract, written after the check (Explore, owner-approved: "go
    ahead with the CSS check") revealed a materially bigger and more severe finding than
    the original framing suggested (a real UX-gate violation, not just subtle typography),
    which was reported back to the owner before implementing; owner then approved the fix
    itself ("go ahead") with full knowledge of the actual scope and severity.
  - 2026-08-25 — cto-reviewer round 1 FAILed on a real, well-evidenced gap (zero test
    coverage for `frontend/styles.py` across 5-6 recurrences of this exact bug class);
    `tests/frontend/test_styles.py` added and `scope_paths` updated to include it. Not
    escalated — see technical_definition's final paragraph for why this is compliance with
    an existing rule, not a new scope decision.
