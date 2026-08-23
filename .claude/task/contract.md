# Task contract

objective: **Replace the card face's text-only "Higher than sector median" indicator with a
  monochrome range mark** showing the company's value positioned between its sector's min
  and max, with the median labeled at its actual position. Raised by the owner testing the
  live app ("so what" — no sense of scale from words alone), researched against bullet-graph
  theory and its documented failure modes, iterated through several rounds of visual
  refinement in conversation before this contract was written. Scoped to the 5 metrics
  already benchmarked today; extending benchmarking to the other 11 metrics (financial,
  pre-revenue, plus 2 more operating) is explicitly deferred — see explicitly_not_in_scope.

scope_paths:
  - dbt_analytics/models/4_intermediate/int_stock__sector_benchmarks.sql  # +min()/max() for the existing 5
  - dbt_analytics/models/4_intermediate/_intermediate.yml                # doc/test the 10 new columns
  - dbt_analytics/models/5_marts/mart_stock_cards.sql                    # select the new columns through
  - dbt_analytics/models/5_marts/_marts.yml                              # doc/test the 10 new columns
  - frontend/card_copy.py            # range-position calc + formatting helper
  - frontend/card_ui.py              # _metric_cell_html: replace _bench_indicator_html with the range mark
  - frontend/styles.py               # new range-mark CSS; existing .ss-bench-indicator stays (still used
                                      # by the separate learn-panel recap list, see explicitly_not_in_scope)
  - tests/frontend/test_card_copy.py # range-position calc: normal, degenerate, out-of-bounds-clamped
  - tests/frontend/test_card_ui.py   # range mark renders; omitted below the 8-peer threshold
  - docs/ui/card_metric_cell.md      # wireframe + visual-hierarchy spec describe the old indicator today
  - docs/north_star.md               # Benchmarking (v1) section didn't distinguish card-face vs recap mechanism
  - docs/data_contract.md            # sector-benchmark Output table + mart_stock_cards column table both
                                      # describe the sector_median_* columns this diff sits alongside — missed
                                      # in the original scope_paths, caught by scope-auditor round 1
  - scripts/export_to_supabase.py    # EXPORT_COLUMNS allowlist — missed in round 1, caught by
                                      # analytics-engineer-reviewer: without this, the mart's new columns
                                      # are silently never sent to Supabase
  - supabase/migrations/012_sector_benchmark_min_max.sql  # new — additive columns on the real
                                      # public.mart_stock_cards table, same pattern as 007/008/009/010
  - tests/tooling/test_export_to_supabase.py  # regression guard: new sector_median_* companion
                                      # columns must be in EXPORT_COLUMNS
  - docs/ux_principles_finanz_lern_apps.md  # stale arrow-glyph line, caught by scope-auditor round 3
  - dbt_analytics/seeds/metric_catalogue.csv  # forward_pe's learn text: added the low-P/E caveat,
                                      # removed em-dashes, per owner-approved round-6 wording
  - frontend/metrics.json            # regenerated from the seed via export_metric_definitions_json.py
                                      # (never hand-edited) to pick up the metric_catalogue.csv change
  - .claude/task/contract.md

