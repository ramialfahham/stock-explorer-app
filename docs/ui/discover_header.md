# Discover header — UI spec

**Scope:** Top chrome shared across Discover, Saved, and Search (`_discovery_page` in `frontend/app.py`).  
**Authority:** [`north_star.md`](../north_star.md) (explore model v2.3).

---

## Vertical order (top → bottom)

```
┌─────────────────────────────────────────────┐
│ Stock Explorer                              │  1. Brand
│ Understand companies through five…          │  2. Tagline (`PRODUCT_TAGLINE`)
├─────────────────────────────────────────────┤
│ [ Discover | Saved | Search ]          [⋯] │  3. Nav (+ overflow)
├─────────────────────────────────────────────┤
│ [ Filters ▾ ]          All markets · All sectors │  4. Filters (Discover only)
├─────────────────────────────────────────────┤
│ 47 left · 3 saved                           │  5. Stats (context line)
├─────────────────────────────────────────────┤
│ … tab body (card, list, or search) …        │
└─────────────────────────────────────────────┘
```

| # | Block | Source | Notes |
|---|--------|--------|-------|
| 1 | Brand | `_render_brand_header()` | Product name only — no market name |
| 2 | Tagline | `_render_brand_header()` | One line under brand |
| 3 | Nav | `_render_bottom_nav()` | Horizontal flex row: Discover / Saved / Search segmented control + **⋯** popover (same line on mobile; Streamlit `st.columns` stacks below 640px) |
| 4 | Filters | `_render_explore_filters()` | **Discover tab only** — one **Filters** popover (market + sector inside); closed row shows `filter_scope_summary()` |
| 5 | Stats | `_render_scope_stats()` | Discover: `{remaining} left · {saved} saved`; Saved/Search: `{saved} saved` only |

Sticky **Save** / **Not now** actions render **below** the card body on Discover — not in the header.

---

## Filters popover

**Closed state:** `Filters` button + right-aligned summary (`All markets · All sectors` or scoped labels).

**Open state:** Market selectbox, then Sector selectbox (sector list respects current market). Changes reset walk queue via `_on_filter_change`.

**Removed:** “Surprise me worldwide” checkbox — use **All markets** in the popover instead.

**Phase 2 (deferred):** Metric range filters — needs a mobile-friendly pattern (not a long scrollable popover with min/max widgets). Track in #109.

---

## What belongs in the header vs elsewhere

| Belongs in header | Belongs on card / overflow / filters |
|-----------------|--------------------------------------|
| Product name & tagline | Company name, ticker |
| Tab navigation | Sector headline + peer count |
| Active filter summary | Metric values and gloss |
| Scope stats line (`N left`) | Walk position (`3 of 47` in walk UI) |
| | Eligible pool breakdown (⋯ → About the data) |
| | Market name on card meta (card shows market when needed) |

---

## Do not repeat in the header

- **Market name** when it is already clear from filters or card sector header.
- **Full eligible-pool counts per market** on the main face — keep in **⋯ → About the data** (`discover_pool_summary`, `eligible_breakdown_lines`).
- **Fundamentals as-of date** — Saved list shows it once at tab top; card footer / overflow for Discover context.
- **Filter state in stats line** — scope is visible in filter summary; overflow “Right now” line may summarize.

---

## Overflow menu (⋯)

Popover content order:

1. **Right now** — tab-aware one-liner (`right_now_line`)
2. **Tip** — Discover / Saved / Search hint
3. Actions (start over, clear saved, etc.)
4. **About the data** expander: refresh cadence (every two weeks), fundamentals-per-company gate, market breakdown; caption when `business_summary` export is missing

---

## Anti-patterns

- Two full-width filter dropdowns on the card face (use popover).
- Moving filters below the card or into the overflow menu (filters must stay discoverable on Discover).
- Duplicating “Exploring: UK · Technology” in both filters and a second banner under stats.
- Global queue counters divorced from scope (e.g. `1/834` with no filter context).

---

## 480px smoke

- [ ] Brand + tagline + nav visible without scrolling
- [ ] **⋯** menu inline with Discover / Saved / Search (not on its own row)
- [ ] Discover: Filters row + stats + top of card (or list) fit without horizontal scroll
- [ ] Save / Not now reachable when a card is shown

---

## Related

- [`saved_list.md`](saved_list.md)
- [`card_metric_cell.md`](card_metric_cell.md)
