# Task contract
> DISPOSABLE. **Owns:** THIS task's objective, `scope_paths`, reserved decisions and
> `done_when`.
> **Never:** anything that outlives the task. Overwritten by the next task.

objective: Owner found live: on a Discover card, clicking "Discover" (already the active
  nav tab) does nothing. Root cause: `st.segmented_control` only ever reports a NEW
  selection -- clicking the option already selected returns exactly the value it already
  had, indistinguishable from no click at all. Traced against Streamlit's own source
  earlier this session; not fixable by reading the return value differently. The owner
  explicitly rejected patching around this (hiding/disabling the broken pill) as the wrong
  fix, since that still leaves navigation dependent on a widget signal that structurally
  cannot exist for this case.

  Same root cause, three places (only the first was reported; the other two share the
  identical defect and get the identical fix in this task):
  - Card focused on Discover, click "Discover": no-op.
  - Card focused on Saved, click "Saved": no-op.
  - Not-now overlay open (from the overflow menu), click the active tab: no-op.
  Clicking the OTHER tab always worked, because that is a genuine value change, which
  `segmented_control` can detect -- the defect is specifically the reselect-the-active-tab
  case, which the widget cannot report by design.

  Fix: replace the two nav pills with two plain `st.button()`s (Discover / Saved, primary
  style when active). A plain button fires on every click, active-already or not, so the
  no-signal case cannot occur. One handler for both buttons, one rule for every nav click:
  land on the clicked tab's plain list -- close the Not-now overlay if open, clear that
  tab's focused card (and Discover's search, if leaving/re-entering Discover), set the
  active tab. This is ordinary tab-bar behavior (tapping the tab you're on returns to its
  root) and it removes the app's only remaining dependency on segmented_control's broken
  reselect signal, not just for the reported case.

  Deleted as dead state once segmented_control was no longer in use: the `bottom_nav`
  session-state key (it only ever existed to manage that widget's own identity/reseed).
  `active_page` is now the single source of truth for the active tab.

  Round 1 review (cto-reviewer) FAILed on exactly the class of gap working-agreement.md §2
  warns about: two authoritative UI docs (`docs/ui/design_system.md`,
  `docs/ui/discover_header.md`) still described the nav as `st.segmented_control` after
  this diff replaced it with plain buttons. Fixed before round 2, and a third stale claim
  in the same discover_header.md table row 7 (left over from the earlier search-unification
  task, found while already editing that row) fixed alongside it.

scope_paths:
  - frontend/app.py
  - frontend/styles.py
  - tests/frontend/test_app_e2e.py
  - docs/ui/design_system.md
  - docs/ui/discover_header.md
  - .claude/task/contract.md
  - .claude/task/review.md

decisions_reserved: none -- the owner asked for a short, concrete plan (table format) for
  this exact behavior change, reviewed it, and said to implement.

done_when:
  - Card focused on Discover, click "Discover": returns to Discover's list (not a no-op).
  - Card focused on Saved, click "Saved": returns to Saved's list (not a no-op).
  - Not-now overlay open, click the active tab: overlay closes, list shows (not a no-op).
  - Genuine tab switches (Discover <-> Saved) still work, including from a focused card or
    the Not-now overlay on the tab being left.
  - `pytest tests/frontend -q` and `pytest tests/ -q` (excluding the pre-existing, unrelated
    `tests/tooling/test_generate_assessments.py` collection error from a missing local
    `anthropic` import) pass, including new coverage for all three reselect cases above.
  - `check_no_em_dash.py` and `check_context_budget.py` pass.
  - Live-verified in the browser: all three reselect cases above, plus a normal Discover
    <-> Saved switch, still behave correctly.

impact_map: frontend/app.py (nav rendering + one new shared handler), frontend/styles.py
  (nav-row CSS updated for two plain buttons instead of segmented_control's DOM), matching
  test coverage. No data/schema/CI change.
