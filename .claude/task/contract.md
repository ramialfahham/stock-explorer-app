# Task contract

objective: Fix the remaining ~1-2s click-to-response delay the owner reported after the
  Discover pagination fix ("substantially faster... but still delayed"). Root cause found by
  direct server-side timing instrumentation (temporary, not shipped): `get_anon_client()`
  (`frontend/supabase_client.py`) rebuilds a brand-new Supabase client via `create_client(url,
  key)` from scratch on every single Streamlit script rerun, with zero caching -- unlike card
  data, which is correctly cached in `session_state`. Measured cost: ~1.06-1.09s per run,
  consistently, versus ~0.12-0.18s for everything else in a run combined (list rendering, pool
  filtering, pagination). Because `frontend/row_ui.py`'s row click handler calls `st.rerun()`
  right after registering a click (aborting the in-flight run and starting a fresh one), this
  cost is paid twice per click, not once -- closely matching the owner's reported 1-2s.

scope_paths:
  - frontend/supabase_client.py
  - tests/frontend/test_supabase_client.py
  - docs/backlog/discover_list_performance.md
  - .claude/task/contract.md
  - .claude/task/review.md
  - .claude/active_work.md

decisions_reserved: none -- this is a pure technical fix with a well-established Streamlit
  idiom as the answer (`st.cache_resource`, the framework's own primitive for exactly this: an
  expensive-to-construct, shareable resource like a DB/API client, safe to cache once across all
  sessions since it carries no per-user state -- this is the anonymous, non-user-specific
  client). No product/UX/metric/naming decision involved.

done_when:
  - `get_anon_client()` is decorated with `@st.cache_resource` (or equivalent), so
    `create_client()` runs once, not on every script rerun. Done.
  - `tests/frontend/test_supabase_client.py` covers the caching behavior (two calls return the
    same object, `create_client` invoked once) and confirms the credential-missing error path
    re-raises on every one of three consecutive calls, not just the first (a cached resource
    must not paper over a genuinely missing configuration by caching the exception itself).
    Done, both verified to test real behavior via mocks. **Round-1 cto-reviewer catch:** the
    first draft called `get_anon_client()` only once under missing credentials, which cannot
    distinguish a real fix from a regression where the failure gets cached and a second call
    returns something falsy instead of re-raising -- fixed to call it three times.
  - `pytest` green. Done: 430 passed (428 baseline + 2 new).
  - Live verification, not assumed from the code: with the dev server warm (cache populated),
    click a row and confirm the click-to-focus-card delay drops close to the ~0.12-0.2s floor
    the rest of a run already costs, via the same server-side timing methodology used to
    diagnose this (temporary instrumentation, removed before commit) -- not the browser-side JS
    timer approach, which this session already found unreliable (throttled on a
    reported-hidden preview tab). Done: measured two clicks post-fix at ~0.30s and ~0.47s total
    click-to-response (click event to the fresh rerun completing), down from ~1.2-1.4s for a
    single run pre-fix (and correspondingly worse across the two runs a click actually costs).
    The one-time `create_client()` cost is now paid once per server process (cached globally via
    `st.cache_resource`, not per-session), confirmed by the first page load after a server
    restart still paying it once while every subsequent run, including the very next one in the
    same load, was already fast.
  - No em dash or en dash on any added line.

impact_map:
  - `frontend/supabase_client.py` only; single call site (`frontend/app.py`'s `main()`).
  - No change to Supabase query logic, RLS, auth scope, or the data the client fetches -- only
    how often the client object itself is constructed.
  - Does not touch `frontend/row_ui.py`'s `st.rerun()`-inside-the-loop pattern (the second,
    separately-identified contributor to click latency) -- that is a larger, riskier
    restructuring of code shared by Discover/Saved/Search, out of scope for this fix. Flagged
    for the owner as a possible follow-up, not actioned here.

amendments: (none)
