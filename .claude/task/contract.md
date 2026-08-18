# Task contract

objective: **Slice 6a — Design system foundation.** First of three phases of the UI redesign
  (Slice 6). The owner wants one consistent design language across the whole app, not just a
  redesigned card. An audit found real inconsistency outside the card: Saved-list rows,
  Search results, and nav/overflow buttons each hand-pick their own corner radius and
  spacing (three different radius values, no shared scale), and Search results have no
  custom styling at all — plain default Streamlit buttons next to everything else's custom
  HTML/CSS. This slice builds the token/component foundation, fixes Search's missing
  styling, and prunes dead CSS. **6b** (Landing/Overflow unification) and **6c** (rendering
  the new card content — health verdict, AI read, per-type metrics) are separate, later
  slices; this one deliberately touches neither. Approved plan:
  ~/.claude/plans/pure-juggling-frost.md.

scope_paths:
  - frontend/styles.py                              # + token block, row/button primitives, - dead CSS
  - frontend/row_ui.py                               # NEW: shared row primitive (build_row_html/render_row_list)
  - frontend/app.py                                  # Saved-list + Search wired onto row_ui; new icon-btn marker
  - docs/ui/design_system.md                         # NEW: token/primitive spec, matches existing docs/ui/ template
  - docs/ui/saved_list.md                            # class-name references updated (.ss-saved-list-* -> .ss-row*)
  - docs/north_star.md                               # + row in the UI component specs table
  - docs/working_agreement.md                        # UX gate's component-specs bullet: + "design tokens"
  - tests/frontend/                                  # if row_ui.py needs unit coverage (build_row_html escaping etc.)
  - .claude/task/contract.md

decisions_reserved (owner-approved this session; §6 — plan-approved):
  - **Row corner radius matches the card** (0.75rem), not the smaller control radius — the
    one deliberate visual change in this slice; Saved-list rows go from 0.4rem to 0.75rem.
  - **Rows get a filled background** (`var(--ss-surface)`, matching the card), not
    outline-only as today.
  - **Search keeps its 20-result cap** — no change, even though rows are now visually taller.
  - **Search's interaction model stays as-is** (results list + opened card both showing) —
    NOT adopting Saved's list-then-focus-with-back-button flow in this slice. That's a
    behavior change, not a styling change, and is explicitly deferred to a later decision.
  - **Button radius base rule applies app-wide**, but primary/secondary color/background
    skin stays scoped to only the fixed action bar — Landing/Overflow button reskinning is
    6b's job, not this slice's.

technical_definition:
  - **New tokens in `:root`** (styles.py ~line 14-28, additive only): spacing
    `--ss-space-1..4` (0.35/0.55/0.75/0.85rem, each already an existing hand-picked value
    elsewhere in the file — adopting them is a no-op, not a redesign); radius
    `--ss-radius-control` (0.5rem, already hand-picked twice) and `--ss-radius-surface`
    (0.75rem = card's existing 12px, tokenized); type `--ss-row-title` (0.85rem, a new rung
    between `--ss-title` and `--ss-label`, reserved for list-row text only).
  - **Retokenize first, pure substitution, zero visual diff:** `.ss-card` radius (12px ->
    `var(--ss-radius-surface)`), overflow trigger + nav icon button radius (both 0.5rem ->
    `var(--ss-radius-control)`) — verify no visual change before touching anything else.
  - **`frontend/row_ui.py` (new):** mirrors `card_ui.py`'s pure-function + render-function
    split. `build_row_html(title, subtitle) -> str` emits `.ss-row` markup (renamed from
    `.ss-saved-list-entry`); `render_row_list(items, *, key_prefix, on_select, title_fn,
    subtitle_fn, row_key_fn)` emits the `.ss-row-group` marker + per-item row HTML + the existing
    invisible-overlay-button tap mechanism (kept structurally identical, just re-keyed from
    `.ss-saved-list-items`/`.ss-saved-list-entry` to `.ss-row-group`/`.ss-row`).
  - **Two consumers migrated onto `row_ui`:** `_render_saved_tab` (app.py:395-414, replaces
    inline loop) and `_render_search_tab` (app.py:459-464, replaces bare `st.button(...)`
    loop — reuses `card_copy.saved_row_subtitle()` unchanged for the subtitle).
  - **Button consolidation:** one new global `[data-testid="stButton"] button { border-radius:
    var(--ss-radius-control); }` rule; delete dead `.ss-menu-popover button` (styles.py:
    710-724, verified zero references anywhere); replace the `:last-child`-positional nav
    icon-button rule with one keyed to a new explicit marker div (before the overflow
    `st.popover` call, app.py:237) — removes a fragile positional coupling, same marker
    idiom `.ss-action-shell`/`.ss-row-group` already use elsewhere in this file.
  - **Dead CSS removed** (confirmed zero references via grep): `.ss-browse-heading/-name/
    -ticker/-sub` (styles.py:609-628), `.ss-saved-list-row` + `.ss-saved-row` (styles.py:
    535-543 — NOT `.ss-saved-list-entry` at 504, which is live), `.block-container.ss-no-actions`
    (styles.py:59-61), `.ss-saved-ticker` (styles.py:600-602, superseded by `.ss-row-sub`).
  - **New doc `docs/ui/design_system.md`:** same template as every existing `docs/ui/*.md`
    (Scope/Authority/Implementation, wireframe, rules table, anti-patterns, 480px smoke,
    Related). Explicitly notes the segmented control (Discover/Saved/Search nav pills) is
    excluded from the button-variant system — native Streamlit widget, not our markup.

