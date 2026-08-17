# Saved list — UI spec

**Scope:** Saved tab list view (not focus view).  
**Authority:** [`north_star.md`](../north_star.md) (Saved = learning list + single focus).  
**Implementation:** `frontend/app.py` (`_render_saved_tab`), `frontend/row_ui.py` (`.ss-row*` — see [`design_system.md`](design_system.md) for the token/primitive spec).

---

## Primary job

User scans saved companies and opens **one** at a time to continue learning.

**Entry point:** Saved tab **always** opens to the list — even with one saved company. No auto-focus on tab load.

---

## List row wireframe (480px)

Each row is a **bordered HTML field** (left-aligned name + ticker·sector) with an invisible full-row tap layer. No separate **Open** control and **no visible button label** (Streamlit centers button text).

```
┌─────────────────────────────────────────────┐
│ Fundamentals as of June 8, 2026             │  ← once at tab top (list mode only)
├─────────────────────────────────────────────┤
│ ┌─────────────────────────────────────────┐ │
│ │ Apple Inc.                              │ │  ← whole row tappable
│ │ AAPL · Technology                       │ │
│ └─────────────────────────────────────────┘ │
│ ┌─────────────────────────────────────────┐ │
│ │ HSBC Holdings                           │ │
│ │ HSBA · Financial Services               │ │
│ └─────────────────────────────────────────┘ │
└─────────────────────────────────────────────┘
```

**Line 1 (`.ss-row-title`):** company display name — bold, left-aligned.  
**Line 2 (`.ss-row-sub`):** `{ticker} · {sector}` via `saved_row_subtitle()` — caption colour, left-aligned.

---

## Layout rules

| Rule | Detail |
|------|--------|
| Row structure | `st.container` per row: HTML `.ss-row` + invisible overlay `st.button` (company name for screen readers only) |
| Freshness | **Tab-level once** — `Fundamentals as of {date}` above the list; **never per row** |
| Focus mode | `← Back to list` then **Recent headlines** (auto-load, up to 3) then Company Snapshot — **no duplicate name/sector row** above the card |
| Empty state | One `st.info` — no fake rows |
| Compare | **Removed** — no saved-company compare UI |

---

## Focus view — headlines (480px)

Headlines load automatically when the user opens a saved company (Yahoo Finance, session cache ~1 hour). Not shown on Discover.

```
┌─────────────────────────────────────────────┐
│ ← Back to list                              │
├─────────────────────────────────────────────┤
│ RECENT HEADLINES                            │
│ Short title · Reuters          (Yahoo link) │
├─────────────────────────────────────────────┤
│ Airbus · AIR.PA                             │  ← card identity (once)
│ Industrials (8 companies)                   │
│ … summary, metrics …                        │
└─────────────────────────────────────────────┘
```

Long headlines reuse the shared disclosure pattern — see [`disclosure_pattern.md`](disclosure_pattern.md).

---

## Anti-patterns (do not ship)

- **Auto-opening focus view** when the user has only one save (breaks “Back to list”).
- **Separate Open button column** — wastes vertical space; row itself is the control.
- **Never put row copy inside a visible `st.button` label** — Streamlit centers it; use HTML + invisible tap layer.
- **Never repeat “As of …” on every row** — clutters the learning list.
- **Never use the full card or metric grid in list mode** — list is for picking, not reading numbers.
- **Never horizontal-scroll tables** of saved companies on mobile.
- **Never “Compare with another saved company”** — removed in UX recovery v2.5.

---

## 480px smoke

- [ ] No horizontal scroll on the list
- [ ] Company name + ticker · sector readable in each row
- [ ] Whole row tappable (bordered field), no tiny Open button
- [ ] Tab open shows list first (1 or N saves)

---

## Related

- [`design_system.md`](design_system.md) — row primitive tokens (radius, spacing, `.ss-row*`) this spec builds on
- [`card_metric_cell.md`](card_metric_cell.md) — metric layout on the focused snapshot
- [`discover_header.md`](discover_header.md) — shared chrome above tabs
