# Task contract

objective: Rework Discover from a one-card-at-a-time walk into filter -> scrollable list ->
  tap-to-focus, mirroring the pattern Saved already uses, so filtering produces a visible
  result instead of an invisible change to an abstract queue. List rows show a health verdict
  plus one type-aware lead metric (Variant B, approved 2026-08-29 from a reviewed mockup):
  Operating margin for operating companies, Return on equity for financial companies, Cash
  runway (months) for pre-revenue companies (split by type, revised 2026-08-29, see
  decisions_reserved below), each a CORE, verdict-deciding axis for that company type's own
  verdict rule in `scripts/assessment_rules.py`, not a metric chosen for this task alone. This
  reverses a documented v2.4 decision (`docs/north_star.md`: "Browse list: Removed... Discover
  is filter + walk only") by explicit owner instruction, not a reinterpretation.

scope_paths:
  - frontend/app.py
  - frontend/row_ui.py
  - frontend/card_copy.py
  - frontend/discovery_queue.py
  - frontend/explore_filters.py
  - frontend/landing.py
  - frontend/overflow_menu.py
  - frontend/styles.py
  - docs/north_star.md
  - docs/ui/design_system.md
  - docs/ui/discover_header.md
  - docs/ui/saved_list.md
  - docs/ui/discover_list.md
  - README.md
  - docs/ux_principles_finanz_lern_apps.md
  - docs/backlog/discover_metric_filters_phase2.md
  - docs/data_contract.md
  - dbt_analytics/models/_docs.md
  - dbt_analytics/models/5_marts/_marts.yml
  - dbt_analytics/models/4_intermediate/_intermediate.yml
  - frontend/markets.py
  - tests/frontend/test_row_ui.py
  - tests/frontend/test_card_copy.py
  - tests/frontend/test_explore_filters.py
  - .claude/task/contract.md
  - .claude/task/review.md
  - .claude/active_work.md

decisions_reserved:
  - **Lead metric mapping revised 2026-08-29, superseding the original approval above.**
    The as-approved mapping (operating/financial -> `statement_roe_pct`) was wrong for
    `operating`: `equity-analyst-reviewer`'s round-5 review checked it against
    `scripts/assessment_rules.py:159-198` and found `statement_roe_pct` is only a
    **supporting** axis in `_verdict_operating` ("can break a tie but never rescue a red
    flag," that function's own comment), never one of the three **core** axes
    (`net_debt_to_ebitda`, `ebit_margin_pct`, `fcf_margin_pct`) that alone decide red/green.
    For `financial` the same metric genuinely is co-primary in `_verdict_financial`, so the
    defect was operating-only. Presented three options to the owner (keep ROE for both and
    accept the weaker claim, drop the lead metric for operating entirely, or split by type);
    owner chose **split by type: `ebit_margin_pct` (Operating margin (TTM), importance_tier 1,
    one of the three core axes) for operating, `statement_roe_pct` stays for financial.**
    `pre_revenue -> cash_runway_months` is unchanged. Fixed in `frontend/card_copy.py`'s
    `_LEAD_METRIC_BY_TYPE` and `lead_metric_for_row()`, `tests/frontend/test_card_copy.py`,
    `docs/north_star.md`'s "List row" rule, and `docs/ui/discover_list.md`'s lead-metric table
    and wireframe.
  - **List order.** Recommending alphabetical by company name: stable, predictable, and a row
    stays where you last saw it. The current walk's round-robin/skip-deprioritization order
    (`discovery_queue.build_queue`) is stateful and session-interaction-dependent by design,
    which suits a sequential walk but not a list you re-scan (a row moving because you skipped
    something unrelated earlier is confusing, not helpful, in a list). If this reasoning is
    wrong, say so before implementation starts rather than after.
  - **The walk mechanism is retired, not kept as a dead parallel path.** `queue`, `queue_index`,
    `market_index`, `sector_shown`, `discovery_queue.py`'s `build_queue()`, and the "Next
    company" button are removed, not left unused. Confirmed via the round-2 explore: nothing
    outside `_render_discover_tab`/`_render_sticky_actions` consumes this state, so nothing
    else breaks. Flagged here because it's a bigger deletion than the "add a list" framing
    implies, and "no half-finished work" argues against leaving retired machinery in place.
  - **Found during implementation, not in the original plan: the overflow menu's "Start over"
    button is retired too.** It calls `on_start_over` -> `_start_over()` -> resets
    `queue_index`/`market_index`/`sector_shown` (`frontend/overflow_menu.py`'s
    `menu_start_over` button, `frontend/app.py`'s `_start_over`). Once none of those exist,
    the button has nothing left to do. No test or doc references it, so removal is clean.
    "Clear saved" is a separate, unrelated action and stays untouched.
  - **Also found during implementation: `card_venue_line()` (`frontend/explore_filters.py`)
    is retired too.** It exists solely to format the walk's "{market} · {position} of
    {total}" meta line; grepped the repo and confirmed its only production call site is the
    walk's own `_render_discover_tab`. The focus card no longer needs a position at all, so
    it doesn't pass `scope_meta`, falling through to `build_card_html()`'s existing
    `_format_market_code` fallback, exactly matching how Saved and Search already display a
    card's market. `walk_meta_line()` in the same file was already dead code before this task
    (a prior review found zero callers) and stays out of scope: unrelated to this change,
    not something to clean up opportunistically here.
  - **Also found during implementation: two more copy locations described the removed walk
    model and needed a mechanical correction, not a design decision.** The overflow menu's
    Discover tip (`frontend/overflow_menu.py`, `_DISCOVER_TIP`) said Not now "skips for
    later," which is no longer true under the decision below. The landing page
    (`frontend/landing.py`) had a bullet reading "walk one company at a time" and another
    repeating the same stale Not-now framing. Both corrected to describe the shipped
    behavior; this is not the broader landing/onboarding rethink flagged separately as its
    own follow-up, only fixing copy that would otherwise describe a feature that no longer
    exists.
  - **Found by round-1 scope-auditor review, not the original doc-sync sweep: four more
    stale references, one with an actively broken link.** `docs/north_star.md`'s "What we
    are building" overview still said "filter + walk" a hundred lines above the table this
    task already corrected; its "Out of scope for v1" list still carried "Discover browse
    list expander (removed...)" even though a browse list is exactly what ships.
    `docs/ui/design_system.md`'s 480px checklist compared a button's skin to "Next company,"
    a button this diff deletes. `README.md` (outside the original scope_paths, added here)
    highlighted "Deterministic discovery queue" with a markdown link to
    `frontend/discovery_queue.py`, which this diff deletes: a real broken link, not just
    stale prose, in the project's own front door. All four fixed.
  - **Found by round-2 scope-auditor review, a sibling doc one hop from a file already
    fixed.** `docs/ux_principles_finanz_lern_apps.md` (linked directly from
    `docs/north_star.md`, the very file round 1 corrected) still had a "Walk ordering"
    bullet describing the retired round-robin/hero-start behavior and a "No browse list"
    bullet stating the exact opposite of what ships. `docs/backlog/discover_metric_filters_
    phase2.md`'s acceptance criteria referenced a "Discover walk pool" that no longer
    exists. Both fixed. Also found on my own further sweep past what either review round
    asked for: `frontend/markets.py`'s `discover_pool_summary()` renders a **live,
    user-visible** string in the overflow menu's "About the data" panel reading "{market}
    first, then rotating worldwide," describing the retired walk's traversal order, not
    a doc, actual shipped copy. Corrected to state the hero market's count as a fact with
    no ordering claim; `HERO_MARKET_CODE`'s comment corrected too, since the constant
    itself is not dead (still drives `markets_in_deck_order`'s breakdown-list ordering),
    only its stated reason for existing was stale.
  - **Found by round-3 scope-auditor review: the eligibility gate's own documentation
    named the retired mechanism, in four places round 1 explicitly (and, in hindsight,
    wrongly) judged non-blocking.** `docs/data_contract.md`, `dbt_analytics/models/
    _docs.md`, `dbt_analytics/models/5_marts/_marts.yml`, and `dbt_analytics/models/
    4_intermediate/_intermediate.yml` all described `is_card_eligible`'s current,
    still-active downstream effect as "excluded from discovery queue" or "drives
    discovery queue inclusion." A round-1 reviewer had read the same `data_contract.md`
    line as a generic, non-live concept and passed it; a round-3 reviewer, independently,
    read it as a live description of an in-use column naming a deleted mechanism, and
    failed it. The round-3 reading is the one acted on here: all four corrected to say
    "discover pool" instead of "discovery queue." Pulls in `analytics-engineer-reviewer`
    (the two `dbt_analytics/*.yml` files) and `equity-analyst-reviewer`
    (`docs/data_contract.md`) as required reviewers from this round on, since routing is
    computed from staged paths.
  - **"Not now" in the list model: log only, no visible list effect. Decided 2026-08-29.**
    Today it never removes a ticker from the pool, only deprioritizes it in the walk's own
    ordering (`skip_counts`) so it resurfaces later; `filter_pool()` only ever excludes
    *saved* tickers. Once the walk's stateful ordering is gone, "deprioritize" has nothing left
    to act on. Not Now still records a `"skip"` interaction (preserving whatever downstream
    value that log has), but the list looks identical after tapping it; the user free-scrolls
    to whatever they want next instead of being pushed to a "next" item. Not `filter_pool`'s
    concern: no new exclusion set, `_saved_keys()` stays the only one.
  - **Save/Not now stay on the focus card, not added to the list rows.** Adding a second
    per-row action (a save icon, say) would need a second tap target per row, which
    `docs/ui/saved_list.md`'s own anti-pattern list already rejects for Saved ("row itself is
    the control"). Matching that precedent rather than inventing a new list-row interaction.
  - **Stats line copy ("N left") needs a small wording pass** since "left" reads as
    walk-remaining language once there's no walk. Proposing "{N} match your filters · {N}
    saved" in place of "{N} left · {N} saved"; flagging as a small, correctable-later wording
    choice, not blocking implementation on it.

done_when:
  - `frontend/card_copy.py` gains a pure function computing the row's lead metric from a card's
    `company_type`: `ebit_margin_pct` for operating, `statement_roe_pct` for financial,
    `cash_runway_months` for pre_revenue (split by type, see decisions_reserved above),
    returning `None` (not a placeholder) when the underlying value is missing so the row
    degrades to verdict-only rather than showing a blank or invented number.
  - `frontend/row_ui.py` gains a new row-builder for the rich variant (verdict emoji + lead
    metric label/value), alongside the existing `build_row_html`, which stays exactly as-is so
    Saved and Search are untouched.
  - `frontend/app.py`'s Discover tab renders: Filters (unchanged) -> a scrollable list of the
    filtered, alphabetically-ordered pool using the new rich row -> tap opens the existing
    focus card (`render_stock_card`, unchanged) with a "Back to list" affordance mirroring
    `saved_focus_key`'s exact pattern, under its own session-state key.
  - Save and the resolved Not-now behavior (per the decision above) are wired on the focus
    card, matching where they already live today.
  - `queue`, `queue_index`, `market_index`, `sector_shown`, `discovery_queue.py`, and the "Next
    company" button are removed. `pytest` catches any remaining reference (a leftover import or
    call would fail loudly, not silently).
  - `docs/north_star.md`'s "Discover" table is corrected: the "Browse list: Removed" rule is
    replaced with the shipped behavior. `docs/ui/design_system.md`'s "who uses rows" line is
    corrected (Discover now does). A new `docs/ui/discover_list.md` documents the list+focus
    spec (row content, tap behavior, 480px checklist), matching `saved_list.md`'s shape; note
    where and why it differs (richer row: verdict + metric, vs. Saved's plain title+subtitle).
  - New tests: the lead-metric function (three cases: operating, financial, pre_revenue, plus a
    missing-value case returning `None`); the new rich row builder (renders verdict + metric,
    degrades cleanly when metric is `None`); whatever test coverage the resolved Not-now
    behavior needs once decided.
  - `pytest` green. Full UX PR gate: north_star check, component specs, 480px live browser
    check against the running app with real Supabase data (not assumed from the CSS): no
    horizontal scroll on the 924-row alphabetical list; verdict + lead metric render per row,
    correctly type-branched (confirmed both branches live: Operating margin on an operating
    row, Cash runway on a pre_revenue row); tap opens the focus card with the market-only meta
    line (no position); Save decrements the list count, increments saved, and the ticker
    appears in Saved; Not now returns to the list with the count and content unchanged.
  - No em dash or en dash on any added line.

impact_map:
  - `frontend/discovery_queue.py` is deleted; its sole caller (`frontend/app.py`) is rewritten.
  - Every Discover card is affected: the interaction model changes for all ~924 eligible cards,
    not just the twelve cross-market duplicates the venue-line fix addressed.
  - `docs/north_star.md`, `docs/ui/design_system.md` both need correction since they currently
    describe the opposite of what this ships.
  - No dbt, ingestion, or data model change. Display/interaction only.

amendments: (none)
