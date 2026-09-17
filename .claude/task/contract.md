# Task contract
> DISPOSABLE. **Owns:** THIS task's objective, `scope_paths`, reserved decisions and
> `done_when`.
> **Never:** anything that outlives the task. Overwritten by the next task.

objective: Closes #16. Today "Not now" is recorded as an interaction with no visible
  effect on the list -- the reader has no way back to a skipped company except re-finding
  it via Search or Discover. Add a "Not now" review list, structurally identical to Saved's
  own list (same `row_ui` pattern, same focus/back-row mechanics), reachable from the
  overflow (⋯) menu rather than a fourth bottom-nav tab -- decided via AskUserQuestion.

  Design, worked out this session (not a new AskUserQuestion round -- these are mechanics,
  not product decisions, and follow the confirmed direction directly):
  - The panel is an overlay reachable from ANY tab via the overflow menu (`not_now_open`
    session flag), not a new `NAV_PAGES` entry -- avoids `st.segmented_control`'s `default=`
    needing to be one of its own `options`, which a real 4th nav value would break.
  - Tapping a different bottom-nav tab while the panel is open closes it (mirrors how
    opening Saved/Search implicitly abandons whatever focus state a prior tab was in).
  - A skipped company's detail view offers **Save** (moves it to Saved) and **Remove**
    (drops it from the list) -- needs a new `unskip` interaction action, mirroring the
    existing `unsave`. No DB schema change: `user_interactions.action`'s CHECK constraint
    is already known-stale and unenforced (nothing live writes to that table; interactions
    live in a browser cookie, per `.claude/active_work.md`'s existing note on this).
  - `saved_keys_with_order`'s tie-break logic (latest action wins) is generalized into a
    shared `_latest_action_keys(interactions, add_action, remove_action)` so the new
    `skipped_keys_with_order` can't silently diverge from it -- proactive, not a
    reviewer-driven fix this time.

  **Round 1 (cto-reviewer) FAILED, both findings real, both fixed:**
  1. **`browser_storage.py` never persisted skip/unskip.** Its whole cookie module was
     built on the documented premise "skips have no effect on any screen... so they stay
     in session state only" -- exactly true until this task, and the diff added the
     `unskip` action string without touching that premise anywhere. Result: the Not-now
     list would silently reset on every reload, contradicting the issue's own goal.
     Fixed by generalizing the module's save-cookie machinery (state-encoding, chunking,
     the write script, `ensure_interactions_loaded`) to a second, independent cookie
     namespace (`SKIP_COOKIE_PREFIX = "ss_skipped_"`), parameterized the same way the
     `_latest_action_keys` generalization above already established the pattern for.
     Live-verified: skip a company, reload the page for real, it's still in Not-now.
  2. **The save+unskip fix only covered ONE of the two Save buttons.** Discover's own
     sticky "Save" action (`_render_sticky_actions`) appended `"save"` only -- a card
     skipped, then re-encountered and saved directly from Discover (filter_pool doesn't
     exclude skipped tickers), would end up saved AND stuck in Not-now. Fixed by
     extracting a shared `_save_card()` that always appends both `save` and `unskip`,
     used by both Save buttons so neither can drift from the other again.
  3. **Found while fixing #1, not a reviewer finding:** `clear_interactions()` ("Clear
     saved") reset the WHOLE interactions list, including skip rows -- harmless while skip
     was session-only, but now would silently wipe Not-now too, without its own
     confirmation dialog ever mentioning that. Scoped it to save/unsave rows only.

scope_paths:
  - frontend/explore_filters.py
  - frontend/app.py
  - frontend/overflow_menu.py
  - frontend/browser_storage.py
  - tests/frontend/test_explore_filters.py
  - tests/frontend/test_app_e2e.py
  - tests/frontend/test_app.py
  - tests/frontend/test_browser_storage.py
  - docs/ui/discover_header.md
  - .claude/task/contract.md
  - .claude/task/review.md

decisions_reserved: none -- the one product decision (should skipped companies be
  revisitable, and how) was answered via AskUserQuestion before this contract was written.

done_when:
  - `explore_filters.py`: `skipped_keys_with_order()` mirrors `saved_keys_with_order()` via
    a shared `_latest_action_keys()` helper.
  - Overflow menu shows a "Not now (N)" entry with the current skipped count.
  - Opening it shows a row list of skipped companies (empty state if none); selecting one
    shows its card with Save and Remove actions.
  - Save moves the company out of the not-now list (records a `save` interaction); Remove
    drops it (records an `unskip` interaction). Both return to the list.
  - Switching bottom-nav tabs while the panel is open closes it cleanly, no leftover state.
  - `docs/ui/discover_header.md`'s overflow-menu section documents the new entry.
  - Verified live against a running dev server: skip a company on Discover, open Not now
    from the overflow menu, confirm it appears, open it, Save it, confirm it's gone from
    Not now and appears in Saved. Then, separately: skip a company, verify a real page
    RELOAD (not just an AppTest run) keeps it in Not-now; confirm "Clear saved" leaves it
    untouched.
  - `pytest tests/frontend/ -q` green, with new coverage for `skipped_keys_with_order`,
    `skipped_state`/cookie encode-decode under `SKIP_COOKIE_PREFIX`, `_save_card` clearing
    skip status, `clear_interactions` preserving skip rows, and AppTest e2e paths for the
    full round trip, the tab-switch-closes-panel behavior, and Remove.

impact_map: frontend-only. New action string `unskip` (interaction-log convention, not a
  schema change -- the DB CHECK constraint is already known-stale/unenforced). New cookie
  namespace `ss_skipped_*`, additive -- no existing `ss_saved_*` cookie shape changes. No
  schema, dbt, ingestion, or CI change.
