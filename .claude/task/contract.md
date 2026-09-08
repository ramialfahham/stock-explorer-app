# Task contract

objective: Cut Streamlit first-visit load time from minutes to seconds by fetching a slim
  deck (list/filter/search columns only), hydrating the full row only for the card actually
  being rendered, and caching both across browser sessions instead of per session.

  Owner's stated requirement, this session: "I want a reasonably good user experience from any
  user. as an executive i would close the app immediately and say it doesn't work." So the
  COLD path -- a first-time visitor with an empty `session_state` -- is what has to be fast,
  not just the second page view.

  Measured before (2026-09-08, live production): the app fetches all 4,683 eligible
  `mart_stock_cards` rows at `select=*` (79 columns) over 5 sequential PostgREST pages, plus
  1,039 `card_assessments` rows over 2 more, then discards ~78% of the mart rows in
  `dedupe_to_latest_snapshot` (only ~1,039 unique `(market_code, ticker)` survive). That is
  ~9-18 MB of JSON parsed and deduped in Python, on a free-tier shared-CPU Render instance,
  and `_ensure_all_cards` caches the result in `st.session_state`, which is per browser
  session -- so every new visitor pays it in full. `business_summary` alone is 66% of the
  mart payload and is only read when a card renders. Render itself is warm (0.42s TTFB
  measured), so spin-down is NOT the cause.

  Approved plan: `C:\Users\Rami\.claude\plans\jolly-cooking-sunset.md`.

scope_paths:
  - frontend/supabase_cards.py
  - frontend/app.py
  - frontend/explore_filters.py
  - frontend/overflow_menu.py
  - tests/frontend/test_supabase_cards.py
  - tests/frontend/test_explore_filters.py
  - tests/frontend/test_app.py
  - tests/frontend/test_app_e2e.py
  - docs/supabase_setup.md
  - docs/backlog/discover_list_performance.md
  - .claude/task/contract.md
  - .claude/task/review.md
  - .claude/active_work.md

decisions_reserved:
  - Adding a Postgres view (`DISTINCT ON` over `mart_stock_cards`) to dedupe server-side.
    Would cut the slim deck from 5 round trips to 1, but needs a migration plus a grant and
    a `coalesce` to preserve the `business_summary` backfill. A new mechanism, §6, owner's
    call. Explicitly OUT of this task -- revisit only if measurement after this change shows
    the slim deck is still too slow.
  - Evicting old snapshots at export time. Fixes the 4.5x over-fetch at source but deletes
    production rows. Destructive, owner's call, out of scope.
  - The deck cache TTL is a freshness decision AND interacts with the Supabase idle-pause
    keep-alive (open item 6). RESOLVED: the owner approved the plan
    (`jolly-cooking-sunset.md`), which specifies "Keep the deck TTL short (15-60 min)".
    30 minutes is shipped as a value inside that approved band, not a fresh decision. The
    band was chosen so ordinary traffic keeps querying Supabase well inside its ~7-day
    idle-pause threshold. Flagged back to the owner in the session summary regardless,
    since it is the one number here with a production side effect.
  - No user-visible copy, metric definition, label, format, or ordering changes. This task is
    strictly about WHEN and HOW MUCH data is fetched, never what a card says.

done_when:
  - The Discover/Saved/Search list, filter and count paths run off a slim column set; the
    full 79-column row is fetched only for the card being rendered.
  - Deck and card-detail fetches are cached across browser sessions, not per session.
  - `cards_lack_business_summary()` no longer fires against a deliberately-slim deck (it must
    be rescoped, not deleted -- it guards a real failure mode), proven by a mutation test:
    reverting the rescope must make a test fail, not just change a column count.
  - `fetch_card_detail` preserves the cross-snapshot `business_summary` backfill currently in
    `dedupe_to_latest_snapshot` (`frontend/explore_filters.py:87`).
  - BXB/RMS/SPK (`au_asx200`, legitimately stuck on the 2026-08-20 snapshot, open item 1)
    still appear in the deck -- no global `max(snapshot_date)` filter.
  - `pytest tests/frontend` green, including the `AppTest` end-to-end coverage.
  - The full suite (`pytest tests/ -q`, what CI actually runs) green locally BEFORE the
    first push. CORRECTION: an earlier draft of this line named `ruff` and `sqlfluff`.
    Neither applies -- `ruff` is not installed and is in no CI job, and `sqlfluff` lints
    only `dbt_analytics/`, which this task does not touch.
  - Fetch cost measured against production Supabase, before and after, both recorded in
    `review.md`. CORRECTION: an earlier draft of this line promised browser first-paint
    timing from a fresh incognito session. What was actually measured is the data-layer
    cost (round trips, bytes, seconds) plus a manual end-to-end pass against the running
    dev server. The browser-side paint number was never produced and is not claimed.

