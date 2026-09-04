# Task contract

objective: Close out backlog item 4 ("`frontend/browser_storage.py` has zero test coverage") --
  one of the agent-executable items from today's open-issues list, no owner decision needed.
  `browser_storage.py` wraps `streamlit_extras`'s `local_storage_manager`, a real custom
  component that only responds inside a live browser session; that's why it had no coverage
  while every other frontend module does. Fixed by faking the component (a small `_FakeManager`
  test double controlling `.ready()`/`.get()`) and exercising `st.session_state` directly --
  confirmed live that `st.session_state` works as a real dict-like object outside `streamlit
  run` (a documented "bare mode" warning, not a failure), so no session_state mock was needed.
  Matches this repo's own established convention of testing pure/session-state logic directly
  rather than the Streamlit-calling render shell (see `test_app.py`'s discover-pagination
  comment for the precedent this follows).

scope_paths:
  - tests/frontend/test_browser_storage.py (new file)
  - .claude/active_work.md
  - .claude/task/contract.md
  - .claude/task/review.md

decisions_reserved: none -- this is pure test-coverage addition for existing, unchanged
  behavior. No metric, copy, or product decision anywhere in scope.

done_when:
  - Every public function in `browser_storage.py` has at least one test:
    `_parse_interactions` (pure -- every input shape: None, list, valid/invalid JSON string,
    unexpected type), the pending-write queue (`_pending_store`/`_queue_storage_write`/
    `_queue_interactions_write`), `get_interactions`/`storage_sync_pending` (including that
    `get_interactions` returns a copy, not the live list), `append_interaction`/
    `clear_interactions` (row shape, queued write, flags set, `st.rerun()` called), and
    `ensure_interactions_loaded`'s full boot sequence: not-ready triggers exactly one rerun,
    the boot flag prevents a second one, ready reads/parses/stores correctly,
    `sync_pending` is set only when non-empty, and an already-loaded session returns the
    cached value without re-reading the component. `_mount_manager`'s per-run-id caching also
    covered (same run id reuses the instance, a new run id remounts).
  - Tests prove the actual branch, not just "doesn't crash" -- e.g. the boot-rerun-guard test
    asserts zero further `st.rerun()` calls once the flag is set, not just that the function
    returns something.
  - `pytest` full suite green (`505 passed`, up from 482 -- the 23 new tests, nothing else
    regressed).
  - No em dash or en dash on any added line.

impact_map:
  - Pure test addition. No production code in `frontend/browser_storage.py` (or anywhere else)
    changed -- this task adds coverage for existing, unmodified behavior, nothing more.
  - No CI, dbt, or Supabase surface touched.

amendments: scope-auditor's round-1 review correctly caught an out-of-scope edit: the
  `.claude/active_work.md` diff had also rewritten an unrelated open item (the Supabase
  free-tier pause risk) to "resolved," based on a live check done today but with no
  corroborating artifact in the repo and no connection to this task's own objective/scope_paths.
  Reverted that item back to its original text unchanged; the Supabase check itself was real
  (a live query succeeded) but belongs in whichever task's handover update actually concerns it,
  not bundled into a test-coverage task's contract. No other change.
