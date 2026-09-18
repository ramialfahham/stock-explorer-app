# Task contract
> DISPOSABLE. **Owns:** THIS task's objective, `scope_paths`, reserved decisions and
> `done_when`.
> **Never:** anything that outlives the task. Overwritten by the next task.

objective: Fix a real UX gap the owner found live: opening a card from Discover's search
  results never enters a focused state the way every other card-open path in the app does
  (Discover's own list, Saved's list). The search box and the result row stay rendered
  above the opened card indefinitely -- no back button, no way to tell "I'm on a card now."
  This makes the search-opened card the one inconsistent entry point in an otherwise
  consistent focus pattern (`discover_focus_key` / `saved_focus_key`, each hides its list
  and shows a back row + the card). Fix: add the same treatment for search
  (`search_selected` already exists as the state key, it just was never wired into the
  hide-list-show-back-row pattern the other two use).

scope_paths:
  - frontend/app.py
  - tests/frontend/test_app.py
  - tests/frontend/test_app_e2e.py
  - docs/media/discover-card.png
  - .claude/task/contract.md
  - .claude/task/review.md

decisions_reserved: none -- this applies an already-established, already-approved pattern
  (focused card hides its list, shows a back row) to a second entry point that was missing
  it, not a new UX decision. Back returns to the search RESULTS (same query), mirroring how
  Discover's and Saved's own back buttons return to their own list, not further up.

done_when:
  - Opening a card from search hides the search box and the result row list, shows a
    `← Back to list` row, then the read-only card -- matching Discover's/Saved's own
    focused-card chrome.
  - Back returns to the search results for the same query (not to the empty search box,
    not to the full Discover pool).
  - `_card_open("Discover")` returns True when a search-opened card is focused too, so the
    header compacts consistently with every other focused-card state.
  - The search query widget's session_state survives being hidden while a card is
    focused (the file's own established reseed-when-key-absent pattern, already used for
    market/sector filters surviving the same kind of hide) -- verified live, not just by
    AppTest, per this file's own standing rule for widget-identity bugs.
  - `_render_search_results`'s now-dead "render the selected card inline" branch is
    removed (search_selected can no longer be true when this function runs).
  - `pytest tests/frontend -q` passes, including new coverage for the focused-search-card
    state and the back-to-results transition.
  - Live-verified in the browser: search, open a card, confirm it looks like every other
    focused card (no search box, no result row, back button present, back returns to the
    same search results).
  - `docs/media/discover-card.png` refreshed to the current card design (owner-supplied
    screenshot, cropped to match the existing framing) -- unrelated to the UX fix itself,
    bundled since both surfaced in the same conversation.

impact_map: one new focused-view function in frontend/app.py, two call-site changes
  (`_card_open`, `_discovery_page`), removal of dead code in `_render_search_results`,
  plus test coverage. No data/schema/CI change. Pure UX consistency fix.