impact_map: Frontend consumption layer only. No dbt model, no ingestion, no Supabase schema
  and no exported column changes -- `mart_stock_cards` and `card_assessments` are read
  exactly as they are today, only with narrower `select=` lists and different call timing.
  Downstream of the frontend there is nothing; the marts are unaffected.

amendments:
  - Review round 2 (scope-auditor PASS, cto-reviewer FAIL) found one real bug and two false
    numbers of mine. The bug: `_descriptions_missing` swallowed EVERY exception into False,
    including PostgREST's 42703 for a missing `business_summary` column -- which is exactly
    the pre-migration-004 state the overflow-menu caption exists to announce, so the guard
    failed open on its own trigger. Fixed with `is_undefined_column_error()`
    (`supabase_cards.py`): a 42703 answers True, anything else stays quiet. The numbers: the
    cold-path round-trip headline said 5 when the eagerly-computed popover probe makes it 6
    (7 -> 6, not 7 -> 5), and a handover claim that the UptimeRobot ping reaches Supabase
    "because the card fetch is uncached per request" was true before this branch and false
    after it.
  - DELIVERY SHORTFALL against the approved plan, disclosed rather than buried: the plan
    (`jolly-cooking-sunset.md`) estimated ~150-250 KB over 1-2 round trips on the cold path.
    Delivered is 1.46 MB over 6. The KB estimate was sized against the ~1,039 rows that
    survive dedupe, but the deck still fetches all 4,683 and dedupes client-side; 4,683 rows
    cannot fit in fewer than 5 PostgREST pages, so 1-2 round trips was never reachable
    without the reserved `DISTINCT ON` view. Still a 12.6x payload cut and a 4x time cut, but
    the estimate was wrong and the gap is the owner's to close or accept.
  - Two disclosed behaviour differences in the rescoped export diagnostic, neither fixed
    (both would cost a cold-path round trip to detect, for states that already render
    correctly): `export_lacks_business_summary` returns True for a completely EMPTY eligible
    set where the old `cards_lack_business_summary` returned False, and
    `gt("business_summary", "")` counts a whitespace-only summary as present where the old
    check stripped it. `scripts/check_export_health.py` already gates fill at source.
  - Review round 1 (scope-auditor FAIL, cto-reviewer FAIL) found four defects that were
    fixed rather than argued: (1) `_ensure_all_cards` cleared only `session_state`, so a
    stale-shaped deck came straight back out of the cross-session cache and the guard
    spun forever instead of recovering -- now calls `_cached_deck.clear()`, mutation-
    verified; (2) the guard's docstring claimed the cache "outlives a deploy", false for
    `persist=None` -- rewritten to state the narrow case it actually covers; (3) the
    export probe cached a swallowed exception as "no problem" for a full TTL window --
    the try/except moved outside the cached call so a transient error retries; (4) a NEW
    user-visible error string had been added in `_hydrate` while this contract reserves
    user-visible copy -- now reuses `_load_cards`' existing wording verbatim. Two stale
    docs found by the same round are fixed under the scope addition above.
  - Added `frontend/overflow_menu.py` to scope_paths. It was a second, unforeseen consumer
    of `cards_lack_business_summary()` -- it renders an operator caption warning that
    company descriptions are missing from the export. Once `business_summary` left the
    deck by design, that caption would have displayed permanently and falsely. Deleting it
    would be a §6 user-visible-copy decision, so instead the diagnostic is preserved and
    answered by a new one-row probe (`export_lacks_business_summary`, NULL-safe via
    `gt("business_summary", "")`). No copy changed. CORRECTION, caught by both reviewers:
    an earlier draft of this amendment justified the probe as running "only when the menu
    is opened". That is false -- a `st.popover` body is computed eagerly unless it opts
    into `on_change="rerun"`, so the probe runs on every script run including the first
    cold one. The @st.cache_data wrapper is what holds it to one round trip per TTL
    window; the honest cost is one extra single-row request per window, not zero.
  - NOT done, flagged for the owner instead: the deck load still shows no progress
    indicator (`show_spinner=False` on both caches). A spinner with a message would help
    perceived speed on the first visit, but its text is user-visible copy, §6.
  - Noted, not acted on: `scripts/check_export_health.py` is a pre-export gate that already
    checks `business_summary` fill on latest snapshots, so the overflow-menu caption is a
    redundant second copy of a check that already blocks a bad export at source. Whether to
    retire the UI caption is the owner's call, out of scope here.
