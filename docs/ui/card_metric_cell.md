# Card metric cell — UI spec

**Scope:** One metric block on the Company Snapshot (`_metric_cell_html` in
`frontend/card_ui.py`) and the lens grouping the metric stack renders it inside
(`_metric_stack_with_groups`, same file).  
**Authority:** [`north_star.md`](../north_star.md) ("The card: fundamentals by company type").

---

## Cell wireframe

```
┌───────────────────────────────┐
│ [Operating margin (TTM)]      │  ← label chip (period-honest)
│                                │
│ 21.5%                          │  ← value (largest)
│                                │
│  -150.2%      16.9%     49.7% │  ← numbers row: min / median / max values, each
│                                │    center-aligned on its real bar position
│  ▁▁▁▁▁▁▁▁▁▁●▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁ │  ← bar: two segments with a gap at the median,
│                                │    marker (●) = this company
│   min       median       max  │  ← words row: same center-alignment rule as the
│                                │    numbers row directly above it
│ Operating profit as share      │  ← gloss (one short line, Tier 2) — ends
│ of sales (TTM). Higher is      │    ". Higher/Lower is better." for every metric
│ better.                        │    with a catalogue direction — see Benchmarks
└───────────────────────────────┘
```

**Visual hierarchy (strict):**

1. **Label** — `.ss-metric-label` — a bordered/filled chip (Slice 6c; `--ss-bg` fill,
   `--ss-radius-control` corners), applied uniformly to every metric — period in
   parentheses when needed (`Operating margin (TTM)` vs `(annual)` via `metric_label()`).
2. **Value** — `.ss-metric-value` — numeric, dominant, on its own row.
3. **Range mark** — `.ss-metric-range` — three rows (numbers, bar, words). This
   company's value sits on the bar between its sector's min and max; the median gets
   its own gap in the bar plus a label in both the numbers and words rows. Min,
   median, and max are positioned with the *same* rule (`left:X%` + a shared CSS
   class's `transform: translateX(-50%)`) so they read as one consistent reference
   frame — see Benchmarks below for exactly how each is placed and clamped.
4. **Gloss** — `.ss-metric-gloss` — one plain-language line under the range mark (or
   under `.ss-metric-range-unavailable`'s placeholder line, when this metric has no
   mark); always visible on the card face (Tier 2). `0.5rem` top margin on both the
   mark/placeholder (from the value) and the gloss (from the mark/placeholder) —
   originally `0.1rem`, raised after owner feedback that the gloss line read as "too
   close to the number or to the bullet graph." Both rules are scoped
   `.ss-metric .ss-metric-gloss` / `.ss-metric .ss-metric-range-unavailable`, not bare
   single-class selectors — see the anti-pattern below, this isn't cosmetic.
   Typography (2026-08-26, owner feedback on a live card): `0.78rem` / `--ss-muted` /
   `line-height: 1.35`, deliberately one step LARGER and LIGHTER than the range mark's own
   `.ss-metric-range-number` / `.ss-metric-range-word` (`--ss-caption-size` /
   `--ss-caption`). At matched size and colour the explanation read as a footnote to the
   bar instead of the point of the cell. Keep the two tiers distinct if either changes.

Deep copy (analogy, learn text) lives in **Understand these numbers** (`st.expander` — one
panel per card), not in the cell. Inside that panel, the analogy line renders unconditionally
per metric; the longer learn-text paragraph sits behind its own `disclosure_html()` Read
more/Show less toggle — see [`disclosure_pattern.md`](disclosure_pattern.md).

---

## Metric stack: lens-grouped, per-type

All metrics for a card render in **one vertical column** (`.ss-metrics-stack`),
grouped and ordered by analytical lens, via `metrics_for_card()` /
`_metric_stack_with_groups()` in `frontend/card_ui.py`:

- `metrics_for_card(card)` (`frontend/card_copy.py`) selects which metrics apply to
  this card's `company_type` (Sector/Lifecycle Router) and have a non-null value, then
  sorts by `(lens rank, display_order)` — `_LENS_ORDER = ("valuation", "profitability",
  "growth", "solvency", "liquidity", "cash", "returns")`, matching the catalogue's own
  `perspective` field.
- `_metric_stack_with_groups(card, cell_fn)` walks that ordered list and inserts a
  `<p class="ss-metric-group-heading">` (the lens name, title-cased via
  `metric_perspective_label()`) every time the lens changes — once per group, not once
  per metric. The **same** helper renders both the card-face metric cells and the
  learn panel's per-metric definitions, so the two surfaces always group identically.
- Which lenses actually appear, and how many metrics land in each, varies by
  `company_type` — e.g. an operating card spans all 7 lenses (including two metrics
  under **Solvency**: net debt/EBITDA and debt/equity — a real per-lens count, not a
  bug), while the pre-revenue survival set only touches Valuation/Liquidity/Cash. There
  is no hardcoded per-type metric list in this doc to keep in sync — read
  `metrics_for_card()` for the authoritative set.

No hero/balance split; no side-by-side rows at any breakpoint.

**Group heading spacing (`.ss-metric-group-heading` in `frontend/styles.py`):** the
card face lays the stack out on a CSS grid (`.ss-metrics-grid { gap: 0.95rem }`), so a
heading's own `margin` *adds to* that gap rather than replacing it. The card-face rule
(`.ss-metrics-stack .ss-metric-group-heading`) accounts for this deliberately: a
positive `margin-top` on top of the grid gap for a clear break before a new section,
and a *negative* `margin-bottom` to claw back part of the grid gap so the heading reads
as attached to the group below it rather than floating equidistant between both
neighbors. The learn panel's list container has no `gap`, so it uses the plain
(non-negative) base rule instead — see the anti-pattern below before changing either.

---

## Value-aware gloss

Some metrics need copy that depends on the **number**, not just the metric id.

| Metric | Condition | Gloss behavior |
|--------|-----------|----------------|
| `net_debt_to_ebitda` | value &lt; 0 | “Net cash: cash on hand exceeds debt” (not “years to repay”), and the universal direction cue below is suppressed; this branch already states the favorable read directly |
| `debt_to_equity` | value &lt; 0 | “Negative equity, so this ratio isn't a normal leverage read” and the cue is suppressed — same failure shape as net debt/EBITDA (debt is always ≥ 0, so a negative ratio structurally means equity itself went negative — the catalogue's own `applicability` text: "the ratio then flips or explodes"), self-detecting from the ratio's own sign the same way. `statement_roe_pct` has the same underlying risk (a loss over negative equity can read as a spuriously positive %) but is **not** self-detecting this way — its sign alone can't distinguish that case from genuine profitability, and fixing it properly needs a raw equity-sign signal the pipeline doesn't currently expose to the frontend. Given a caveat in its `learn` text instead (equity-analyst-reviewer, round 2 of this task) rather than a frontend-only value-aware branch. |
| `ebit_margin_pct` | `ebit_margin_basis == annual_latest` | Label/gloss say **annual**, not TTM — the direction cue still appends after this alternate base text |

