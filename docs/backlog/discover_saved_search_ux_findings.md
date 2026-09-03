# Discover / Saved / Search UX simulation findings

**Status:** Open. Found 2026-09-03 during a full click-through simulation of Discover, Saved,
and Search, requested by the owner 2026-08-31 ("a full user-flow simulation... to find further
UX inconsistencies beyond the ones already found and fixed"). Four bugs confirmed by hand in a
running local instance (not just read from code), plus one structural risk that could not be
fully reproduced at the volume tested. No fixes chosen or shipped yet.

## Summary

The simulation covered all three tabs against the live Supabase-backed dev server: Search's
query/result/focus mechanics, Saved at volume (17 saves) including the destructive "Clear
saved" action, and Discover's market/sector filter across tab navigation. Four real,
reproducible bugs were found; one code-visible structural risk (Saved has no pagination) could
not be confirmed as a *felt* problem at the scale tested. This doc records what was confirmed
and how, and leaves the fix direction for the owner.

## Context

**Confirmed by direct interaction in the running app** (clicking through
`http://localhost:8501`, not assumed from reading code alone):

- **Search silently resurrects a stale card.** Search "Apple" → open it (full Company Snapshot
  renders below the result list) → change the query to "Microsoft" (Apple's card correctly
  disappears) → change the query to "App" (which matches Apple Inc., Applied Materials,
  AppLovin, and NetApp) → **Apple's full snapshot reappears on its own, with no click.**
  Confirmed mechanism, not just symptom: `frontend/app.py:479-483` reads
  `st.session_state["search_selected"]` (set once by `_select_search_row`,
  `frontend/app.py:442-443`, on click) and renders whichever card in the **current** `matches`
  list has that key -- with no check that the key was actually selected in response to the
  *current* query. `search_selected` is never cleared when `query` changes. Any query that
  happens to re-match a previously-opened card's ticker/name as a substring will silently
  reopen it.
- **The Search box's typed text is lost on tab switch.** Type a query, tap Discover, tap back
  to Search -- the box is empty again (placeholder text showing), not the query. Confirmed
  mechanism: `st.text_input("Search", placeholder=..., label_visibility="collapsed")`
  (`frontend/app.py:447-451`) has no explicit `key=`. `_render_search_tab` only runs while the
  Search tab is active (`frontend/app.py:519`), so the widget isn't instantiated on the runs
  where the user is on Discover or Saved -- an unkeyed widget's value does not survive that.
- **Discover's Market/Sector filter also resets to "All markets · All sectors" on tab
  switch** -- not part of the original test plan, found live. Reproduced twice, cleanly: set
  Market to "Nikkei 225" (110 matches), tap Saved, tap back to Discover → filter reads "All
  markets · All sectors" again (1042 matches). Repeated with "ASX 200" (184 matches) → same
  reset. **Mechanism not yet confirmed** -- and the obvious explanation (the Search box's
  unkeyed-widget pattern above) does **not** apply here: both selectboxes have explicit
  `key="explore_market"` / `key="explore_sector"` (`frontend/app.py:277-297`), tied to
  `st.session_state` defaults that are only initialized once per session
  (`frontend/app.py:59-70`) and a one-time version-migration guard
  (`frontend/app.py:72-75`) that reads a plain integer constant (`EXPLORE_DEFAULTS_VERSION = 5`,
  not recomputed at runtime) -- ruled out as the cause by reading it directly. The selectboxes
  themselves are only rendered while on Discover and unfocused
  (`_render_explore_filters`, called at `frontend/app.py:501-502`), so whatever is resetting
  the stored value happens somewhere in that gap. **Needs a live, instrumented pass** (print
  the actual `st.session_state["explore_market"]` value at the top of `_init_state()` across a
  tab-switch round trip, the same kind of direct measurement `docs/backlog/discover_list_performance.md`
  used for the click-latency investigation) before a fix is chosen -- the mechanism matters
  because a fix aimed at the wrong cause (e.g. copying the Search box's future `key=` fix) may
  not actually work here.
- **"Clear saved" is one click, no confirmation, no undo, and also silently discards skip
  history.** Saved 17 companies, opened the overflow menu (⋯), clicked "Clear saved" once --
  all 17 gone instantly, session state correctly shows the empty-state message
  ("Nothing saved yet..."). No "are you sure?" step anywhere. Confirmed in code too:
  `frontend/overflow_menu.py:147-150` wires the button straight to `clear_interactions()`
  (`frontend/browser_storage.py:136-140`), which wipes the entire interactions list -- saves
  *and* skips -- in one call, no staged/two-step confirmation pattern anywhere in this app today.

**Checked and confirmed NOT a bug** (predicted risks from code-reading that didn't hold up
under actual testing):

- Saving a card in Discover shows up in Saved immediately -- no lag, no extra refresh needed.
- Discover's market/sector filter does not leak into Search or Saved: with Discover filtered to
  a specific market, Search still finds and opens companies from every market.
- Saved's row-click responsiveness felt normal at 17 rows.
- A hard browser refresh on Saved (with 1 existing save) landed correctly on Discover (no tab
  persistence across a full reload, which appears intentional -- there's no evidence anywhere in
  the code of an attempt to persist the active tab) with the correct saved count and pool size;
  no empty-state flash was caught in this pass, though the timing window for that predicted
  flicker is narrow enough that this is inconclusive, not a clean "no bug" -- see open questions.

**A structural risk, not confirmed as a felt problem at the volume tested:** `_render_saved_tab`
(`frontend/app.py`) calls `row_ui.render_row_list()` on the full, unsliced saved-cards list --
no pagination, unlike Discover's `DISCOVER_PAGE_SIZE = 30` (added in
`docs/backlog/discover_list_performance.md`'s fix after ~930 unconditional rows measured
~2.4s of click-registration lag). 17 saved rows showed no perceptible lag. This doc does not
claim the risk is real at today's typical usage -- only that the same structural gap Discover
had before MR !70 exists in Saved today, unquantified, and would need testing at a much higher
save count (tens to hundreds) to actually measure, which wasn't practical to do by hand in this
pass.

## Open questions (owner decisions, not answered here)

- **Fix direction for the two confirmed navigation-state bugs (Search box text, Discover
  filter).** Once the Discover-filter mechanism is actually confirmed (see above), is the fix
  "give both widgets an explicit `key=` backed by persistent session_state" (matching how the
  filter selectboxes are *already* keyed, so this alone may not be sufficient), or something
  else entirely depending on what the instrumented pass finds?
- **Fix direction for the Search stale-selection bug.** The simplest fix is clearing
  `search_selected` whenever `query` changes (e.g. resetting it inside `_render_search_tab` the
  moment the current query no longer produces a match containing the previously-selected key,
  or simply on every query change). Worth confirming this doesn't conflict with any intended
  "keep the open card visible while refining a search" behavior -- nothing in
  `docs/north_star.md`'s two-line Search description suggests that's intended, but it's the
  kind of assumption worth a quick explicit check rather than silently deciding.
- **Is "Clear saved" acceptable as-is, or does it need a confirmation step?** This is a product
  risk call, not an engineering one -- how much does accidentally losing a curated saved list
  matter for this app's actual usage pattern? A single-step "Are you sure?" dialog (Streamlit
  has no native modal-confirm primitive; would need `st.session_state`-driven two-click pattern,
  e.g. "Clear saved" → "Confirm clear" for a few seconds, or a checkbox-gated button) is a small,
  contained UI change if the owner wants one.
