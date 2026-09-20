# Task contract
> DISPOSABLE. **Owns:** THIS task's objective, `scope_paths`, reserved decisions and
> `done_when`.
> **Never:** anything that outlives the task. Overwritten by the next task.

objective: Owner review of the merged contrast-tier work (MR !198) surfaced a second round
  of UX problems on the same header/nav surface, worked through live:

  1. **About redesign.** Owner: old "Right now"/"Tip" text was wasted space, `Clear saved`
     sat in a menu shared with Discover though it only acts on Saved ("disconnected from
     saved"), trigger was "crippled... 3 dots and an arrow." Fix: merged "Right now"/"Tip"
     and the separate "About the data" expander into one flat `About` popover body (no
     nested expander, one click not two); `Clear saved` moved to the Saved tab, next to the
     count it acts on; `⋯` renamed to a text-labeled `About` button beside Discover/Saved.

  2. **"Not now" removed entirely** (card button + overflow review list). Verified first:
     its `skip` interaction was never read by `filter_pool` (only `save` excludes a ticker),
     so it did exactly what `← Back to list` already does. Removed the button, the panel,
     `skip`/`unskip`, and `skipped_keys_with_order`.

  3. **Saved per-row removal.** Owner: "Clear saved is fine but it clears all, why not
     remove individual stocks." `row_ui.render_removable_row_list`: full-row tap opens the
     card, a separate `Remove` button in its own column removes without opening it.

  4. **Nav row**, iterated live (owner: "you always move it in the direction of near",
     "not good spacing", "looks shit on a small screen") to: three equal-width siblings,
     one uniform gap, `About` distinguished only by dimmer label + kept chevron -- not
     width/gap, both tried and rejected at multiple widths incl. 320px. Found a real bug:
     the old nested Discover/Saved wrapper carried a Streamlit default ~7.2px margin-bottom
     `About` didn't have; fixed by flattening to one flex level, not compensating margins.

  5. **Copy, each round explicitly owner-approved this round.** About's intro: cut
     "real" (owner: "what are 'real' numbers???" -- empty word, does no work); cut "No
     ratings, no buy or sell calls" (owner: "no birds, no dogs and no clouds" -- an
     unbounded negative claim, not informative); rewrote the metric-list `--` break as a
     colon (owner: "shitty signs of AI text"). Final, owner-approved: "Stock Explorer shows
     a company's numbers: margins, debt, growth, cash, returns, measured against its
     industry. Each card also carries a short AI-written summary, generated from those same
     numbers, so every line in it can be checked against the figures right above it." Stats
     line: dropped the query-specific "N for 'query'" form entirely (owner: "N companies" --
     same label whether searching or browsing) and added the singular ("1 company", owner:
     "if it is only one then it should be 1 company"); `_render_discover_scope_stats` no
     longer takes a `query` param. Data-source line: the app's `·` chip separator (e.g.
     `ticker · sector`) had leaked into a plain sentence (owner objected) -- rewritten as two
     plain sentences. Re-swept touched `frontend/` strings for the same leak; none found.

  6. **Popover alignment: attempted, reverted, left as a known limitation.** A real ~2.4px
     edge gap between the `About`/`Filters` panels and the page's row/card edges. Fix 1
     (constrain `left`/`right`/`width`, clear `transform`) broke both popovers outright --
     reverted. Fix 2 (a `margin-left` nudge) helped `About` but over-corrected `Filters` --
     different trigger positions, doesn't generalize. Reverted. Owner: move on -- left as
     Streamlit's own floating-popover limitation, not fixed.

  7. **Rounds 2-9 review: each found real incomplete-removal or stale-doc gaps**, fixed
     before the next round, same pattern throughout -- code or CSS left behind after a
     function/feature was deleted, or a doc describing the old shape (most recently:
     `discover_header.md`'s sourcing-line example and `north_star.md`'s copy-vocabulary list
     both still showed a pre-fix/removed form after the surrounding paragraph in the same
     file had already been corrected). Full list per round is in the commit history and MR
     description, not restated here. Copy findings needed owner input; resolved live (point 5).