**Implementation:** `metric_gloss()`, `metric_analogy()`, `metric_learn_text()` in `frontend/card_copy.py` — pass the full `card` dict when basis or sign matters.

When adding a new value-aware metric, update `card_copy.py` **and** this table in the same PR.

---

## Universal direction cue

Every metric with a known catalogue `direction` (currently all 16 — 11 `higher_better`,
5 `lower_better`, none `neutral` today) gets its gloss line suffixed with a plain
`". Higher is better."` / `". Lower is better."`, via `metric_direction()` /
`metric_gloss()` in `frontend/card_copy.py`.

- **Applies to every metric, not just the 5 with a range mark.** A metric without a
  mark (not `benchmarkable: true`, or a marked metric whose sector fell below the peer
  threshold this card) still gets the same plain cue — see the next section for why
  the mark itself is more limited. This decouples two things the old (pre-2026-08-24)
  design conflated: whether a range MARK can be drawn (needs a sector cohort to compare
  against) and whether the direction CUE can be stated (a fact about the metric's own
  axis, independent of any cohort).
- **This is a ceteris-paribus statement about the metric's own axis** — e.g. a lower
  P/E is more attractively priced for the same growth/quality profile — not a health
  judgment. It doesn't conflict with `assessment_rules.py` excluding P/E from the
  health verdict, which is about not letting P/E alone drive a composite score, a
  different and higher-stakes claim than naming which way one axis points (owner
  decision). The caveat that P/E should be read alongside growth belongs in forward
  P/E's own deep-dive explanation (analogy/learn text in "Understand these numbers"),
  not a hedge stuffed into this short gloss line — an earlier draft tried exactly that
  hedge and was correctly rejected as giving "no guidance at all."
- **Suppressed** for `net_debt_to_ebitda`'s "Net cash" branch and `debt_to_equity`'s
  "Negative equity" branch (see the value-aware gloss table above) — both already state
  the actual situation directly, and appending "Lower is better." on top would imply a
  more negative number is a better version of the same good news, when it's a
  different, broken state. Nothing else opts out.
