# Task contract

objective: Two small, already-diagnosed UI bugs from the row-tap-target investigation, both
  confirmed in code before this task started, neither requiring a product decision:
  1. **Market filter dropdown offers markets with zero companies.** `frontend/markets.py`'s
     `MARKET_DISPLAY_NAMES` is a static, hardcoded 9-market dict; `explore_filters
     .market_filter_options()` lists every entry in it regardless of whether that market
     actually has any eligible companies exported yet. Confirmed live earlier this session via
     direct Supabase query: 4 of the 9 markets (France, Netherlands, Switzerland, Spain) are
     onboarded but have zero exported data (pipeline hasn't run for them since onboarding), so
     the Filters popover currently offers four choices that silently return an empty list.
  2. **Filters/stats stay visible on the focus card.** `frontend/app.py`'s
     `_render_explore_filters()` and the "remaining match your filters" portion of
     `_render_scope_stats()` are called unconditionally whenever `active == "Discover"`, with no
     check for whether a card is currently focused -- so "923 match your filters" and a Filters
     button that only makes sense for browsing the list both stay visible while looking at one
     specific company's Snapshot.

scope_paths:
  - frontend/explore_filters.py
  - frontend/app.py
  - tests/frontend/test_explore_filters.py
  - docs/ui/discover_header.md
  - .claude/task/contract.md
  - .claude/task/review.md
  - .claude/active_work.md

decisions_reserved: none -- both are bug fixes with an already-diagnosed, mechanically-verifiable
  root cause, not a product/UX decision. The user-facing content itself (market names, stats
  wording) is unchanged; only which markets are offered and when the row is shown changes, both
  restoring already-established, already-approved behavior (a filter shouldn't offer an empty
  result; chrome that's list-only shouldn't persist onto the single-item focus view, matching
  how the rest of Discover's chrome already behaves).

done_when:
  - `market_filter_options()` takes the live `cards` list (matching `sectors_for_market()`'s
    existing pattern) and only includes a market if at least one eligible card exists for it,
    preserving `MARKET_DISPLAY_NAMES`'s registry-ingest-order ordering among the ones shown.
    "All markets" always included regardless.
  - The call site in `frontend/app.py`'s `_render_explore_filters` passes the already-available
    `cards` list. If `st.session_state["explore_market"]` holds a code no longer in the live
    options (a market that just dropped out), it's reset to `default_market_filter()` before the
    selectbox renders, matching the existing self-healing pattern already used for
    `explore_sector` two lines below it -- not left to crash `st.selectbox` on a stale value.
  - `_render_explore_filters()` and the "remaining match your filters" portion of
    `_render_scope_stats()` (i.e. `show_remaining`) are both skipped when a Discover card is
    currently focused (`st.session_state.get("discover_focus_key")` set), matching how the rest
    of Discover's list-only chrome already doesn't appear on the focus view. `saved_count` still
    renders regardless of focus state, matching Saved's own already-established behavior of
    never hiding it.
  - `docs/ui/discover_header.md` updated: row 5 (Filters) and row 6 (Stats) in the vertical-order
    table, and the wireframe/its caption, no longer imply both always show regardless of focus.
  - `tests/frontend/test_explore_filters.py` covers `market_filter_options()`'s new filtering
    behavior: a market with an eligible card is included, one with zero eligible cards is
    excluded, "All markets" is always present and first, ordering among included markets matches
    `MARKET_DISPLAY_NAMES`'s own order.
  - `pytest` green. Done: 435 passed (430 baseline + 5 new).
  - Live verification, not assumed from the code: with the dev server warm, confirm the Filters
    popover's market list matches the markets actually present in the live pool (not the full
    static 9); confirm opening a focus card hides the Filters row and the "N match your filters"
    text, and confirm "Back to list" restores both; confirm Saved and Search are unaffected
    (their own header behavior is untouched by this change). Done: confirmed via the accessibility
    tree that all 5 markets with live eligible data (S&P 500, FTSE 100, Nikkei 225, ASX 200,
    DAX) appear in the dropdown and all 4 without data (CAC 40, AEX, SMI, IBEX 35) don't; opening
    a row hid the Filters button and "match your filters" text while "0 saved" remained, "Back to
    list" restored both, and Saved's own header (unaffected code path) still showed correctly.
  - **`docs/working_agreement.md`'s UX PR gate, checked explicitly (round-1 scope-auditor catch --
    this diff is a Discover-chrome interaction change and the gate applies unconditionally, not
    only when a product decision is involved):**
    1. **north_star check** -- `docs/north_star.md`'s Discover Browse row already states focus
       view uses "the same layout Saved's focus view already uses." Saved has no Filters row at
       all, so hiding Discover's on focus brings it INTO alignment with this rule, not away from
       it.
    2. **Component specs** -- `docs/ui/discover_header.md` updated in this same diff (vertical-
       order table, wireframe, Filters-popover section, 480px checklist) to match.
    3. **One primary job** -- goes in the MR description, not this contract.
    4. **Mobile wireframe** -- goes in the MR body (an ASCII sketch of the collapsed focus-view
       header), matching `discover_header.md`'s own updated wireframe.
    5. **480px smoke** -- actually exercised at a 480x900 viewport (not just desktop-width
       accessibility-tree checks, which is all round 1 had): no horizontal scroll on the list or
       the focus view; Filters row genuinely absent with no leftover gap on focus (screenshot
       confirmed); Save/Not now reachable; "Back to list" restores the Filters row and stats text
       with no horizontal scroll either.
  - No em dash or en dash on any added line.

impact_map:
  - Discover tab only; Saved and Search's own header/stats logic is untouched.
  - Pure display-layer filtering and a visibility condition; no change to pool computation,
    card eligibility, or the underlying Supabase query/export.
  - No dbt, ingestion, or data model change.

amendments:
  - **Round-1 scope-auditor catch:** the original contract's `decisions_reserved` argued only
    that neither bug needed a §6 product/UX decision, which answers the working agreement's
    decision-rights question but not the separate, unconditional UX PR gate in
    `docs/working_agreement.md` (it does not carve out well-diagnosed bug fixes). Fixed: all
    five gate items walked through explicitly above, and the 480px smoke was actually run at a
    480x900 viewport (round 1's live verification only checked desktop width via the
    accessibility tree, not mobile).
