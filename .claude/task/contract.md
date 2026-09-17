# Task contract
> DISPOSABLE. **Owns:** THIS task's objective, `scope_paths`, reserved decisions and
> `done_when`.
> **Never:** anything that outlives the task. Overwritten by the next task.

objective: Remove the standalone "Search" bottom-nav tab. Since issue #20 (persistent
  search box on Discover), the tab is fully redundant: same widget, same global match
  logic, same result rendering as Discover's own search box -- confirmed live by the
  owner ("I still don't get what the point of the search button is"), and confirmed by
  reading the code (`_render_search_tab` calls the exact same shared helpers Discover's
  box does). Owner's explicit go: "do it." Nav shrinks to Discover / Saved.

scope_paths:
  - frontend/nav_pages.py
  - frontend/app.py
  - frontend/overflow_menu.py
  - frontend/supabase_cards.py
  - frontend/styles.py
  - tests/frontend/test_nav_pages.py
  - tests/frontend/test_app.py
  - tests/frontend/test_app_e2e.py
  - tests/frontend/test_overflow_menu.py
  - docs/north_star.md
  - docs/ui/discover_header.md
  - docs/ui/discover_list.md
  - docs/ui/design_system.md
  - docs/streamlit_deploy.md
  - .claude/task/contract.md
  - .claude/task/review.md

decisions_reserved: none -- the owner already made this call live in chat.

done_when:
  - `NAV_PAGES` is `("Discover", "Saved")`; `_render_search_tab` and its nav branch are
    gone.
  - The Discover persistent search box, matching, and result rendering are unchanged in
    behavior (still global across the deck, still read-only results) -- only the second
    entry point is removed, not the underlying feature.
  - `overflow_menu.py`'s tab-specific copy (`right_now_line`, `quick_tip_line`) no longer
    branches on a "Search" tab that can't occur.
  - `pytest tests/frontend -q` passes with the standalone-tab tests removed and the
    persistent-search tests (which already cover the same regressions) intact.
  - UI docs (`discover_header.md`, `discover_list.md`, `design_system.md`, `north_star.md`)
    no longer describe a three-way Discover/Saved/Search nav.
  - `docs/working_agreement.md`'s UX PR gate satisfied: MR body states the one primary
    job change, includes a mobile wireframe (nav chrome changed), and a live 480px smoke
    check is run before merge (this is Discover chrome).
  - `python scripts/check_no_em_dash.py` and `check_context_budget.py` pass.

impact_map: frontend nav (one less tab) + its own tests + the UI docs that described the
  old three-way nav. No data/schema/CI change. `_search_query_widget` /
  `_search_matches` / `_render_search_results` stay -- Discover's box still needs them.
