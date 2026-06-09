# Saved list — UI spec

**Scope:** Saved tab list view (not focus view, not compare).  
**Authority:** [`north_star.md`](../north_star.md) (Saved = learning list + single focus).  
**Implementation:** `frontend/app.py` (`_render_saved_tab`), `frontend/styles.py` (`.ss-saved-list-*`).

---

## Primary job

User scans saved companies and opens **one** at a time to continue learning.

---

## List row wireframe (480px)

Each row is **HTML + a separate Open button** — not a single `st.button` carrying all copy.

```
┌─────────────────────────────────────────────┐
│ Fundamentals as of June 8, 2026             │  ← once at tab top (list mode only)
├─────────────────────────────────────────────┤
│ Apple Inc.                          [Open] │
│ AAPL · Technology                           │
├─────────────────────────────────────────────┤
│ HSBC Holdings                       [Open] │
│ HSBA · Financial Services                   │
└─────────────────────────────────────────────┘
```

**Line 1 (`.ss-saved-name`):** company display name — largest text in the row.  
**Line 2 (`.ss-saved-sector`):** `{ticker} · {sector}` via `saved_row_subtitle()` — no dates, no metrics.

---

## Layout rules

| Rule | Detail |
|------|--------|
| Row structure | `st.columns([5, 1])` — text block left, **Open** right |
| Freshness | **Tab-level once** — `Fundamentals as of {date}` above the list; **never per row** |
| Focus mode | `← Back to list` then single Company Snapshot (same as Discover) |
| Empty state | One `st.info` — no fake rows |
| Compare | Optional 2-up vertical compare in focus flow — never N-column matrix |

---

## Anti-patterns (do not ship)

- **Never put 3+ text lines inside an `st.button` label** (Streamlit renders button labels poorly; multi-line hacks break on mobile).
- **Never repeat “As of …” on every row** — clutters the learning list.
- **Never use the full card or metric grid in list mode** — list is for picking, not reading numbers.
- **Never horizontal-scroll tables** of saved companies on mobile.

---

## 480px smoke

- [ ] No horizontal scroll on the list
- [ ] Company name + ticker · sector readable without expanding a row
- [ ] **Open** tappable without overlapping text

---

## Related

- [`card_metric_cell.md`](card_metric_cell.md) — metric layout on the focused snapshot
- [`discover_header.md`](discover_header.md) — shared chrome above tabs
