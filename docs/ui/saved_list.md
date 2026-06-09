# Saved list — UI spec

**Scope:** Saved tab list view (not focus view).  
**Authority:** [`north_star.md`](../north_star.md) (Saved = learning list + single focus).  
**Implementation:** `frontend/app.py` (`_render_saved_tab`), `frontend/styles.py` (`.ss-saved-list-*`).

---

## Primary job

User scans saved companies and opens **one** at a time to continue learning.

**Entry point:** Saved tab **always** opens to the list — even with one saved company. No auto-focus on tab load.

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
| Focus mode | `← Back to list` then **Recent headlines** (auto-load, up to 3) + Company Snapshot (same metrics as Discover) |
| Empty state | One `st.info` — no fake rows |
| Compare | **Removed** — no saved-company compare UI |

---

## Focus view — headlines (480px)

Headlines load automatically when the user opens a saved company (Yahoo Finance, session cache ~1 hour). Not shown on Discover.

```
┌─────────────────────────────────────────────┐
│ ← Back to list                              │
├─────────────────────────────────────────────┤
│ Apple Inc.                                  │
│ AAPL · Technology                           │
├─────────────────────────────────────────────┤
│ RECENT HEADLINES                            │
│ Apple reports… · Reuters                    │  ← short title = direct link
│ Long headline preview words…                │  ← long title = preview only
│ Read full headline                          │  ← gold toggle (not the preview)
├─────────────────────────────────────────────┤
│ … Company Snapshot card …                   │
└─────────────────────────────────────────────┘
```

Long headlines reuse the shared disclosure pattern — see [`disclosure_pattern.md`](disclosure_pattern.md).

---

- **Auto-opening focus view** when the user has only one save (breaks “Back to list”).
- **Never put 3+ text lines inside an `st.button` label** (Streamlit renders button labels poorly; multi-line hacks break on mobile).
- **Never repeat “As of …” on every row** — clutters the learning list.
- **Never use the full card or metric grid in list mode** — list is for picking, not reading numbers.
- **Never horizontal-scroll tables** of saved companies on mobile.
- **Never “Compare with another saved company”** — removed in UX recovery v2.5.

---

## 480px smoke

- [ ] No horizontal scroll on the list
- [ ] Company name + ticker · sector readable without expanding a row
- [ ] **Open** tappable without overlapping text
- [ ] Tab open shows list first (1 or N saves)

---

## Related

- [`card_metric_cell.md`](card_metric_cell.md) — metric layout on the focused snapshot
- [`discover_header.md`](discover_header.md) — shared chrome above tabs