- **Does Saved need pagination now, or wait for evidence of real-world scale?** Unlike
  Discover's ~930-row catalogue (guaranteed large for every user), Saved's size is entirely
  user-curated -- most users may never approach a count where this matters. Worth deciding
  whether to build proactively (reusing the exact `DISCOVER_PAGE_SIZE` pattern, low engineering
  cost since the mechanism already exists and is proven) or wait and see if it's ever reported
  as slow, the same way Discover's issue was originally surfaced by a real complaint.

## Candidate directions (not decisions, for owner discussion)

1. **Navigation-state bugs (Search box, Discover filter, Search stale-selection):** likely one
   contained engineering pass once the Discover-filter mechanism is confirmed, touching
   `frontend/app.py` only. No new dependency or mechanism needed for any of the three.
2. **"Clear saved" confirmation:** smallest version is a two-click confirm (button label
   changes to "Confirm clear" for ~5 seconds or until another action, no new component needed).
   A modal-style confirm would be more standard but is a heavier UI pattern this app doesn't use
   anywhere else today.
3. **Saved pagination:** reuse `DISCOVER_PAGE_SIZE`'s exact mechanism
   (`frontend/app.py`/`frontend/row_ui.py`), likely a small, low-risk change given it's already
   proven in production for Discover -- mostly a question of whether it's worth doing now.

## Related

- `frontend/app.py` (`_render_search_tab`, `_select_search_row`, `_render_explore_filters`,
  `_render_saved_tab`, `_init_state`), `frontend/overflow_menu.py`, `frontend/browser_storage.py`.
- `docs/backlog/discover_list_performance.md` -- the precedent for both the pagination fix
  candidate direction and the "confirm by direct measurement, don't guess the mechanism" method
  this doc tried to follow for the Discover-filter bug.
- `docs/ui/saved_list.md`, `docs/ui/discover_list.md`, `docs/ui/discover_header.md` -- no
  `docs/ui/search*.md` exists; Search's intended behavior beyond `docs/north_star.md`'s two-line
  description is undocumented, which is itself worth the owner knowing while deciding these
  fixes.
