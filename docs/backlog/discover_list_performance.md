# Discover list performance

**Status:** Backlog. Found 2026-08-30 while investigating a separate report ("it literally
takes minutes to open a card by clicking on an entry in the list... too slow or buggy"), then
flagged in `.claude/active_work.md` as a real, reproducible architectural problem not yet
scoped. Scoped as its own item 2026-08-31.

## Summary

Opening a Discover card by tapping a list row is measurably slow. This doc separates what's
been confirmed by direct measurement from what's still a well-reasoned but unconfirmed
hypothesis, and lays out the product/engineering questions that block writing a build contract.
It does not choose a fix.

## Context

**Confirmed by direct measurement in the running app** (via `getBoundingClientRect()` and
polling Streamlit's own "Running..." indicator, not assumed from the code):

- With the full, unfiltered Discover list showing (~923-924 card-eligible companies), the page
  has 931 individual `st.button` elements and ~20,600 total DOM nodes. `frontend/row_ui.py`'s
  `_render_tappable_rows` renders one `st.container()` holding one `st.markdown()` (the row's
  rich HTML) plus one `st.button()` (the invisible tap target) **per row, unconditionally,
  every row, every render**. There is no pagination, windowing, or virtualization: all ~923
  rows are mounted at once regardless of how many are actually visible in the viewport.
- Clicking a row in that full-size list takes **~2.4 seconds before Streamlit even starts
  processing the click** (before any Python code runs). This is front-end cost: the browser
  has to register the interaction among ~930 simultaneously-tracked widgets.
- Narrowing the list to a 39-company market (DAX; 47 buttons, ~1,168 DOM nodes) drops that
  same pre-processing delay to **~0.6-0.7 seconds**. The correlation between widget/DOM count
  and click-registration delay is direct and reproducible, not a one-off measurement.
- Ruled out as causes of a *separate* slowness (see below), by reading the code, not by
  guessing: Supabase data is bulk-fetched once per session
  (`supabase_cards.fetch_eligible_cards_with_assessments`, paginated, cached in
  `st.session_state["all_cards"]`), not per-card, so opening a specific company never triggers
  its own network fetch. Sector benchmarks are precomputed columns on each card
  (`sector_median_*`), not computed live in the frontend. Pool filtering
  (`explore_filters.filter_pool`) is a single linear pass over ~923 items using set lookups, no
  nested loops; the subsequent sort (`app._discover_pool`'s own `pool.sort(...)`) is one
  `list.sort()` call over the same small N, not a performance concern either.

**A well-reasoned but not yet directly confirmed hypothesis**, for a second, separately-observed
symptom: once a rerun does start, its actual duration is inconsistent (measured anywhere from
~100ms to several seconds across different clicks, not obviously tied to which company or
whether it had been opened before in the same session). Reading `_render_tappable_rows`
(`frontend/row_ui.py`) closely: the per-row click handler calls `on_select(item)` and then
**`st.rerun()` unconditionally**, inside the `for item in items` loop. `st.button` returning
`True` already means Streamlit is mid-way through a script run triggered by that exact click;
calling `st.rerun()` immediately aborts that run and starts a fresh one from the top. Because
the row loop renders rows in order and the abort happens exactly where the clicked row's
button is, **the aborted run's own cost before it gets interrupted scales with how far down the
list the clicked row sits**: clicking near the top aborts cheaply, clicking near the bottom
means Streamlit has already built ~900 rows' worth of markdown and buttons before the abort
fires, and then a second, full, top-to-bottom run happens anyway. This would explain the
inconsistency (different rows sit at different positions) without needing any per-company
explanation. It has not been confirmed with a controlled, position-varying test in this pass
(one attempted live retest was inconclusive due to environment noise); a profiling pass (real
Python profiling, e.g. `cProfile`, or Streamlit's own instrumentation) should check this
directly before anyone assumes it's the answer.

**Why the explicit `st.rerun()` is there at all, not obviously a bug to just delete:** without
it, setting `discover_focus_key` mid-loop would take effect only on Streamlit's own next natural
rerun (the following interaction), not immediately: the list would keep rendering for the rest
of the current script run and the reader would need to interact again to see the card they just
tapped. The `st.rerun()` buys immediate feedback at the cost described above. Removing it without
another way to short-circuit the current run's remaining work would trade one problem for
another.

## Open questions (owner decisions, not answered here)

- **Is a smaller live-widget count per render (pagination or equivalent) the direction, and if
  so what shape?** Candidate directions below aren't ranked; picking one, or none, is a real
  product/UX decision (page size and pagination UI are user-facing, composition/ordering
  concerns under this repo's working agreement §6), not something to default silently.
- **Does the `st.rerun()`-inside-the-loop hypothesis need its own engineering spike before any
  fix is chosen, or can a widget-count fix (e.g. pagination) be built without first confirming
  it?** A widget-count reduction would independently shrink *both* symptoms (less to render
  before an abort, and less to register on click), so it may not require root-causing the
  second issue first, but that's worth an explicit call, not an assumption.
- **Page size, if pagination is the direction.** Smaller pages (e.g. 30) minimize widget count
  most aggressively but mean more clicks to browse the full list; larger pages (e.g. 100) leave
  more of the original problem in place. No data yet on where the felt slowness actually
  crosses a threshold.
- **Does this reopen or interact with the "Discover's first-time default scope" decision**
  (`docs/backlog/discover_first_time_default.md`, decided: no change, full list stays for
  everyone)? That decision was about not curating a smaller subset for beginners. A pagination
  fix here is a different justification entirely (a technical widget-count ceiling, not a
  content decision) and doesn't reduce what's browsable, but the two could visually look
  similar (a shorter first screen), so the distinction should stay explicit wherever this is
  explained to the owner or documented, not blurred.
- **Scope: Discover only, or does Saved need the same look?** Saved's list uses the plain
  `build_row_html`/`render_row_list` (not the rich verdict+metric row), and today's saved lists
  are user-curated and typically far smaller than 923 companies. Likely out of scope for now,
  but worth naming explicitly rather than silently assuming, since Saved could theoretically
  grow large for a heavy user.
- **New mechanism.** Simple pagination (slicing an already-in-memory list by a session-state
  page index) needs no new dependency. A `st.dataframe`-based rewrite is Streamlit's more
  idiomatic pattern for large selectable lists, but a much bigger change: the row's visual
  richness (verdict dot, lead metric, subtitle) would need to be re-expressed within a
  dataframe's more constrained cell rendering. Real virtualization (a custom component,
  since Streamlit has no built-in windowing for a loop of custom HTML rows) would each be a new
  mechanism requiring its own sign-off, not something to reach for by default.

## Candidate directions (not decisions, for owner discussion)

1. **Pagination.** Render a fixed page (e.g. 30-50 rows) at a time with page/"load more"
   controls. Lowest engineering risk: reuses the existing row HTML and tap mechanism unchanged,
   no new dependency. Reduces the live widget count on any single render, which should help
   both the confirmed click-registration delay and, if the `st.rerun()` hypothesis holds, the
   per-click render cost too. Page size and pagination-UI shape are still open (see above).
2. **"Load more" / incremental append.** Similar mechanics and cost profile to pagination, but
   keeps a single continuous list (no page boundaries) that grows as the reader asks for more.
   Feels more like scrolling, at the cost of eventually reaccumulating a large widget count if
   someone keeps clicking "load more" through the whole list.
3. **Rebuild the list on `st.dataframe` with row-selection.** Streamlit's more idiomatic
   mechanism for a large, selectable list: one widget for the whole table instead of hundreds.
   Would very likely fix both symptoms outright, but at real cost: `st.dataframe`'s cell
   rendering is far more constrained than custom HTML, so the row's current visual design
   (verdict dot + lead metric + two-line title/subtitle, all in one row) would need to be
   redesigned to fit, not just ported. A materially bigger change than the other options.
4. **Virtualization (render only rows near the viewport).** The standard web-engineering fix
   for huge lists, but Streamlit has no native support for windowing a loop of custom HTML rows;
   building it would mean a custom React component, a genuinely new mechanism and a much larger
   engineering lift than the other three options.

## Related

- `frontend/row_ui.py` (`_render_tappable_rows`, `render_rich_row_list`, `build_rich_row_html`),
  `frontend/app.py` (`_render_discover_tab`, `_discover_pool`).
- `docs/backlog/discover_first_time_default.md`: the decision this doc's fix must not be
  confused with or silently reopen.
- The verdict-dot alignment fix (`feat/discover-row-verdict-dot`, merged 2026-08-31), found and
  fixed in the same investigation thread as this performance issue, but a fully separate,
  already-resolved concern.
