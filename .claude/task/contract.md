# Task contract
> DISPOSABLE. **Owner:** THIS task's objective, `scope_paths`, reserved decisions and
> `done_when`.
> **Never:** anything that outlives the task. Overwritten by the next task.

objective: Works #74 (FE-2 defects 23 and 24, FE-3 defect 25 of the quality-baseline audit re-run; the owner calls 27
  to 30 stay untouched). `docs/ui/discover_list.md` says search-result rows carry no numbers while the code, and
  `docs/ui/design_system.md`, give them the lead metric; the spec says an empty list is "one `st.info`" while an
  empty search shows `st.warning`; and `_render_bottom_nav` takes a `saved_count` it never reads. One rule: the
  spec and the code say the same thing, and a parameter that nothing reads is removed.

scope_paths:
  - frontend/app.py
  - tests/frontend/test_app_e2e.py
  - docs/ui/discover_list.md
  - .claude/active_work.md
  - .claude/task/contract.md
  - .claude/task/review.md

decisions_reserved: Answered by the owner in chat. Defect 23: A, search-result rows keep the lead metric, so
  `discover_list.md` is corrected to match the code and `design_system.md`; no code change. Defect 24: A, an empty
  search shows `st.info` (not `st.warning`) with the text it has today, and the "Empty state" row of
  `discover_list.md` says so. Defect 25 is mechanical (a parameter nothing reads). No other copy, layout, token or
  interaction changes.

changes:
  - `docs/ui/discover_list.md`: the heading and first paragraph of "Why this list is richer than ..." name Saved rows
    only as the picking rows with no numbers, and say search results share this list and its lead metric (one pool,
    one rendering path, as `design_system.md` says). The "Empty state" row says one `st.info`, and that an empty
    search shows `No matches for “<query>”.` in it.
  - `frontend/app.py`: the empty-search message is `st.info(f"No matches for “{query}”.")`; `_render_bottom_nav`
    loses `saved_count`, and `_discovery_page` stops passing it (it keeps its own `saved_count` for
    `_render_saved_scope_stats`).
  - `tests/frontend/test_app_e2e.py`: the no-match search test asserts the message is an info box and that no
    warning box shows.
  - `.claude/active_work.md`: current facts.

done_when:
  - `git grep -n -E "richer than Saved's or search results|search-result rows are picking rows" -- docs frontend tests`
    finds nothing.
  - `git grep -n "st\.warning" -- frontend` finds nothing (the only use was the empty search).
  - `_render_bottom_nav` has no `saved_count` parameter and no caller passes one: `git grep -n "_render_bottom_nav" --
    frontend tests` shows only the definition, the one call with `client=` alone, and prose mentions.
  - The e2e test fails when the empty search shows `st.warning` again, and when the text changes (mutation-checked).
  - `pytest tests -q` passes; `python scripts/check_context_budget.py` passes; the UX PR gate in
    `docs/working_agreement.md` is answered in the merge request.

known_limits:
  - No live run against Supabase: the app needs keys this machine does not have; the Streamlit AppTest e2e suite
    renders the real page against a mocked client.
  - The colour change (yellow box to blue box) for an empty search is the owner's answer A; no other widget moves.

regression_checklist:
  - Every other e2e test of search, Discover and Saved passes unchanged.
  - The empty filter scope still shows its own `st.info` text; Saved's empty state is untouched.