scope_paths:
  - frontend/app.py
  - frontend/explore_filters.py
  - frontend/overflow_menu.py
  - frontend/row_ui.py
  - frontend/styles.py
  - frontend/browser_storage.py
  - frontend/markets.py
  - docs/ui/discover_header.md
  - docs/ui/discover_list.md
  - docs/ui/design_system.md
  - docs/ui/saved_list.md
  - docs/north_star.md
  - docs/ux_principles_finanz_lern_apps.md
  - docs/context_budget.yml
  - CLAUDE.md
  - README.md
  - tests/frontend/test_app.py
  - tests/frontend/test_app_e2e.py
  - tests/frontend/test_explore_filters.py
  - tests/frontend/test_overflow_menu.py
  - tests/frontend/test_browser_storage.py
  - tests/frontend/test_styles.py
  - tests/ingestion/test_market_onboarding.py
  - docs/streamlit_deploy.md
  - docs/supabase_setup.md
  - .claude/task/contract.md
  - .claude/task/review.md

decisions_reserved: The Not-now removal ("remove the not now button"), per-row Saved
  removal (owner's own request), final nav spacing (owner rejected two alternatives before
  "looks ok now"), and both copy strings (About intro, stats line -- see point 5, each word
  individually approved or cut live this round after scope-auditor round 5 flagged neither
  had a recorded final sign-off) were escalated and answered live. No decision left open.
  Popover-alignment gap is an accepted limitation, not a decision -- owner said move on.

done_when:
  - `overflow_menu.py` exposes `render_about_panel` (not `render_overflow_menu`); no
    `Not now` review panel, no `right_now_line`/`quick_tip_line`/`discover_scope_line`.
  - `app.py`: sticky actions show only `Save`; nav row renders three equal-width siblings
    (`Discover`, `Saved`, `About`) with no per-child width/margin override beyond the row's
    own uniform gap; `_render_saved_scope_stats` renders `{N} saved` plus its own
    `Clear saved`/confirm flow (`saved_clear`, `saved_clear_cancel`, `saved_clear_confirm`
    keys); no `not_now_*` session-state keys or handlers remain.
  - `row_ui.render_removable_row_list` exists and is used by the Saved tab; each row's
    `Remove` button (`{key_prefix}_remove_{row_key}`) removes without opening the card.
  - `explore_filters.skipped_keys_with_order` removed; no `skip`/`unskip` interaction is
    written anywhere; `browser_storage.py` has no `SKIP_COOKIE_PREFIX`, `skipped_state`, or
    skip-cookie read/write path left -- `ensure_interactions_loaded`/`append_interaction`/
    `clear_interactions`/`flush_storage_writes` all handle Saved only; `markets.py` has no
    `discover_pool_summary` (zero remaining callers after the About rewrite).
  - `_render_discover_scope_stats` renders `{N} companies` (`{N} company` singular at 1),
    same form whether or not a search query is active; takes no `query` param.
  - `overflow_menu.MENU_METRICS_LINE` ("Fundamentals per company, no substitutes") still
    renders in the About panel -- only the per-market breakdown was owner-flagged for
    removal, not this line.
  - No file in the repo still describes "Not now", "skip"/"unskip" as a live mechanic, or a
    `⋯`/icon-only/"About the data" overflow trigger outside historical explanation of why it
    was removed -- verified by grepping the whole repo, not just `scope_paths`
    (`design_system.md`, `saved_list.md`, `north_star.md`, `ux_principles_...md`, `CLAUDE.md`,
    `README.md` all updated); `docs/ui/saved_list.md` documents the per-row `Remove` control
    it previously didn't mention at all.
  - `row_ui.render_row_list` removed (zero callers); no dead `.ss-menu-*` CSS remains in
    `styles.py`.
  - `pytest tests/` passes in full (828 tests).
  - `check_no_em_dash.py`, `check_context_budget.py` pass. Two budget raises, both reasoned:
    `discover_header.md` 9000 -> 9300 (new About-panel section replacing the old overflow-menu
    one); this file, `contract.md`, 8000 -> 9500 (nine review rounds each added a real,
    reviewer-caught finding to the objective/done_when; trimming twice already, further
    cuts would start losing the record those rounds exist to keep).
  - Live-verified against the real Streamlit dev server at 375px and 320px widths: nav row,
    About panel content and one-click open, Not-now fully gone from the card and the menu,
    Saved per-row remove, Clear-saved confirm flow, updated stats-line copy.

impact_map: All seven `frontend/` app files (`overflow_menu.py`, `app.py`, `row_ui.py`,
  `explore_filters.py`, `browser_storage.py`, `markets.py`, `styles.py`) plus matching tests;
  doc sweeps across `docs/ui/*`, `north_star.md`, `ux_principles_...md`, `CLAUDE.md`,
  `README.md`, `streamlit_deploy.md`, `supabase_setup.md` -- see objective points 1-7 for
  what changed where and why. Two budget lines raised, both reasoned above. No new
  dependency, service, or CI change.
