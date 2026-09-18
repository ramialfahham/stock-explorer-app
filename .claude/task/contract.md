# Task contract
> DISPOSABLE. **Owns:** THIS task's objective, `scope_paths`, reserved decisions and
> `done_when`.
> **Never:** anything that outlives the task. Overwritten by the next task.

objective: Owner, live-testing the app across three prior narrow fixes (search-card-focus
  MR !186, search-clear-button MR !188), found each fix addressed only the specific
  symptom reported and left the underlying design broken: search was built as a second,
  parallel state machine to Discover's filtered list (its own focus flag `search_selected`,
  its own rendering functions `_render_search_results`/`_render_search_focused_card`, its
  own read-only card carve-out), duplicating the list/pagination/focus/back mechanism the
  filtered list already had. Owner's explicit instruction: stop patching individual
  symptoms and implement one coherent navigation concept for the whole app.

  Concept implemented: search is not a separate mode, it narrows the same Discover pool a
  market/sector/preset filter would. `_discover_pool()` returns `_search_matches()` results
  when a query is set, else the normal `filter_pool()` results -- and `_render_discover_tab()`,
  already generic over whatever pool it receives, renders filtered and searched lists/cards
  identically with no added branching. One state key (`discover_focus_key`), one row-list
  path, one back-button implementation, shared by every way a Discover card can be opened.

  Removed as dead code once the second state machine no longer existed: `_card_key`,
  `_select_search_row`, `_render_search_results`, `_render_search_focused_card`, and the
  `search_selected` session-state key.

  Net behavior changes from unifying (both examined against the owner's request, not
  applied silently):
  - A card opened from search now gets full Save/Not-now actions, same as one opened from
    the filtered list. The prior read-only carve-out was itself a symptom of search being a
    lesser, separate code path -- keeping it would have meant threading a read-only flag
    through the now-shared render path, reintroducing the special-casing being removed.
  - The scope-stats line now shows during an active search too (previously hidden by a
    search-specific branch that no longer exists) -- but with its wording corrected to
    match: "N match "query"" during a search, "N match your filters" otherwise
    (`_render_discover_scope_stats` now takes the active query and branches on it, mirroring
    the empty-state message just below it, which already branched on `query` the same way).
    A round 1 review (both cto-reviewer and scope-auditor, independently) caught that the
    first pass reused the filter-only string unconditionally, so an active search claimed
    "matches your filters" while zero filters were in effect -- fixed before round 2.

  Deliberately NOT changed: search's underlying card-set semantics. It stays global (matches
  the full deck, ignoring the current market/sector/preset filters) and still excludes
  nothing -- this was an explicit, already-made product decision (AskUserQuestion, issue
  #20) and re-scoping it now would be a second, unrelated change riding on this one.

scope_paths:
  - frontend/app.py
  - tests/frontend/test_app.py
  - tests/frontend/test_app_e2e.py
  - .claude/task/contract.md
  - .claude/task/review.md

decisions_reserved: none -- the owner explicitly delegated the concept and asked for direct
  implementation ("I told you to come up with a concept... implement... stop
  micromanaging me").

done_when:
  - Discover's list, its pagination, its focused-card view, and its back button behave
    identically whether the pool came from filters or from a search query -- no
    search-specific rendering path remains in frontend/app.py.
  - Opening a card from a search result grants the same Save/Not-now actions a
    filtered-list card gets.
  - `pytest tests/frontend -q` and `pytest tests/ -q` (excluding the pre-existing,
    unrelated `tests/tooling/test_generate_assessments.py` collection error from a missing
    local `anthropic` package) pass.
  - `check_no_em_dash.py` and `check_context_budget.py` pass.
  - Live-verified in the browser: searching "apple" narrows the list to the one match with
    the stats line and no Filters popover; clicking it opens the card directly (the exact
    bug the owner screenshotted: "clicking on the field, apple content opens, but i'm not
    on a card") with Save/Not-now visible; Back returns to the same one-match search
    results; switching to Saved and back to Discover clears the search and restores the
    full filtered list.

impact_map: frontend/app.py (Discover's pool/list/focus/back logic, net smaller after
  removing the duplicated search rendering path), matching test coverage. No data/schema/CI
  change.