- A plain bar-and-marker otherwise implies "further right = better" the way a loading
  bar or battery does — true for `higher_better` metrics, which need no cue since that
  already matches the convention, but actively misleading for `lower_better` metrics
  without one. Originally caught by equity-analyst-reviewer: an unlabeled spatial mark
  carries a stronger implicit favorability signal than the old text-only indicator ever
  did, for exactly the metric (debt) `north_star.md`'s "Do not use naive... rankings"
  line already warns about. The cue being universal now (rather
  than mark-gated) is a direct extension of that same reasoning to every metric.

---

## Range mark mechanics

- The range mark (`_metric_range_html()` in `frontend/card_ui.py`, via
  `benchmark_range()` in `frontend/card_copy.py`) shows only when `sector_peer_count >= 8`
  **and** the sector has genuine spread (`sector_min != sector_max` for this metric) — a
  sector where every eligible peer reports the same value has no range to show, not an
  error to hide.
- **When either condition fails, or the metric isn't `benchmarkable: true` at all**,
  `_metric_range_html()` returns `""` and `_metric_cell_html()` falls back to
  `_metric_range_unavailable_html()` — a single calm line, `"No sector comparison for
  this metric."` (`.ss-metric-range-unavailable`). Added 2026-08-24 after owner
  feedback that a silent gap where the mark would have been "still looks like a bug"
  — a missing element, not an intentional absence. The direction cue (previous
  section) still shows either way, mark or placeholder.
- Three rows: numbers (`.ss-metric-range-numbers`), bar (`.ss-metric-range-track`),
  words (`.ss-metric-range-words`). Min and max sit exactly at the track's own edges
  (`left: 0%` / `left: 100%`), centered via `transform: translateX(-50%)`.
  `.ss-metric-range-number` also carries `max-width: 5rem; overflow: hidden;
  text-overflow: ellipsis` — added after cto-reviewer flagged that the equivalent
  fixed-width-column protection on the old design (dropped when this design moved to
  absolute positioning) had no replacement, for a data shape this doc's own "Known
  data-quality interaction" note confirms is live today. This is a bounded cap, not an
  unconditional guarantee: it comfortably covers every real value seen in production
  (including the -129,810.5% DYL outlier, ~60px rendered) with headroom to spare, but a
  sufficiently more extreme *future* outlier could still ellipsis-truncate rather than
  overflow cleanly — that's the intended degradation (visibly truncated, not silently
  breaking layout), not a claim that no value can ever be too wide. Tightening the cap
  further to close that gap entirely is not possible without also clipping legitimate,
  non-outlier values (the container's own padding alone bounds a collision-free half
  width to ~19px, tighter than even an ordinary "-150.2%").