done_when:
  - Token additions + pure radius retokenization produce **zero visual diff** (verified
    locally, before/after).
  - Saved tab list view: rounder, filled rows; focus view and Discover unaffected (they use
    the card, not the row primitive).
  - Search tab: results render as real styled rows instead of plain buttons; opening a
    result still shows the card beneath, unchanged.
  - Overflow trigger and nav icon button: visually identical before/after.
  - `grep -rn "ss-saved-list-row\|ss-saved-row\b\|ss-browse\|ss-menu-popover\|ss-no-actions\|ss-saved-ticker" frontend/`
    returns nothing outside the deletions themselves — no stale references left.
  - Full 480px mobile smoke across Discover / Saved (list + focus) / Search — matches the UX
    PR gate in `docs/working_agreement.md`. The in-app Browser pane could not composite
    frames or dispatch real input for part of this session; coverage was instead produced via
    an independent headless-Chrome CDP harness (real mouse/keyboard events, not JS-dispatched
    synthetic ones) — see `amendments` for the full account and what was owner-approved.
  - `pytest tests/` still green (pure frontend change; confirms nothing else broke).
  - MR description includes the UX gate's required "one primary job" sentence + an ASCII
    wireframe for Search's new row layout (the one genuinely new layout pattern here).

impact_map:
  - New shared component (`row_ui.py`) removes duplication between Saved and Search: two
    hand-rolled row loops become one. No new dependency, no backend/data/migration change —
    pure frontend styling + one new small module. Dead CSS removed, not just unused —
    reduces future-confusion surface.
  - Required reviewers (per `.claude/review_routing.json`): **scope-auditor** (always) ·
    **cto-reviewer** (`frontend/*`). Neither analytics-engineer nor data-engineer nor
    equity-analyst-reviewer route to this diff (no `*.sql`/`*.csv`/dbt/`supabase/*`/
    `ingestion/*`/`metric_catalogue.csv`/`data_contract.md`/`metric_layer.md` touched).
  - Also subject to the project's **UX PR gate** (`docs/working_agreement.md`) — not part of
    the standard reviewer routing, a separate project-specific requirement for any Streamlit
    layout/copy/interaction change.

