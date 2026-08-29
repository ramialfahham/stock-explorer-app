# Task contract

objective: Show each Discover card's own listing venue on its meta line, so a reader meeting
  the same company twice across markets (Shell, Rio Tinto, Block Inc, etc.) can tell the two
  cards apart. Format "{market} · {position} of {total}" (Option B from the reviewed mockup),
  owner-approved 2026-08-29 ("go with option B"). Goes through the UX PR gate
  (`docs/working_agreement.md`).

scope_paths:
  - frontend/explore_filters.py
  - frontend/app.py
  - docs/north_star.md
  - docs/ui/discover_header.md
  - tests/frontend/test_explore_filters.py
  - .claude/task/contract.md
  - .claude/task/review.md
  - .claude/active_work.md

decisions_reserved:
  - **The exact format was decided via a reviewed mockup**, not here: market leads, queue
    position follows, "·" separator (matching the app's existing convention elsewhere, e.g.
    the header's "{N} left · {N} saved"). Not re-litigated.
  - **Scope of the fix: Discover only.** Saved and Search already show the card's own market
    via `build_card_html()`'s existing fallback (`_format_market_code`, used whenever no
    `scope_meta` is passed): they have no queue-position concept, so they already read
    correctly today (e.g. "FTSE 100" alone). Only `_render_discover_tab` in `frontend/app.py`
    overrides that fallback with a position-only string, which is the actual gap. Confirmed by
    reading every caller of `render_stock_card`, not assumed.
  - **`docs/north_star.md:128` is being reversed, not just extended.** It currently reads
    "position copy is scope-aware ... market/sector live in filters and card sector header,
    not repeated on the card meta line": the exact rule this task changes. This is the same
    decision the owner already made resolving the duplicate-cards issue ("we should see on
    each card, where it is listed"); this task's job is to make the doc match the decision,
    not to make a new one.
  - **Always show the card's own market, not just when the filter is "All markets."** The
    mockup showed it unconditionally; a conditional ("only show market when duplicates are
    possible in this filter scope") would be a different, unreviewed design and adds a branch
    for no benefit: a single market-filtered queue showing its own (redundant-with-the-filter)
    market on every card is harmless, and uniform behavior is simpler to reason about and test.

done_when:
  - `frontend/explore_filters.py` gains `card_venue_line(*, position, total, market_code)`,
    pure, mirroring `walk_progress_line`'s shape: returns `""` when `total <= 0`, else
    `f"{market_display_name(market_code)} · {position} of {total}"`.
  - `frontend/app.py`'s `_render_discover_tab` passes the card's own `market_code` through
    `card_venue_line` instead of `walk_progress_line` for `scope_meta`. `walk_progress_line`
    stays (still exported, still tested) since nothing else in this task's scope proves it's
    now dead code; removing it would be a separate, unreviewed cleanup.
  - `docs/north_star.md`'s Discover explore-model table row is corrected: market now IS
    repeated on the card meta line, by design, to disambiguate a company listed on more than
    one market in scope. Versioned (v2.3 -> v2.4) per that doc's own convention.
  - `docs/ui/discover_header.md` is corrected too, found by round-1 scope-auditor review, not
    the original plan: its own "Authority" line cited v2.3, and its "Belongs in header vs
    elsewhere" table listed "walk position" and "market name on card meta" as two separate
    facts, which this change unifies into one line. Both fixed.
  - `tests/frontend/test_explore_filters.py` gains unit tests for `card_venue_line`: normal
    case matches the approved format exactly; `total <= 0` returns `""`; a `None`/unknown
    market_code degrades to `market_display_name`'s own missing-data placeholder rather than
    crashing.
  - 480px smoke check (per the UX PR gate): no horizontal scroll on Discover; company, sector,
    and health verdict still visible without scrolling; first metric value still above the
    fold. Verified live in a browser, not assumed from the CSS alone.
  - `pytest` green, no other test touched or weakened.
  - No em dash or en dash on any added line.

impact_map:
  - Visible-copy change only: the Discover card's top line. No data model, query, or scoring
    change. `walk_progress_line` remains used nowhere after this change inside `app.py`, but is
    kept (see decisions_reserved) since dropping it is out of scope.
  - Affects every Discover card, not just the twelve cross-market duplicates: every card now
    shows its own market, which is new information on the ~470 non-duplicate cards too. That is
    the accepted tradeoff in the approved mockup (uniform behavior, not conditional).

amendments: (none)