- **Min/median/max share one alignment rule**, not three: every point renders via
  `_range_point_html()` into `.ss-metric-range-number` / `.ss-metric-range-word`, both
  styled with `transform: translateX(-50%)` in CSS — only the inline `left` position
  differs per point. An earlier draft edge-anchored min/max instead (text growing
  outward from the track's ends) while centering median on its own point; that read as
  three different rules and made the max label drift away from its own tick. Don't
  reintroduce a per-role class (`-min`/`-max`/`-median-label`) — the shared class *is*
  the guarantee that all three stay visually consistent.
- The company's own value and the median are both clamped to `[0, 100]%` position within
  `[min, max]` defensively; under normal operation the card's own company is part of the
  cohort its own min/max is computed from, so it should already fall inside that range.
- The median **label's** on-track reading position (in both the numbers and words rows)
  is separately floored/ceilinged 3rem from either track edge —
  `left:clamp(3rem, {median_pct}%, calc(100% - 3rem))` — a realistically skewed sector
  can put the true median within a few percent of the min or max, and the label text
  must not run into the min/max labels at the track's own edges. The bar's actual gap
  still renders at the true, unclamped `median_pct`; only the label text is nudged
  inward. Verified against every real range-mark row in production (3,967 rows across
  all 5 benchmarked metrics, incl. a sector with a -129,810.5% FCF-margin outlier — see
  the data-quality note below) plus synthetic cases beyond today's real spread; the
  tightest real numbers-row gap currently live is ~12px, comfortably non-colliding.
  This is a fixed floor, not width-aware — an even more extreme future data shape could
  in principle still crowd it. If a real case ever visibly collides, widen the floor
  (and re-verify against production data the same way) rather than special-casing one
  metric.
- Min/median/max are all formatted through `format_metric_value()` — same units and
  precision the value itself already uses, no separate formatting logic. No "min "/"max "
  text prefix on the numbers row (that was the old design) — the words row directly
  below carries "min"/"median"/"max" instead, once, for the whole row.
- Only the 5 metrics with `benchmarkable: true` in the metric catalogue get a range
  mark today (forward P/E, operating margin, revenue growth, net debt/EBITDA, FCF
  margin) — financial and pre-revenue metrics aren't benchmarked yet, a separate
  follow-up. (The direction cue is not limited this way — see above.)
- Full median primer and per-metric compare lines still live in **How we compare to
  similar companies** inside **Understand these numbers** — that recap list is unchanged,
  still text-only (`.ss-bench-indicator`, `benchmark_indicator_label()`); the scanability
  problem the range mark solves is specific to the card face, not that already-disclosed
  detail panel.
- When peers &lt; 8, that section shows one calm line: “Fewer than 8 similar companies in this market: sector compare is hidden.”

**Known data-quality interaction:** sector min/max are computed from raw ratios with no
outlier handling upstream. At least one live sector (ASX Energy, `fcf_margin_pct` /
`ebit_margin_pct`) currently has its whole cohort's range dominated by one company with
a near-zero-revenue denominator (Deep Yellow / DYL: -129,810.5% FCF margin), which
compresses every other company's marker in that sector toward one end of the bar. The
mark still renders correctly (verified — no visual bug), but the *comparison itself* is
close to meaningless for that sector until the underlying metric/eligibility rule
excludes or winsorizes near-zero-revenue denominators upstream. That's a dbt-layer
metric-definition decision (owner's call, `docs/layering.md` + working agreement §6),
not something to patch in the frontend — flagged here so it isn't rediscovered from
scratch.

---

## Anti-patterns

- Putting analogy or `METRIC_LEARN` paragraphs under the value on first load.
- Using color alone for above/below median (monochrome only — deliberately reopened and
  re-confirmed when the range mark replaced the text indicator, not an oversight).
- Hard-coding “Operating margin (TTM)” when `ebit_margin_basis` is `annual_latest`.
- Replacing gloss with raw Yahoo field names (`operatingMargins`, etc.).
- Two-column metric grids on mobile (net debt + FCF side by side).
- Deriving a range-mark test fixture's expected position from the same value that
  produces it (e.g. computing the assertion from `STALE_SNAPSHOT_DAYS`-style live
  constants) — pin to literal numbers so the test can actually fail.
- Giving `.ss-metric-group-heading` a plain positive `margin` and assuming that's the
  whole story — the card face's grid `gap` already provides spacing, so an
  unscoped margin compounds into a lopsided, oversized gap above every heading. Any
  margin change to this class needs the `.ss-metrics-stack`-scoped override kept in
  sync (or removed deliberately, not by accident) — see "Group heading spacing" above.
- Gating the direction cue on range-mark availability again ("no mark → no cue") — that
  was the old design, corrected deliberately (ceteris paribus applies regardless of
  whether a cohort to compare against currently exists).
- Leaving `_metric_range_html()`'s `""` return unhandled again (a silent gap where the
  mark would have been) — always route it through `_metric_range_unavailable_html()`.
- Styling a new `<p>`-rendered class in `frontend/styles.py` with a bare single-class
  selector and assuming its `margin` applies. Streamlit's own emotion-cache stylesheet
  carries an ancestor-scoped `p { margin-top: 0; margin-left: 0; margin-right: 0; }`
  reset at (0,1,1) specificity, which silently beats a (0,1,0) single-class rule
  regardless of source order — no error, `getComputedStyle` just reports Streamlit's
  value instead of yours. This bit both `.ss-metric-gloss` and
  `.ss-metric-range-unavailable` on first write (the fix each needed is why they're
  scoped `.ss-metric .ss-metric-gloss` / `.ss-metric .ss-metric-range-unavailable`
  rather than bare classes). Scope under a parent class for (0,2,0)+ specificity
  instead of trying to win a specificity tie on source order alone.

---

## 480px smoke

- [ ] Label + value + gloss readable for each metric without horizontal scroll
- [ ] Value is the most prominent element in each cell
- [ ] Range mark's min/max numbers/words don't force horizontal scroll or visibly clip
      against the card edge; every metric's bar starts and ends at the same x-position
      in the stack
- [ ] Median label doesn't collide with min or max when the sector is realistically
      skewed (median near either edge)
- [ ] Group headings read as attached to the group below them, with a clearly bigger
      gap above (new section) than the spacing between two metrics in the same group
- [ ] All metrics for this company_type visible in one column, correctly grouped
- [ ] A metric with no mark (never benchmarked, or below peer threshold) shows the
      "No sector comparison for this metric." placeholder, not a silent gap
- [ ] Gloss line has visible, even breathing room from what's above it, whether that's
      a range mark or the unavailable placeholder — not visually stuck together

---

## Related

- [`../ux_principles_finanz_lern_apps.md`](../ux_principles_finanz_lern_apps.md) — Kennzahlen-Schule / playgrounds
- [`discover_header.md`](discover_header.md)