amendments:
  - **CSS specificity bug found and fixed during local verification (not anticipated by the
    plan):** `.ss-row-title` and `.ss-row-sub` as bare class selectors on `<p>` tags lost to
    Streamlit's own auto-generated reset, `.st-emotion-cache-<hash> p { font-size: inherit }`
    (specificity `(0,1,1)`, beats a bare class selector's `(0,1,0)`), so both rendered at the
    browser default 16px instead of their intended tokens regardless of source order. This is
    why the existing in-card identity line (`.ss-company`/`.ss-ticker`, styles.py:150-158)
    puts those classes on `<span>`s nested inside a plain `<p>` rather than on the `<p>`
    itself — spans aren't targeted by Streamlit's `p`-element reset, so they never hit this
    trap. `build_row_html()` in the new `row_ui.py` instead puts the class directly on two
    separate `<p>` tags (one per line), which does hit it. **Fix:** scoped both selectors to
    `.ss-row .ss-row-title` / `.ss-row .ss-row-sub` (styles.py, row-primitive section) —
    specificity `(0,2,0)`, a clean win regardless of source order — matching this same file's
    existing `:has(.ss-row-group) .ss-row {...}` scoping idiom rather than introducing
    `!important` (the file's other precedent for winning a Streamlit specificity fight, at
    styles.py:495, reserved for overriding Streamlit's own component styles rather than its
    generic element resets). Verified via computed styles on a live local run: row title
    13.6px (`--ss-row-title: 0.85rem`, was 16px) and row subtitle 11.52px
    (`--ss-caption-size: 0.72rem`, was 16px), radius 12px and filled background unaffected
    (those live on the `.ss-row` div, never targeted by the `p`-element reset).
  - Doc updates (`docs/north_star.md`, `docs/ui/saved_list.md`, `docs/working_agreement.md`)
    completed exactly as scoped — no deviation from the plan's knock-on-updates list.
  - **480px smoke coverage — initially partial and disclosed, then completed and
    owner-approved.** The in-app Browser pane was unable to composite frames or dispatch real
    click/keyboard input for part of this session (a client-side environment issue, not app
    or code state). Worked around it with a second, independent headless-Chrome harness
    (scratch-only scripts, not part of this diff) driven via real CDP mouse/keyboard events —
    trusted input, not JS-dispatched synthetic events. This produced actual rendered
    screenshots of Discover, Saved list (1 row), and Search results (7 rows, including the
    long-name truncation case), covering the full interaction path: landing -> save -> Saved
    tab -> Search tab -> type a query -> Enter -> results. Sent the screenshots to the owner
    in-thread; owner reviewed them and replied "go ahead" to proceed.
  - **scope-auditor FAIL (round 3), fixed:** the round-3 pass correctly rejected "Saved's
    focus view is unchanged code, so it wasn't re-screenshotted" as an unsound blanket
    rationale — this diff's new global rule, `[data-testid="stButton"] button {
    border-radius: var(--ss-radius-control); }` (styles.py), reaches every `st.button`
    app-wide, including the focus view's "Back to list" button (app.py), regardless of
    whether the view's own render code changed. Closed by actually opening the focus view
    (via the same CDP harness, a real click on the saved row) and checking it directly:
    screenshot shows "Back to list" and "Try again" rendering correctly, and
    `getComputedStyle` on the "Back to list" button returns `border-radius: 8px` = exactly
    `var(--ss-radius-control)` (0.5rem @ 16px root) — the global rule applies as intended,
    no breakage. `done_when`'s "Saved (list + focus)" requirement is now actually met, not
    just argued around.
  - **Real bug found via the headless-Chrome screenshots, fixed:** the row hover highlight
    (styles.py, `:hover .ss-row { border-color: var(--ss-accent) }`) was bleeding to **all**
    rows simultaneously instead of just the one under the pointer — confirmed via computed
    styles (`border-color: rgb(201,169,98)` i.e. `--ss-accent` on every row at once, with none
    of their wrapper elements individually matching `:hover`). Root cause: the selector
    `div[data-testid="stVerticalBlock"]:has(.ss-row):hover` matches ANY ancestor
    `stVerticalBlock` that transitively contains a `.ss-row` descendant and is currently
    hovered — Streamlit nests a `stVerticalBlock` per row AND one wrapping the whole row
    list, so hovering anywhere in the list area (not just a specific row) satisfied the outer
    wrapper's `:has(.ss-row):hover`, and the accent border then applied to every `.ss-row`
    beneath it. Traced the actual DOM chain live (`.ss-row` -> `stMarkdownContainer` -> ... ->
    `stElementContainer` -> the correct tight `stVerticalBlock` -> `stLayoutWrapper` -> the
    broad outer `stVerticalBlock`) and fixed by requiring `stElementContainer` as a *direct
    child* of the matched wrapper (`:has(> [data-testid="stElementContainer"] .ss-row)`),
    which only the tight per-row wrapper satisfies. Verified via a real CDP `mouseMoved` event
    onto one specific row: only that row's computed `border-color` changes; the other six stay
    at the default `--ss-border`. The other `:has(.ss-row)` selectors in this same block
    (styles.py, position/margin/button-overlay rules) are unaffected by the same over-matching
    because they set state-independent properties — applying them via either ancestor level
    produces an identical result, so they were left as-is rather than touched speculatively.
  - **cto-reviewer FAIL (round 1), fixed:** `frontend/row_ui.py` shipped with zero test
    coverage — `scope_paths` itself had flagged this as a maybe (`tests/frontend/  # if
    row_ui.py needs unit coverage (build_row_html escaping etc.)`) but the diff dropped it
    without recording why. Added `tests/frontend/test_row_ui.py`, mirroring
    `test_card_ui.py`'s pattern for `card_ui.py`'s analogous pure `build_card_html`: asserts
    title/subtitle appear in the output, HTML-special characters are escaped (`<script>` ->
    `&lt;script&gt;`, `&` -> `&amp;`), and `None` title/subtitle don't raise. `render_row_list`
    itself (the Streamlit-calling half) is not unit-tested, matching this repo's existing
    convention — no test file in `tests/frontend/` mocks `st` to test a render function; only
    the pure HTML-builder half of each pair (`build_card_html`, now `build_row_html`) is
    covered. Also fixed a related drift the same reviewer flagged: `technical_definition`
    above listed `render_row_list`'s signature without `row_key_fn`, which the real function
    requires — corrected to match the actual signature.
  - **scope-auditor FAIL (round 4), fixed — two doc-accuracy bugs:** (1)
    `docs/ui/design_system.md`'s token table claimed `--ss-space-1` was used for "nav row gap,
    metric gloss margin" and `--ss-space-3` for "Section spacing," but neither token was
    actually wired into the CSS anywhere — grep confirmed only `--ss-space-2`/`--ss-space-4`
    were adopted (the new row padding); the two claimed sites still had disconnected hardcoded
    literals, and one claimed example (`.ss-metric-gloss`, styles.py) doesn't even have a
    matching value (`0.1rem`, not `0.35rem`) — a fabricated example, not just an unwired one.
    Fixed by actually wiring the tokens into the two sites that do genuinely match: the
    bottom-nav row's `gap: 0.35rem` (styles.py, `.ss-nav-row-marker + [stHorizontalBlock]`) ->
    `var(--ss-space-1)`, and the Saved-tab news heading's top margin (styles.py,
    `.ss-saved-news-heading`, `margin: 0.75rem 0 0.4rem`) -> `margin: var(--ss-space-3) 0
    0.4rem`. Both are exact-value pure substitutions (0.35rem/0.75rem unchanged), so zero
    visual diff. Corrected the doc's table to name these real, now-true sites instead of the
    fabricated one. (2) `done_when`'s 480px-smoke line named the Browser pane specifically,
    but that tool was unusable for part of this session and a different, disclosed tool (the
    CDP harness) is what actually produced the coverage — reworded `done_when` to describe
    what was actually done instead of asserting a method that wasn't used.
  - **scope-auditor FAIL (round 5), fixed:** round 4's fix checked only the two flagged token
    rows, not the whole table — `--ss-space-4`'s "page gutter" claim (`docs/ui/design_system.md`)
    was the same defect class, still unwired: `frontend/styles.py`'s `.block-container`
    padding used the bare literal `0.85rem` for its horizontal gutter, never `var(--ss-space-4)`.
    Fixed by wiring it in (`padding: 0.4rem var(--ss-space-4) calc(...)`, exact-value
    substitution, zero visual diff). Independently re-verified every remaining row in the
    token table against a fresh grep of `var(--ss-*)` usage in `frontend/styles.py` this time
    (not just the previously-flagged rows): `--ss-space-1` (722), `--ss-space-2`/`--ss-space-4`
    (521, 68), `--ss-space-3` (561), `--ss-radius-control` (57, 760), `--ss-radius-surface`
    (137, 520), `--ss-row-title` (600, and nowhere else) — every remaining "Used by" claim in
    the table now traces to a real `var()` reference at the stated kind of site.