decisions_reserved (owner-approved this session, in conversation):
  - **Reopening the card-face benchmark indicator's whole visual form** — owner-initiated,
    after finding "Higher than sector median" gave no sense of scale.
  - **Min/max, not percentiles** — owner's call, corrected the agent's initial assumption
    that min/max was comparably expensive to compute; it isn't (same aggregation pass as
    the existing median, two more columns, no window functions).
  - **Replaces the indicator entirely**, does not sit alongside it.
  - **Monochrome — no color-coding.** Explored directly ("is this color-coding a good
    idea?"): rejected on two grounds, not aesthetics — it would create a second, informal
    judgment layer alongside the one deliberate verdict mechanism this app already has (the
    health badge), and "above/below median" doesn't reliably mean "good/bad" even with
    correct direction-handling (a company can be "above median" in a uniformly weak sector
    and still be weak in absolute terms). Owner did not object to this reasoning.
  - **Visual design**, converged over several iterations, each with a stated reason:
    - Two bar segments (min→median, median→max) with a small gap at the median — not a
      single continuous bar with a separate tick — reusing this project's own existing
      "surface gap separates touching marks" convention rather than inventing a new one.
    - Single vertical-line marker for the company's value (not a circle) — owner: the
      circle "doesn't look clean."
    - No second marker/tick for the median — owner explicitly rejected this ("i didn't tell
      you to use a tick") after the agent added one unprompted; the median is identified by
      its label sitting on the gap, nothing more.
    - Fixed-width min/max label columns (tabular-nums) so the bar itself starts and ends at
      the same x-position across every metric in the stack — owner: inconsistent widths
      "looks like a child has drawn it."
    - Median label's x-position is computed from the same value that positions the gap
      (not a fixed offset) — owner caught the two drifting apart in an earlier draft.
    - Marker height and the gap between the median label and the marker are both sized so
      they can't collide even when the median and the value are close together — owner
      caught a real overlap in the closest-together case (Rev growth YoY) in the full-stack
      mockup, not visible in single-cell examples.
    - Metric title chip's color bumped from `--ss-muted` to `--ss-text` for more
      prominence (font-size/weight unchanged — `var(--ss-label)`/600 already existed from
      Slice 6c) — owner's call after seeing a realistic 5-metric stack, not visible from a
      single isolated cell. Correction: an earlier draft of this bullet said
      "size/weight/color," overclaiming beyond what the diff actually changes —
      cto-reviewer round 2 caught it.
    - Existing gloss line (e.g. "Operating profit as share of sales (TTM)") stays — the
      agent dropped it when consolidating to the full-stack mockup and the owner caught it;
      it is real Tier-2 content per `north_star.md`, not decoration.

technical_definition:
  - `int_stock__sector_benchmarks.sql`: `sector_min_{metric}` / `sector_max_{metric}` added
    alongside each existing `sector_median_{metric}`, same `eligible` CTE, same
    `peer_threshold >= 8` gate (NULL below threshold, identical to today's median behavior —
    no new eligibility logic).
  - `mart_stock_cards.sql`: the 10 new columns selected through by name, matching how the 5
    existing medians are already selected (not a wildcard) — the pre_revenue exclusion
    comment already on this join applies unchanged.
  - `card_copy.py`: new helper computes `{min, median, max, position_pct, median_pct}` for
    a metric on a card, returning `None` when any of min/median/max is missing (preserves
    today's "hide the indicator entirely below 8 peers" policy — no behavior change there).
    `position_pct`/`median_pct` clamped to [0, 100] (defensive — the company's own value
    should always fall within its own cohort's min/max by construction, since the benchmark
    computation includes the card's own company, but clamp rather than trust that
    invariant blindly). Degenerate case (`min == max`, e.g. a sector where every eligible
    peer reports an identical value) returns `None` rather than dividing by zero — no range
    to show when there is no range.
  - `card_ui.py`: `_metric_cell_html()` calls the new range-mark builder instead of
    `_bench_indicator_html()`. Values (min/median/max/company's own) formatted through the
    existing `format_metric_value()` — no new formatting logic, so percent/ratio/currency
    metrics render with the same units and precision the value itself already uses. Min/max
    spans carry a `min `/`max ` text prefix. A new `_direction_cue()` appends
    `". Lower is better."` uniformly to every metric the catalogue classifies
    `direction: lower_better` (today: forward P/E and net debt/EBITDA, no
    metric-specific exception; see amendments for the full back-and-forth this landed on),
    gated on the same `benchmark_range()` availability check as the mark itself, and
    suppressed when `net_debt_to_ebitda`'s value-aware "Net cash" gloss branch is already
    active.
  - `styles.py`: new classes for the two bar segments, the marker, the median label, and
    the fixed-width min/max label columns. `.ss-bench-indicator` and `.ss-metric-value-row`
    are NOT deleted — `_benchmark_compare_body()`'s separate recap list inside "How we
    compare to similar companies" still uses `.ss-bench-indicator` directly (confirmed via
    the actual call sites: the two consumers were already decoupled at the HTML-building
    level, both reading the same underlying `benchmark_indicator_label()` text but wrapping
    it differently) — only the card-face usage changes.

explicitly_not_in_scope:
  - Extending benchmarking to the other 11 metrics (2 more operating, 5 financial, 4
    pre-revenue) — real, separate dbt work (the pre-revenue cohort needs a new code path,
    not just new columns, since it's currently excluded from the benchmarks model
    entirely). Explicit owner decision: ship the visual now, follow-up slice for the rest.
  - `_benchmark_compare_body()`'s recap list inside "How we compare to similar companies" —
    stays as plain text. The scanability problem this task solves is specific to the card
    face; the recap list is inside an already-opened detail panel, a different reading mode.
  - Color-coding — explored and rejected this session, not a deferred future step.

done_when:
  - The 5 already-benchmarked metrics render the range mark on the card face; the old
    "Higher than sector median" text no longer appears there.
  - Below the 8-peer threshold, the range mark is omitted entirely — verified against a
    real low-peer-count case, not just unit-tested in isolation.
  - `_benchmark_compare_body()`'s recap list is unchanged and still renders correctly.
  - Full test suite green, including new tests for the position-calc helper's degenerate
    (`min == max`) and out-of-range-clamped cases.
  - Verified against the real app (local Streamlit + live Supabase) via the Browser pane —
    a realistic multi-metric stack, not one isolated cell; 480px mobile smoke.
  - `docs/ui/card_metric_cell.md` updated — no longer describes the indicator this replaces.
  - UX PR gate: mobile wireframe in the PR body (this is a card-structure change); one-
    sentence primary-job statement.
  - Required reviewers (scope-auditor always; cto-reviewer per `frontend/*`/`tests/*`/
    `scripts/*`; analytics-engineer-reviewer per the bare `*.sql` pattern — matching not
    just the two changed dbt models but also `supabase/migrations/012_...sql` (fnmatch's
    `*` matches across `/`, confirmed against `commit_review_gate.py`'s actual routing
    logic) — plus `dbt_analytics/*.yml` matching both changed schema docs and the bare
    `*.csv` pattern matching `metric_catalogue.csv`; equity-analyst-reviewer per the
    explicit `docs/data_contract.md` route and the explicit `*metric_catalogue.csv`
    route; data-engineer-reviewer per the `supabase/*` route matching the new migration)
    pass
    against the staged diff. The reviewer list was itself incomplete through round 2 of
    this task's own review cycle — scope-auditor caught it (see amendments): adding a file
    to `scope_paths` didn't get its routing consequence propagated here or dispatched.

impact_map:
  - User-facing: every card showing any of the 5 benchmarked metrics, all markets, all
    eligible operating companies. Financial and pre-revenue cards are unaffected (none of
    their metrics are benchmarked today; unchanged by this task).
  - New dbt columns only — no change to any existing metric value, verdict, or eligibility
    calculation.

amendments:
  - **`done_when`'s `*.sql` attribution undercounted, scope-auditor round 8 FAIL,
    fixed.** The reviewer-attribution text said the bare `*.sql` route matched "both
    changed models" — it also matches `supabase/migrations/012_...sql` (fnmatch's `*`
    crosses `/`; confirmed directly against `commit_review_gate.py`'s routing logic).
    Doesn't change which reviewers were required (analytics-engineer-reviewer was
    already required via the two models), but scope-auditor raised a fair secondary
    concern: did analytics-engineer-reviewer's actual review ever substantively examine
    the migration's DDL, or only the two models the text named? Checked against the
    actual record: yes — its round-2 review explicitly compared `012_...sql` against
    `007_router_card_columns.sql`/`002_fundamentals_mart.sql` and verified the
    additive/nullable/no-backfill pattern directly (one of that round's two named
    `risks_checked` items, not an incidental mention). No actual coverage gap; fixed the
    attribution text to name the migration too, so the description matches what the
    routing rule (and the reviewer's own past work) actually covers.
  - **Forward P/E's `learn` text — the "no rewrite needed" check was wrong,
    equity-analyst-reviewer round 6 FAIL, fixed.** The round-5 amendment (below) said
    forward P/E's existing `learn` text "already conveys the growth-context nuance...
    no rewrite needed." On a literal re-read, that text only hedges the HIGH-P/E case
    ("A higher number often means investors expect faster growth — or are paying a
    premium today") — it says nothing about the LOW-P/E case, which is exactly the one
    that needed covering once the card face started asserting "lower is better." A low
    P/E can just as easily mean weak expected growth or a temporary earnings dip as a
    genuine bargain — the "never treat a low P/E as cheap" point this app already makes
    in `assessment_rules.py`. Owner approved a specific addition (candidate shown
    rendered, not just described): "A lower number can mean the stock is genuinely
    cheap — or that investors expect slower growth ahead." Owner's reply, verbatim:
    "Approve, add it. Yes, but bo em dashes. And all the other explanatory texts for
    the other metrics should be easy to read as well."
    **Implemented:** `dbt_analytics/seeds/metric_catalogue.csv`'s forward_pe `learn`
    field updated (both the existing em-dash and the new sentence's em-dash removed, to
    match the owner's no-em-dash rule), `frontend/metrics.json` regenerated via
    `scripts/export_metric_definitions_json.py` (never hand-edited). Full field now
    reads: "...A higher number often means investors expect faster growth, or are
    paying a premium today. A lower number can mean the stock is genuinely cheap, or
    that investors expect slower growth ahead." `_direction_cue()`'s own returned text
    changed from `" — lower is better"` to `". Lower is better."` for the same reason
    (it's part of this diff, so in scope to fix now) — tests and docs updated to match.
    **Round 7 review found two loose ends, both fixed:** scope-auditor caught a stale
    wireframe caption in `docs/ui/card_metric_cell.md`'s "Cell wireframe" section still
    showing the old `"— lower is better"` text (the "Benchmarks on the cell" section
    further down was already correct — only the wireframe caption was missed); fixed.
    Scope-auditor also caught that the CSV edit's round-trip through Python's `csv`
    module incidentally stripped now-unnecessary quotes from two unrelated rows
    (`debt_to_equity.description`, `statement_roe_pct.applicability` — both fields
    contain em-dashes but no comma, so CSV quoting was optional either way);
    cto-reviewer, equity-analyst-reviewer, and analytics-engineer-reviewer independently
    confirmed the same thing and all confirmed it was content-inert (verified
    byte-identical text, byte-identical `metrics.json` regeneration either way). Fixed
    anyway, to keep the diff surgically scoped to the one intended change rather than
    leave an unexplained side effect standing — the two rows were restored to their
    exact original (quoted) form; the diff to `metric_catalogue.csv` is now exactly the
    one forward_pe line.
    **Not done, flagged separately, owner's call on scope/timing:** the "no em-dashes"
    and "easy to read" standard, applied catalogue-wide, is much bigger than this one
    field — a repo-wide check found roughly 25 fields across nearly all 16 catalogued
    metrics use em-dashes (`gloss`/`analogy`/`learn`/`interpretation`/`applicability`/
    `calculation`), plus several more hardcoded in `frontend/card_copy.py`'s value-aware
    gloss branches (`metric_gloss()`/`metric_analogy()`/`metric_learn_text()` for
    net_debt_to_ebitda's net-cash case and ebit_margin_pct's annual-basis case). This is
    a real, separate content pass — user-visible wording (§6), not something to absorb
    into finishing this feature. Not started; the user was asked whether to spawn it as
    a follow-up.
  - **Forward P/E's direction cue — RESOLVED.** Round 3 stopped a flat "lower is better"
    claim for forward P/E, reasoning it contradicted this app's own caution elsewhere
    (assessment_rules.py excludes P/E from the health verdict). Round 4 pointed out the
    resulting silence was itself a beginner-safety gap, indistinguishable from a metric
    where silence is correct. The agent's first attempt to resolve this rested on an
    inaccurate premise ("the catalogue is silent on direction") — equity-analyst-reviewer
    round 5 FAILed it: the catalogue's `direction` field is `lower_better` for forward_pe,
    same as net debt/EBITDA; only the free-text `interpretation` carries a caveat, and
    that text was unused anywhere in the app.
    **Owner's resolution, verbatim:** "why are we not able to say 'lower is better' or
    'higher is better'. This should be true assuming the ceteris paribus
    condition(although we sgould not use this phrasing)." — i.e. treat "lower is better"
    as a plain statement about the metric's own axis, holding other factors constant; this
    doesn't conflict with excluding P/E from the health verdict, which is a claim about a
    composite judgment, not about which way one axis points. The owner also rejected the
    agent's candidate hedge ("— read alongside growth") as giving "no guidance at all,"
    and stated the caveat belongs in the metric's own explanation, not the short gloss:
    "We should address these things in the metric explanation part." Checked: forward
    P/E's existing `learn` text already conveys the growth-context nuance ("A higher
    number often means investors expect faster growth — or are paying a premium today")
    — no rewrite needed there.
    **Implemented:** `_direction_cue()` no longer special-cases any metric by name — it
    applies `". Lower is better."` uniformly to every metric the catalogue classifies
    `direction: lower_better` (forward P/E and net debt/EBITDA), driven directly off
    `BENCHMARK_METRICS`. Simpler than the round-3/4 hardcoded-exception version, and
    correctly framed: a direction statement about one axis, not a health verdict.
    `test_range_mark_direction_cue_absent_for_forward_pe` was replaced with
    `test_range_mark_direction_cue_shown_for_forward_pe`.
    **Separately, an enforcement question:** the owner asked whether "the frontend must
    stay consistent with the catalogue" can be enforced, not just documented, given the
    agent's own inaccurate claim about it moments earlier. Answer given: prose accuracy
    isn't mechanically checkable (that needs judgment — the review cycle catching this
    mistake IS that mechanism working), but the specific risk of code silently drifting
    from catalogue data can be pinned. Added
    `test_direction_cue_catalogue_assumptions_still_hold()` — asserts the exact
    `direction`/`interpretation` facts `_direction_cue()`'s logic depends on, so a future
    `metric_catalogue.csv` edit that would invalidate them breaks CI instead of silently
    going stale.
  - **Structural overflow fix, cto-reviewer round 3 FAIL, fixed.** The min/max column
    width had been reactively widened three times in this task (2.2rem → 2.6rem → 3.8rem)
    for the same root cause — real values overflowing a fixed-width box — each time fixed
    by measuring only today's data rather than bounding the actual failure mode. The
    catalogue documents that `revenue_growth_yoy_pct` and `net_debt_to_ebitda` can produce
    extreme outliers ("huge % off a small base"; "explodes when EBITDA ≈ 0"), and
    `int_stock__sector_benchmarks.sql`'s `min()`/`max()` have no clamp — a single outlier
    company becomes its sector's displayed min or max on every peer card, unbounded. Fixed
    with the plain, boring fix rather than a fourth width bump: `overflow: hidden;
    text-overflow: ellipsis;` on `.ss-metric-range-min`/`-max` in `frontend/styles.py` —
    a future outlier now truncates visibly instead of silently breaking the owner-approved
    "every metric's bar starts/ends at the same x-position in the stack" alignment
    invariant (`flex-shrink: 0` alone doesn't prevent a flex item's default
    `min-width: auto` from growing past an explicit smaller `width` to fit its content;
    `overflow` other than `visible` is what actually caps it).
  - **Forward P/E overclaim, equity-analyst-reviewer round 3 FAIL, fixed (not re-escalated
    — a correctness fix within the already-approved "Option A" mechanism, not a new
    product decision).** The round-2 fix applied `" — lower is better"` to both lower_better
    metrics (forward P/E, net debt/EBITDA) uniformly. Verified against this app's own,
    unchanged code: `dbt_analytics/seeds/metric_catalogue.csv`'s forward_pe row itself
    declines to assert a direction ("Always read next to growth"); `scripts/assessment_rules.py`
    deliberately excludes valuation from the health verdict ("never treat a low P/E as
    cheap" in its LLM prompt) — every other surface in this app treats forward P/E's
    direction with real caution, and the new card-face cue was the first place asserting
    it flatly. `net_debt_to_ebitda`'s cue is unaffected — its interpretation ("Lower =
    less leverage, safer") is genuinely monotonic and matches its unchanged use as a core
    axis in the health-verdict scoring. Fixed: `_direction_cue()` now applies only to
    `net_debt_to_ebitda`. Also suppressed when that metric's own value-aware "Net cash"
    gloss branch is already active (a secondary, non-blocking equity-analyst-reviewer
    note: the stacked "Net cash — cash on hand exceeds debt — lower is better" wording was
    redundant, since the net-cash branch already states the favorable read directly).
  - **Stale arrow-glyph doc line, scope-auditor round 3 FAIL, fixed.**
    `docs/ux_principles_finanz_lern_apps.md`'s "Benchmarks use monochrome directional text
    (↑/↓/→) per north_star" was never updated when arrows were retired for words at Slice
    6c, and was left further stale by this diff's own rewrite of the north_star.md section
    it cites. Added to `scope_paths`; line corrected to describe both current mechanisms
    (card-face range mark, recap-list short wording) without an outdated glyph reference.
  - **Direction ambiguity, equity-analyst-reviewer round 2 FAIL, owner-decided.** The
    range mark draws identically regardless of metric direction — a marker toward the
    right/max end reads as "further right = better" (the loading-bar/battery idiom) for 3
    of 5 metrics but means the *worst* relative position for the 2 where lower is better
    (forward P/E, net debt/EBITDA); nothing on the card disambiguated this, and the
    finding noted a spatial mark carries a stronger implicit favorability signal than the
    old text-only indicator ever did. Verified: `dbt_analytics/seeds/metric_catalogue.csv`
    confirms `forward_pe`/`net_debt_to_ebitda` are `direction: lower_better`, the other 3
    `higher_better`. This is a product/UX call (§6) — escalated via `AskUserQuestion` with
    3 options for the direction cue (gloss suffix / flip the axis / defer) and 2 for
    whether min/max should get text labels; the user dismissed the question
    ("[User dismissed — do not proceed, wait for next instruction]"), then said, verbatim:
    "I can't approve whta I don't know" — the text-only option descriptions weren't
    concrete enough to decide from. Rendered the actual current cells (real
    `_metric_cell_html()` output, real CSS) side by side with mockups of each option via
    `mcp__visualize__show_widget` instead of re-asking in text. Owner's reply, verbatim:
    "Option A, use min max labels" — i.e. append the gloss-line direction cue (not the
    axis-flip option) and add `min `/`max ` text prefixes to the flanking numbers.
  - Owner caution during this exchange, verbatim: "be careful_: in some drafts the median
    gap is in the middle whixh is not necessarily consistent with the scaling" — a check
    on the mockup widget specifically (which hand-typed a `50%` gap position for its
    example rather than recomputing it, coincidentally correct only because that example's
    median happened to sit exactly halfway between min and max). Verified the real
    `benchmark_range()` computes `median_pct` from actual data every time (never a fixed
    midpoint) — already covered by the skewed-median tests from the prior amendment;
    re-confirmed live post-implementation with a non-centered fixture.
  - Implementing the `min `/`max ` labels surfaced a real, unrelated-to-direction bug:
    the fixed-width min/max column (then 2.6rem) overflowed for realistic longer values
    once prefixed (`"min -24.6%"` needed 54px against a 42px box) — caught by live
    measurement, not assumed. Widened to `3.8rem`; re-verified zero overflow across every
    metric's min/max at both desktop and 375px mobile widths, and that the bar-end/median-
    label-clamp fixes from the prior amendment still hold at the new width. Separately
    surfaced (not fixed, out of scope): the card's actual rendered font is
    `"Source Sans", sans-serif`, not the `"DM Sans"` the global CSS declares with
    `!important` — pre-existing, repo-wide, unrelated to this task; flagged via
    `spawn_task` for separate follow-up rather than fixed here.
  - `done_when`'s required-reviewer list never got the routing consequences of the two
    scope_paths additions above: `docs/data_contract.md` routes to equity-analyst-reviewer,
    `supabase/*` routes to data-engineer-reviewer (`.claude/review_routing.json`), and
    neither was dispatched for round 2. scope-auditor round 2 FAILed on exactly this — a
    process gap in the review cycle itself, not the diff's content. Fixed: both reviewers
    added to `done_when` and dispatched against the same round-2 diff.
  - `docs/data_contract.md` added to `scope_paths` after the fact. scope-auditor round 1
    FAILed: this doc's "Sector benchmarks (dbt → export)" Output table and its
    `mart_stock_cards` column table both document the `sector_median_*` columns this diff
    sits directly alongside (same model, same mart), and were left stale. Cited repo
    precedent (`.claude/active_work.md` #140) for this exact failure mode. Not an owner
    decision — the min/max columns themselves were already owner-approved (see
    decisions_reserved above); this only transcribes them into the doc using the same
    table structure and `nullable` notation the doc already uses for the sibling median
    columns, no new content invented.
  - Two geometry bugs, both cto-reviewer round 1 FAILs, both fixed and re-verified against
    live computed geometry with deliberately skewed edge-case data (median near the sector
    min, median near the sector max, a company sitting exactly at its sector's own min/max):
    - Bar-end segment (`_metric_range_html()`) anchored its inner (median-side) edge but
      shrank a `left`-anchored `width` from its *outer* edge instead — every card's bar
      stopped ~2px short of the true sector-max position instead of the gap sitting only
      at the median. Fixed: `left:calc({median_pct}% + 2px)` with no inline `width`,
      `right:0` added to `.ss-metric-range-bar-end` in CSS so the outer edge is always the
      true track boundary — mirrors how `bar-start` already anchors `left:0` and only
      shrinks its own inner edge.
    - Median label had no floor on its distance from the track's own edges — for a
      realistically skewed sector (e.g. a fat right tail on forward P/E), the median can
      sit within a few percent of the min or max, and the label (`white-space:nowrap`,
      centered via `translateX(-50%)`) would run past the track into the fixed-width
      min/max columns. Fixed: `left:clamp(3rem, {median_pct}%, calc(100% - 3rem))` — the
      label's *reading position* is floored 3rem from either track edge; the bar's actual
      gap position (`median_pct`, unclamped) still shows the true value, only the text
      label is nudged inward to stay legible. Verified this doesn't change the label
      position for any non-extreme median (clamp is a no-op inside the safe zone).
  - Min/max/median text bumped from bespoke sub-caption sizes (0.65rem / 0.6rem — smaller
    than any other text in the stylesheet) to `var(--ss-caption-size)` (0.72rem, this app's
    standard secondary-text token, used everywhere else for gloss/caption content). Raised
    live during the Verify step's real-app check. Owner's words, verbatim: "numbers for min
    max and median are really small." Min/max column width widened 2.2rem -> 2.6rem and
    `white-space: nowrap` added so the larger text can't wrap inside the fixed-width column;
    the median label got an explicit `line-height: 1` so its larger text doesn't reopen the
    marker-collision bug fixed earlier in design (owner: "the tick now crosses the median
    label text"). Re-verified by measuring live computed geometry (gap label->marker,
    gap marker->gloss, wrap state) across all 5 metrics post-change, not just visually.
