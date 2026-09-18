# Task contract
> DISPOSABLE. **Owns:** THIS task's objective, `scope_paths`, reserved decisions and
> `done_when`.
> **Never:** anything that outlives the task. Overwritten by the next task.

objective: Owner found live: once a search has text, there is no way back to Discover's
  normal list except manually deleting every typed character. Clicking the "Discover" nav
  pill while already on Discover is a no-op -- `_render_bottom_nav`'s tab-switch detection
  (`if selected != prior_active`) only fires on a GENUINE switch (Discover<->Saved), never
  when the already-active tab is clicked again, so nothing ever resets the search. This is
  the same class of "stuck sub-state with no way out" bug as the search-card-focus issue
  fixed earlier this session, one layer up: search itself, not just a card opened from it.

  Owner's ask: a clear, coherent navigation concept, not another isolated patch. Concept
  (stated to the owner, implementing directly per their "come up with one and fix it"):
  (1) search always has an explicit, visible clear affordance -- a button, not "delete the
  letters yourself"; (2) a genuine tab switch away and back always resets that tab to its
  clean default view, search included, the same way it already resets the Not-now panel;
  (3) a focused card's back row keeps returning to where it came from (already correct,
  unchanged).

scope_paths:
  - frontend/app.py
  - frontend/styles.py
  - tests/frontend/test_app.py
  - tests/frontend/test_app_e2e.py
  - .claude/task/contract.md
  - .claude/task/review.md

decisions_reserved: none -- the owner explicitly asked for the concept and the fix in the
  same message ("come up with a clear concept... then implement").

done_when:
  - A visible "Clear" control appears whenever the search box has text (list view or the
    focused-card view reached from search); clicking it empties the query and returns to
    Discover's normal filtered list.
  - Switching to Saved and back to Discover (a genuine tab switch) clears any active
    search, landing on Discover's normal list -- not stuck showing old search results.
  - The search-card focus behavior fixed earlier this session (back returns to the same
    search results) is unchanged.
  - `pytest tests/frontend -q` passes, including new coverage for both the clear-button
    and the tab-switch-resets-search cases.
  - Live-verified in the browser: type a query, confirm the clear control appears and
    works; type a query, switch to Saved, switch back to Discover, confirm the list (not
    stale search results) is showing.

impact_map: frontend/app.py (search box + nav tab-switch logic), a small CSS addition if
  the clear control needs one, plus test coverage. No data/schema/CI change.
