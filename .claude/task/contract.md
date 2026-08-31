# Task contract

objective: Fix the Discover list's severe click-registration slowness (~2.4s before Streamlit
  even registers a click, owner reports it as "nothing happens... takes an infinity") by
  paginating the list, per owner decision after being presented the options in
  `docs/backlog/discover_list_performance.md`: pagination, 30 rows per page. Root cause already
  confirmed by direct measurement in that doc: the full ~923-row list mounts ~931 `st.button`
  widgets and ~20,600 DOM nodes unconditionally, every render, with no pagination/windowing.
  Pagination caps the live widget count per render regardless of where a click lands in the
  list, which the doc's own reasoning says should independently shrink both the confirmed
  click-registration delay and the (separately unconfirmed) inconsistent-rerun-duration symptom.

scope_paths:
  - frontend/app.py
  - frontend/styles.py
  - tests/frontend/test_app.py
  - tests/frontend/test_styles.py
  - docs/ui/discover_list.md
  - docs/ui/design_system.md
  - docs/backlog/discover_list_performance.md
  - docs/north_star.md
  - docs/ux_principles_finanz_lern_apps.md
  - README.md
  - .claude/task/contract.md
  - .claude/task/review.md
  - .claude/active_work.md

decisions_reserved: none for this task -- approach (pagination) and page size (30) were both
  explicitly decided by the owner this session, in response to a direct question presenting the
  backlog doc's candidate directions.
  - **Round-1 scope-auditor escalation, owner's answer recorded 2026-08-31:** whether the specific
    pagination control shape (Previous/Next labels, "Page N of M" text, hide-entirely-vs-disable
    on a single-page pool) also needed owner sign-off, separately from the abstract
    pagination/page-size decision -- `docs/backlog/discover_list_performance.md`'s own Open
    Questions section states this class of call ("page size and pagination UI are user-facing,
    composition/ordering concerns... not something to default silently") is not the builder's to
    default. Owner was shown the built shape directly and asked "Good to ship as-is?"; answered
    **"Ship as-is."** No further change made as a result; recorded here (and in
    `.claude/active_work.md`) because the answer previously existed only in chat, not in any
    artifact a cold reviewer or a future session could check -- that gap is what round 2 of this
    branch's review correctly failed on.

done_when:
  - The Discover list renders at most `DISCOVER_PAGE_SIZE` (30) rows per page, via slicing the
    already-computed, already-sorted `pool` before it reaches `row_ui.render_rich_row_list` --
    no change to `frontend/row_ui.py`'s tap-target mechanics, pool computation, filtering, or
    sort order.
  - Changing the market/sector filter resets the page back to the first page (via the existing
    `_on_filter_change` callback already wired to both selectboxes).
  - The current page index is clamped defensively against the pool's actual current length (not
    just reset on filter change), so a shrinking pool for any other reason never leaves the page
    index pointing past the end.
  - Previous/Next controls render below the list, disabled at the first/last page respectively,
    and are hidden entirely when the pool fits on one page (no dead controls for small filtered
    scopes, e.g. a single market).
  - `pytest` green.
  - Live verification, not assumed from the code: with the full unfiltered pool, confirmed at
    most 30 tappable rows and 40 buttons total are mounted (measured directly via DOM query: 40
    buttons / 942 DOM nodes, down from the pre-fix ~931 buttons / ~20,600 nodes -- smaller than
    the backlog doc's own reference "fast" 39-company market). Confirmed the correct company
    opens on row click, at the first row, a middle row, and the last row on a page, with the
    MR !67 tap-target fix (real pixel hit-testing, `document.elementFromPoint`) still resolving
    correctly at both edges of each. Confirmed Next/Previous move between pages and land on the
    correct rows. **Not obtained**: a reliable click-to-response elapsed-time number -- this
    automation environment throttles JS timers on the (always-reported-hidden) preview tab,
    which produced a misleading ~7-8s reading on a page that structurally cannot be that slow
    (40 buttons). The structural, DOM-count evidence is the verification of record here; a
    human timing check on the shipped app is the way to close this out, not another automated
    timer.
  - `docs/backlog/discover_list_performance.md` updated to record the decision and that it's
    been acted on (not left as an open backlog item once shipped).
  - `docs/ui/discover_list.md` updated to describe pagination as part of the list's layout.
  - No em dash or en dash on any added line.

impact_map:
  - Discover list only. Saved and Search use the plain, already-small row list, out of scope
    (the backlog doc's own open question named this and left it out of scope for now).
  - Pure display-layer slicing; no change to pool computation, filtering, sort order, or the row
    primitive's tap-target mechanics (`frontend/row_ui.py` untouched).
  - No dbt, ingestion, or data model change.
  - Does not touch or reopen `docs/backlog/discover_first_time_default.md`'s decision (full list
    stays for every visitor) -- pagination changes how much of the list is mounted at once, not
    how much is browsable; the full pool is still reachable via Next, unfiltered by default.

amendments:
  - **`frontend/styles.py` and `tests/frontend/test_styles.py` added to scope, not anticipated
    at Confirm time.** Found live while verifying: the row-tap-target CSS from MR !67 scopes
    itself via `div[data-testid="stVerticalBlock"]:has(.ss-row)`, a bare `:has()` that matches
    at ANY descendant depth, not just the nearest one -- so it also matches the single big
    stVerticalBlock wrapping the *entire* list (every row is nested inside it too), not only
    each row's own small per-row container. The new Previous/Next buttons, being the first
    other `st.button()` rendered inside that same big wrapper, silently inherited the row-only
    `position: absolute; inset: 0` rule and stretched to the full list's height (~2780px)
    instead of rendering as normal buttons. This is a pre-existing scoping gap in MR !67's own
    rule, not something this task's pagination change introduced structurally -- it simply was
    never exercised before, since no other `st.button()` had ever shared that DOM scope. Fixed
    by tightening five selectors to `:has(> [data-testid="stElementContainer"] .ss-row)` (direct
    child, matching a pattern already used correctly elsewhere in the same file for the hover
    rule), which only matches each row's own container, never the big outer one. Added two new
    regression-guard tests to `tests/frontend/test_styles.py` matching that file's own
    established pattern (a positive presence check plus a negative shape check), both verified
    to fail against the broken form before being kept, same discipline as every other guard in
    that file.
