# Card metric cell — UI spec

**Scope:** One metric block on the Company Snapshot (`_metric_cell_html` in `frontend/card_ui.py`).  
**Authority:** [`north_star.md`](../north_star.md) (three hero metrics + two balance metrics).

---

## Cell wireframe

```
┌──────────────────────┐
│ Operating margin     │  ← label (period-honest)
│ (TTM)                │
│                      │
│ 20.5%            ↑   │  ← value (largest) + optional bench indicator
│                      │
│ Operating profit as  │  ← gloss (one short line, Tier 2)
│ share of sales (TTM) │
└──────────────────────┘
```

**Visual hierarchy (strict):**

1. **Label** — `.ss-metric-label` — period in parentheses when needed (`Operating margin (TTM)` vs `(annual)` via `metric_label()`).
2. **Value** — `.ss-metric-value` — numeric, dominant; benchmark arrow (`↑`/`↓`/`→`) inline on `.ss-metric-value-row` when ≥8 sector peers.
3. **Gloss** — `.ss-metric-gloss` — one plain-language line under the value; always visible on the card face (Tier 2).

Deep copy (analogy, learn text) lives in **Understand these numbers** (`<details>`), not in the cell.

---

## Hero vs balance grid

| Grid | Metrics | CSS |
|------|---------|-----|
| Hero (3) | Forward P/E, operating margin, revenue growth YoY | `.ss-metrics-hero` |
| Balance (2) | Net debt / EBITDA, FCF margin | `.ss-metrics-balance` |

Mobile: three hero **values** visible without scrolling (north_star success check).

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

- Show `↑` / `↓` / `→` only when `sector_peer_count >= 8`.
- **Hide indicator entirely** when peers &lt; 8 — no “unavailable” on the card face.
- Full median primer and per-metric compare lines live in **How we compare to similar companies** (`<details>`), not duplicated under every cell.

---

## Anti-patterns

- Putting analogy or `METRIC_LEARN` paragraphs under the value on first load.
- Using color alone for above/below median (monochrome text only in v1).
- Hard-coding “Operating margin (TTM)” when `ebit_margin_basis` is `annual_latest`.
- Replacing gloss with raw Yahoo field names (`operatingMargins`, etc.).

---

## 480px smoke

- [ ] Label + value + gloss readable for all three hero metrics without horizontal scroll
- [ ] Value is the most prominent element in each cell
- [ ] Benchmark glyph does not wrap to its own line away from the value

---

## Related

- [`../ux_principles_finanz_lern_apps.md`](../ux_principles_finanz_lern_apps.md) — Kennzahlen-Schule / playgrounds
- Epic [#92](https://github.com/ramialfahham/stock-swipe-app/issues/92) — post-metric-trust UX backlog
