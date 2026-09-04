# Task contract

objective: Fix 3 of the 4 confirmed bugs from `docs/backlog/discover_saved_search_ux_findings.md`
  -- the ones with a clear, technical, no-owner-decision-needed fix. Agent-executable per the
  owner's own split of today's open-issues list ("doesn't need you at all... I can just do
  these and show you the result"). The 4th bug ("Clear saved" has no confirmation/undo) and the
  unconfirmed Saved-pagination risk are NOT in this task -- both need an owner product call
  first, per that doc's own "Open questions."

  **Root cause, found live (not guessed):** instrumented `_init_state()` and
  `_render_explore_filters()` with temporary debug prints, drove the actual dev server through
  the exact repro sequence (set a Discover filter, switch to Saved, switch back), and confirmed
  `explore_market` goes fully absent from `st.session_state` at the top of the very next run
  after the widget wasn't rendered for one run -- not just invalid, gone. This holds even though
  the selectbox already had an explicit `key="explore_market"`: Streamlit evicts a KEYED
  widget's session_state entry too, whenever that widget isn't instantiated on the immediately
  preceding run. The original backlog doc's own guess (missing `key=` explains the Search box;
  the filter's cause was separately unconfirmed) was half right and half wrong -- the Search box
  bug IS the same eviction mechanism, but adding a bare `key=` to it (the doc's own candidate
  fix) would NOT have worked, since a keyed widget is evicted too. Debug instrumentation was
  removed before this diff; none of it ships.

  **The fix**, applied identically to both the Discover filter selectboxes and the Search
  text_input: stop giving the widget a `key=` at all. Read/write the durable value as a plain
  session_state entry instead (immune to Streamlit's widget-key lifecycle since nothing here is
  tied to a widget's own key), and seed each render's `index=`/`value=` from it. The widget's
  own return value (not a session_state lookup) is compared against the stored value to detect
  a change.

  **Separately**, `search_selected` (which card's snapshot the Search tab pins open) is now
  cleared whenever the query text itself changes -- an unrelated, purely app-logic bug (a stale
  variable never reset, nothing to do with Streamlit's widget lifecycle) that the same backlog
  doc flagged as bug #1: searching a query that happens to re-match a previously-opened card's
  name/ticker as a substring was silently resurrecting that old card with no click.

  All three fixes verified working by hand against the actual repro sequences in a running dev
  server (not just read as fixed): Discover filter set to ASX 200 survives a Saved-then-back
  round trip; a typed Search query survives a Discover-then-back round trip; searching "App"
  after Apple->Microsoft no longer resurrects Apple's snapshot.

  **No new unit tests for the 2 widget-persistence fixes.** Both are fundamentally about
  Streamlit's own widget-render lifecycle across script reruns, which this repo's existing
  convention explicitly does NOT unit-test (`tests/frontend/test_app.py`'s own docstring: test
  pure logic, not the Streamlit-calling render function) -- a plain pytest unit test can't
  exercise "was this widget instantiated on the immediately preceding run" without either
  Streamlit's heavier `AppTest` harness or refactoring the render functions themselves, both
  bigger asks than this fix. Verified instead by direct, repeatable interaction against a
  running dev server, matching `docs/backlog/discover_list_performance.md`'s own "confirmed by
  direct measurement" precedent for claims about Streamlit's runtime behavior specifically.

  **The `search_selected`-clearing fix IS unit-tested**, since it's plain session_state
  bookkeeping with no Streamlit widget involved -- extracted into its own function
  (`_sync_search_query`) and tested directly in `tests/frontend/test_app.py`, the same
  `st.session_state`-standalone approach `test_browser_storage.py` already established this
  session. **Amended mid-review**: the first version of this contract wrongly folded this fix
  into the same "Streamlit lifecycle, can't unit-test" exemption as the other two, while its own
  objective section (above) correctly called it "nothing to do with Streamlit's widget
  lifecycle" -- a direct self-contradiction cto-reviewer's round-1 pass caught. Fixed by
  extracting and testing it, not by re-arguing the exemption.

scope_paths:
  - frontend/app.py
  - tests/frontend/test_app.py (new tests for the extracted `_sync_search_query`, added
    mid-review per cto-reviewer's round-1 finding)
  - .claude/active_work.md
  - .claude/task/contract.md
  - .claude/task/review.md

decisions_reserved: none for the 3 bugs fixed here -- pure technical fix, no product/wording
  decision, no new mechanism (an unkeyed-widget-plus-manual-session-state pattern is a standard,
  well-known Streamlit idiom for exactly this class of bug, not something invented for this
  task). Separately, recording one small owner decision already made today outside this task's
  own subject: repo hosting stays GitLab-only while the GitHub account remains suspended (the
  `origin` remote), revisit only if that account is recovered -- added to
  `.claude/active_work.md`'s Standing decisions since it came up today and the owner asked not
  to be asked again.

done_when:
  - `frontend/app.py`: Discover's Market/Sector selectboxes and Search's text_input all
    unkeyed, reading/writing their durable value as a plain session_state entry, seeded via
    `index=`/`value=` each render. `search_selected`-clearing logic extracted into
    `_sync_search_query(query)`, called from `_render_search_tab`.
  - All three fixes verified by direct interaction against a running dev server, not just
    inferred from the code: filter persists Discover->Saved->Discover; Search text persists
    Discover->Search->Discover; a re-matching later query does not resurrect a stale selection.
  - `_sync_search_query` unit-tested in `tests/frontend/test_app.py`: unchanged query leaves a
    pinned selection alone; a changed query (including clearing the box entirely) clears it.
    Verified the tests actually catch the regression, not just pass: temporarily stripped the
    clearing logic (kept only the query-persist line), confirmed 2 of the 4 new tests fail,
    restored from a backup, confirmed the full suite green again.
  - Full `pytest` suite green (486 passed -- 482 plus the 4 new tests; this branch is cut from
    `main`, which does not yet include the separate, not-yet-merged
    `test/browser-storage-coverage` branch's 23 tests).
  - `docs/backlog/discover_saved_search_ux_findings.md` is NOT edited in this task (a
    docs-accuracy update reflecting these 3 fixes belongs to whoever next touches that doc for
    the remaining 2 items, to avoid re-opening a separately-reviewed file for an unrelated
    task) -- noted here so a reviewer doesn't expect it.
  - `.claude/active_work.md`: this item closed out (moved from open-items framing to a short
    "fixed" note or removed, per the established collapse-on-merge convention), plus the
    GitLab-hosting decision recorded in Standing decisions.
  - No em dash or en dash on any added line.

impact_map:
  - Purely additive-feeling UX fix: Discover's filter and Search's query box now behave the way
    a reader would already assume they do (survive glancing at another tab). No visible change
    to anyone who never left Discover/Search mid-session.
  - No new dependency, no schema change, no CI change. `frontend/app.py` only.
  - No verdict-computation or metric-definition change anywhere.
  - Leaves 2 items from the same backlog doc open (Clear-saved confirmation, Saved pagination)
    -- both still need an owner product call before any fix is scoped.

amendments: cto-reviewer's round-1 pass found the original contract's "no new tests" reasoning
  self-contradicted itself (see the objective section above) and that the `search_selected` fix
  is genuinely pure, testable logic this repo's own established convention already has a
  pattern for. Fixed by extracting `_sync_search_query` and testing it directly, not by
  re-arguing the exemption. The two widget-persistence fixes remain untested for the reasons
  given, which cto-reviewer's round-1 pass did not dispute.
