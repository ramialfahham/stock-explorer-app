# Card metric cell — UI spec

**Scope:** One metric block on the Company Snapshot (`_metric_cell_html` in `frontend/card_ui.py`).  
**Authority:** [`north_star.md`](../north_star.md) (five fundamentals, priority order).

---

## Cell wireframe

```
┌──────────────────────┐
│ [Operating margin    │  ← label chip (period-honest)
│  (TTM)]              │
│                      │
│ 20.5%   Higher than  │  ← value (largest) + optional bench indicator
│         sector median│
│                      │
│ Operating profit as  │  ← gloss (one short line, Tier 2)
│ share of sales (TTM) │
└──────────────────────┘
```

**Visual hierarchy (strict):**

1. **Label** — `.ss-metric-label` — a bordered/filled chip (Slice 6c; `--ss-bg` fill,
   `--ss-radius-control` corners), applied uniformly to every metric — period in
   parentheses when needed (`Operating margin (TTM)` vs `(annual)` via `metric_label()`).
2. **Value** — `.ss-metric-value` — numeric, dominant; benchmark indicator (words, e.g.
   "Higher than sector median" — Slice 6c replaced the old `↑`/`↓`/`→` glyphs) inline on
   `.ss-metric-value-row` when ≥8 sector peers.
3. **Gloss** — `.ss-metric-gloss` — one plain-language line under the value; always visible on the card face (Tier 2).

Deep copy (analogy, learn text) lives in **Understand these numbers** (`st.expander` — one
panel per card, Slice 6c; was `<details>` before), not in the cell.

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

- Show the indicator words ("Higher than sector median" / "Lower than sector median" /
  "At sector median" — `benchmark_indicator_label()`) only when `sector_peer_count >= 8`.
- **Hide indicator entirely** when peers &lt; 8 — no “unavailable” on the card face.
- Full median primer and per-metric compare lines live in **How we compare to similar companies** inside **Understand these numbers**.
- When peers &lt; 8, that section shows one calm line: “Fewer than 8 similar companies in this market — sector compare is hidden.”

---

## Anti-patterns

- Putting analogy or `METRIC_LEARN` paragraphs under the value on first load.
- Using color alone for above/below median (monochrome text only in v1).
- Hard-coding “Operating margin (TTM)” when `ebit_margin_basis` is `annual_latest`.
- Replacing gloss with raw Yahoo field names (`operatingMargins`, etc.).
- Two-column metric grids on mobile (net debt + FCF side by side).

---

## 480px smoke

- [ ] Label + value + gloss readable for each metric without horizontal scroll
- [ ] Value is the most prominent element in each cell
- [ ] Benchmark indicator words don't wrap away from the value in a way that reads as a
      separate, disconnected line
- [ ] All five metrics visible in one column

---

## Related

- [`../ux_principles_finanz_lern_apps.md`](../ux_principles_finanz_lern_apps.md) — Kennzahlen-Schule / playgrounds
- [`discover_header.md`](discover_header.md)
