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

Each row is a **bordered HTML field** (left-aligned name + ticker·sector) with an invisible full-row tap layer, plus its own `Remove` button in a second column outside that tap layer -- the one exception to "no visible button label," since it's a distinct action, not the row's own open gesture.

```
┌─────────────────────────────────────────────┐
│ 2 saved                          Clear saved │  ← tab-top stats + bulk action
├─────────────────────────────────────────────┤
│ Fundamentals as of June 8, 2026             │  ← once at tab top (list mode only)
├─────────────────────────────────────────────┤
│ ┌───────────────────────────────┐ ┌───────┐ │
│ │ Apple Inc.                    │ │Remove │ │  ← row tappable, Remove separate
│ │ AAPL · Technology             │ │       │ │
│ └───────────────────────────────┘ └───────┘ │
│ ┌───────────────────────────────┐ ┌───────┐ │
│ │ HSBC Holdings                 │ │Remove │ │
│ │ HSBA · Financial Services     │ │       │ │
│ └───────────────────────────────┘ └───────┘ │
└─────────────────────────────────────────────┘
```

**Line 1 (`.ss-row-title`):** company display name — bold, left-aligned.  
**Line 2 (`.ss-row-sub`):** `{ticker} · {sector}` via `saved_row_subtitle()` — caption colour, left-aligned.

---

## Layout rules

| Rule | Detail |
|------|--------|
| Row structure | `row_ui.render_removable_row_list`: `st.container(horizontal=True)` per row -- the row itself (HTML `.ss-row` + invisible overlay `st.button`) in one column, `Remove` in a second, outside the overlay's bounds so the two never fight for the same click |
| Bulk clear | `Clear saved` sits on the tab, next to `{N} saved` (`_render_saved_scope_stats`) -- not a shared menu. Confirms in place: swaps to "Clear all N saved companies?" with Cancel/Clear-all |
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
├─────────────────────────────────────────────┤
│ Remove from saved                           │  ← plain in-flow button, below the card
└─────────────────────────────────────────────┘
```

**Remove from saved:** a single click, no confirmation (unlike `Clear saved`, which does --
see Layout rules above). Returns to the list; the ticker reappears in the scoped Discover
pool. The list view's own per-row `Remove` button is the same one-click removal, reachable
without opening the card first.

Long headlines reuse the shared disclosure pattern — see [`disclosure_pattern.md`](disclosure_pattern.md).

---

## Anti-patterns (do not ship)

- **Auto-opening focus view** when the user has only one save (breaks “Back to list”).
- **Separate Open button column** -- wastes vertical space; the row itself is the open
  control. `Remove` is the one legitimate second column: a distinct action, not another way in.
- **Never put row copy inside a visible `st.button` label** — Streamlit centers it; use HTML + invisible tap layer.
- **Never repeat “As of …” on every row** — clutters the learning list.
- **Never use the full card or metric grid in list mode** — list is for picking, not reading numbers.
- **Never horizontal-scroll tables** of saved companies on mobile.
- **Never “Compare with another saved company”** — removed in UX recovery v2.5.

---

## 480px smoke

- [ ] No horizontal scroll on the list
- [ ] Company name + ticker · sector readable in each row
- [ ] Whole row tappable (bordered field); its own `Remove` button sits outside that tap
      target and never triggers the row's open action
- [ ] Tab open shows list first (1 or N saves)
- [ ] `Clear saved` and each row's `Remove` both reachable without scrolling on a short list

---

## Related

- [`design_system.md`](design_system.md) — row primitive tokens (radius, spacing, `.ss-row*`) this spec builds on
- [`discover_list.md`](discover_list.md): Discover's richer row variant (adds one lead metric), same tap mechanics
- [`card_metric_cell.md`](card_metric_cell.md) — metric layout on the focused snapshot
- [`discover_header.md`](discover_header.md) — shared chrome above tabs
