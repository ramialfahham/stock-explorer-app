# Card metric cell — UI spec

**Scope:** One metric block on the Company Snapshot (`_metric_cell_html` in `frontend/card_ui.py`).  
**Authority:** [`north_star.md`](../north_star.md) (five fundamentals, priority order).

---

## Cell wireframe

```
┌───────────────────────────┐
│ [Operating margin (TTM)]  │  ← label chip (period-honest)
│                           │
│ 21.5%                     │  ← value (largest)
│                           │
│ min 4.1%  ▁▁●▁  max 38.9% │  ← range mark: min/max flanking (labeled), marker =
│         median 15.3%      │    this company, small label at the median position
│                           │
│ Operating profit as share │  ← gloss (one short line, Tier 2) — for the metrics
│ of sales (TTM)            │    where lower is better, ends ". Lower is better.";
│                           │    see Benchmarks on the cell below
└───────────────────────────┘
```

**Visual hierarchy (strict):**

1. **Label** — `.ss-metric-label` — a bordered/filled chip (Slice 6c; `--ss-bg` fill,
   `--ss-radius-control` corners), applied uniformly to every metric — period in
   parentheses when needed (`Operating margin (TTM)` vs `(annual)` via `metric_label()`).
2. **Value** — `.ss-metric-value` — numeric, dominant, on its own row.
3. **Range mark** — `.ss-metric-range` — this company's value positioned between its
   sector's min and max, median labeled at its own position (not a fixed offset — see
   Benchmarks on the cell below). Replaced the old inline "Higher than sector median" text
   entirely; no longer sits on the value's own row.
4. **Gloss** — `.ss-metric-gloss` — one plain-language line under the value; always visible on the card face (Tier 2).

Deep copy (analogy, learn text) lives in **Understand these numbers** (`st.expander` — one
panel per card), not in the cell. Inside that panel, the analogy line renders unconditionally
per metric; the longer learn-text paragraph sits behind its own `disclosure_html()` Read
more/Show less toggle — see [`disclosure_pattern.md`](disclosure_pattern.md).

---

## Metric stack (single column)

All five metrics render in **one vertical column** (`.ss-metrics-stack`), in `ALL_METRICS` order:

1. Forward P/E  
2. Operating margin  
3. Revenue growth YoY  
4. Net debt / EBITDA  
5. FCF margin  

No hero/balance split; no side-by-side rows at any breakpoint.

---

## Value-aware gloss

Some metrics need copy that depends on the **number**, not just the metric id.

| Metric | Condition | Gloss behavior |
|--------|-----------|----------------|
| `net_debt_to_ebitda` | value &lt; 0 | “Net cash — cash on hand exceeds debt” (not “years to repay”) |
| `ebit_margin_pct` | `ebit_margin_basis == annual_latest` | Label/gloss say **annual**, not TTM |

**Implementation:** `metric_gloss()`, `metric_analogy()`, `metric_learn_text()` in `frontend/card_copy.py` — pass the full `card` dict when basis or sign matters.

When adding a new value-aware metric, update `card_copy.py` **and** this table in the same PR.

---

## Benchmarks on the cell

- The range mark (`_metric_range_html()` in `frontend/card_ui.py`, via
  `benchmark_range()` in `frontend/card_copy.py`) shows only when `sector_peer_count >= 8`
  **and** the sector has genuine spread (`sector_min != sector_max` for this metric) — a
  sector where every eligible peer reports the same value has no range to show, not an
  error to hide.
- **Omit entirely** when either condition fails — no "unavailable" placeholder on the card
  face, same policy the old text indicator followed.
- The company's own value and the median are both clamped to `[0, 100]%` position within
  `[min, max]` defensively; under normal operation the card's own company is part of the
  cohort its own min/max is computed from, so it should already fall inside that range.
- The median **label's** on-track reading position is separately floored 3rem from either
  track edge (`left:clamp(3rem, {median_pct}%, calc(100% - 3rem))`) — a realistically
  skewed sector can put the true median within a few percent of the min or max, and the
  label text must not run into the fixed-width min/max columns. The bar's actual gap still
  renders at the true, unclamped `median_pct`; only the label text is nudged inward.
- Min/median/max are all formatted through `format_metric_value()` — same units and
  precision the value itself already uses, no separate formatting logic. Min and max carry
  a `min `/`max ` text prefix (matching the median's own `median X` label) — the median
  label is not the only flanking number that needs identifying as such.
- **Direction cue** (`_direction_cue()` in `frontend/card_ui.py`): a plain bar-and-marker
  otherwise implies "further right = better" the way a loading bar or battery does — true
  for the 3 higher_better metrics (operating margin, revenue growth, FCF margin), which
  need no cue since that already matches the convention. Applies uniformly to every
  metric the catalogue classifies `direction: lower_better` — today, both forward P/E and
  net debt/EBITDA — with the gloss line ending `". Lower is better."`. No metric-specific
  exception: this is a ceteris-paribus statement about the metric's own axis (a lower P/E
  is more attractively priced for the same growth/quality profile), not a health
  judgment, so it doesn't conflict with `assessment_rules.py` excluding P/E from the
  health verdict — that's about not letting P/E alone drive a composite score, a
  different and higher-stakes claim than naming which way one axis points. The caveat
  that P/E should be read alongside growth belongs in forward P/E's own deep-dive
  explanation (analogy/learn text in "Understand these numbers"), not a hedge stuffed
  into this short gloss line — owner decision, after an earlier draft tried exactly that
  hedge and was correctly rejected as giving "no guidance at all." Also suppressed when
  net_debt_to_ebitda's own value-aware "Net cash" gloss is already
  showing — that branch already states the favorable read directly. Tied to the same
  availability check as the range mark itself (no mark to disambiguate, no cue). Caught by
  equity-analyst-reviewer (round 2): an unlabeled spatial mark carries a stronger implicit
  favorability signal than the old text-only indicator ever did, for exactly the metric
  (debt) `north_star.md`'s "Do not use naive rankings — misleading for debt" line
  already warns about.
- Only the 5 metrics with `benchmarkable: true` in the metric catalogue get a range mark
  today (forward P/E, operating margin, revenue growth, net debt/EBITDA, FCF margin) —
  financial and pre-revenue metrics aren't benchmarked yet, a separate follow-up.
- Full median primer and per-metric compare lines still live in **How we compare to
  similar companies** inside **Understand these numbers** — that recap list is unchanged,
  still text-only (`.ss-bench-indicator`, `benchmark_indicator_label()`); the scanability
  problem the range mark solves is specific to the card face, not that already-disclosed
  detail panel.
- When peers &lt; 8, that section shows one calm line: “Fewer than 8 similar companies in this market — sector compare is hidden.”

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

---

## 480px smoke

- [ ] Label + value + gloss readable for each metric without horizontal scroll
- [ ] Value is the most prominent element in each cell
- [ ] Range mark's min/max labels don't force horizontal scroll; fixed-width columns keep
      every metric's bar starting and ending at the same x-position in the stack
- [ ] All five metrics visible in one column

---

## Related

- [`../ux_principles_finanz_lern_apps.md`](../ux_principles_finanz_lern_apps.md) — Kennzahlen-Schule / playgrounds
- [`discover_header.md`](discover_header.md)
