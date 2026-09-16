# Task contract
> DISPOSABLE. **Owns:** THIS task's objective, `scope_paths`, reserved decisions and
> `done_when`.
> **Never:** anything that outlives the task. Overwritten by the next task.

objective: Closes #20. Search is currently a third tab (Discover/Saved/Search); selecting
  it lands on a blank screen with nothing shown until you type. Add a persistent search
  box, always visible above Discover's list (in the same slot Filters occupies today), so
  search never requires leaving the list you're already looking at. Two decisions made via
  AskUserQuestion this session:
  1. While the persistent box has a non-empty query, it REPLACES Discover's Filters popover
     and filtered pool entirely (not shown alongside) -- filters are meaningless once
     you're searching globally.
  2. A company selected from the persistent box renders READ-ONLY (`render_stock_card`,
     no Save/Not now), matching today's standalone Search tab exactly. The separate
     "Search results have no Save button" gap (found during this session's UX review,
     not yet filed as its own issue) is explicitly OUT of scope here.
  The standalone Search tab is KEPT as a fallback entry point (issue #20's own stated
  allowed alternative to removing it outright) -- lower blast radius than ripping `Search`
  out of `NAV_PAGES` and everything keyed on it (tests, overflow menu, nav normalization).
  It shares the same `search_query`/`search_selected` session state and the same matching
  logic as the new box, extracted into `_search_matches()`/`_render_search_results()` so
  the two entry points can't silently diverge.

  **Scope grew mid-task, root cause not a new feature:** verifying against a running dev
  server (not just AppTest) found that the existing unkeyed-`value=`-reseeded text_input
  pattern this file uses elsewhere (and that the new box copied) silently discards every
  edit after the first -- its identity is a function of `value=`, and `value=` is reseeded
  from the widget's own prior output every edit, so the identity moves out from under
  itself after one keystroke. Confirmed live: typing a second query, or clearing the box,
  did nothing, in BOTH the new persistent box and the pre-existing standalone Search tab.
  Fixed at the root with a shared `_search_query_widget()` (stable `key=`, re-seeded only
  when the key is absent -- the actual tab-switch-eviction case the old pattern existed to
  survive). Shipping a search box that provably cannot be edited or cleared fails this
  task's own objective, so the fix is in scope, not a separate follow-up.

scope_paths:
  - frontend/app.py
  - tests/frontend/test_app_e2e.py
  - docs/ui/discover_header.md
  - .claude/task/contract.md
  - .claude/task/review.md

decisions_reserved: none further -- both open UX questions the issue and the earlier
  conversation flagged (filters-vs-search coexistence, Save-button parity) were answered
  via AskUserQuestion this session before this contract was written.

done_when:
  - Discover's list view (not a focused card) shows a persistent search input above
    Filters, always visible, doing the same global (not market/sector-scoped) lookup as
    the standalone Search tab.
  - A non-empty query on Discover hides Filters, the scope stats line, and the filtered
    pool/pagination; shows matches and, if one is selected, its card read-only.
  - Clearing the query restores Discover's normal filtered list unchanged.
  - The standalone Search tab still works exactly as before (unchanged behavior),
    confirming it as a working fallback rather than dead code.
  - No duplicated matching/rendering logic between the two entry points.
  - `docs/ui/discover_header.md` describes the new box in the vertical-order table.
  - `pytest tests/frontend/ -q` green, with new coverage for: box appears on Discover's
    list view; hidden once a card is focused; a query hides filters/pool; clearing it
    restores them; a SECOND edit on either entry point actually takes effect (the
    regression this task's root-cause fix guards).
  - Verified live against a running dev server (`streamlit run streamlit_app.py`), not
    just AppTest: type, edit again, and clear, on both entry points.

impact_map: frontend-only (`frontend/app.py`: one shared `_search_query_widget()` replacing
  two divergent unkeyed text_input call sites, one new shared matching/rendering helper,
  one new Discover-scoped render function, `_discovery_page`'s orchestration order changed
  to render the box before Filters and short-circuit when a query is active). No schema,
  dbt, ingestion, or CI change. `NAV_PAGES`/nav_pages.py untouched -- Search tab kept.
