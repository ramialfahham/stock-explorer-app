# Discover header — UI spec

**Scope:** Top chrome shared across Discover, Saved, and Search (`_discovery_page` in `frontend/app.py`).  
**Authority:** [`north_star.md`](../north_star.md) (explore model v2.5).

---

## Vertical order (top → bottom)

```
┌─────────────────────────────────────────────┐
│ Stock Explorer                              │  1. Brand
│ Understand companies through five…          │  2. Tagline (`PRODUCT_TAGLINE`)
│ Not investment advice.                      │  3. Disclosure (permanent caption)
├─────────────────────────────────────────────┤
│ [ Discover | Saved | Search ]          [⋯] │  4. Nav (+ overflow)
├─────────────────────────────────────────────┤
│ [ Search ticker or company name        ]     │  5. Persistent search (Discover list only)
├─────────────────────────────────────────────┤
│ [ Filters ▾ ]          All markets · All sectors │  6. Filters (Discover list only,
├─────────────────────────────────────────────┤     hidden while row 5 has a query)
│ 47 match your filters                        │  7. Stats (list views; Discover shown
├─────────────────────────────────────────────┤     here -- see per-tab notes below)
│ … tab body (card, list, or search) …        │
└─────────────────────────────────────────────┘
```

Rows 2, 3, 6 and 7 above depict the **list** views. Once a card is focused (Discover or
Saved), rows 2 and 3 are not rendered, rows 5 and 6 disappear entirely, and row 7 becomes
one row with just the back button (plus the saved count on Saved only -- see the table
below). Compacting to the brand alone on the card view keeps the header minimal. The
AI-written read (shown in full as a bullet list -- `disclosure_pattern.md`) can push later
content well down a long card; not a tracked success check (`north_star.md`).

```
│ Stock Explorer                              │  1. Brand only
│ [ Discover | Saved | Search ]          [⋯] │  4. Nav
│ [ ← Back to list ]                  3 saved │  6. Back row, Saved tab (`_render_back_row()`)
│ … the card …                                │
```

On Discover the same back row has no saved count: `[ ← Back to list ]` alone, nothing right-aligned.

| # | Block | Source | Notes |
|---|--------|--------|-------|
| 1 | Brand | `_render_brand_header()` | Product name only — no market name |
| 2 | Tagline | `_render_brand_header()` | One line under brand. List views only |
| 3 | Disclosure | `_render_brand_header()` | "Not investment advice." A permanent caption, not a one-time screen. Replaced the old first-run landing gate (removed) so the disclosure stays reachable every visit instead of appearing once and never again. List views only; the card view is never a visit's first screen |
| 4 | Nav | `_render_bottom_nav()` | Horizontal flex row: Discover / Saved / Search segmented control + **⋯** popover (same line on mobile; Streamlit `st.columns` stacks below 640px) |
| 5 | Persistent search | `_render_discover_search_box()` | **Discover list view only**: always-visible, same global lookup as the standalone Search tab. A query replaces rows 6-7 and the pool with results. Hidden while a card is focused |
| 6 | Filters | `_render_explore_filters()` | **Discover list view only, while row 5 is empty**: **Filters** popover (market + sector); closed row shows `filter_scope_summary()`. Hidden while a card is focused or a query is active |
| 7 | Stats | `_render_discover_scope_stats()` / `_render_saved_scope_stats()` / `_render_back_row()` | **Saved-tab-only saved count** (§6): Discover shows `{remaining} match your filters` (hidden during row 5's query); Saved shows `{saved} saved`; standalone Search shows nothing; a focused card shows the back button alone on Discover, plus `{saved} saved` on Saved |

Sticky **Save** / **Not now** actions render **below** the card body on Discover — not in the header.

---

## Filters popover

**Closed state:** `Filters` button + right-aligned summary. Not shown once a card is focused -- see the vertical-order table above.

**Open state:** Market selectbox, then Sector selectbox (respects current market). Options come from live eligible cards (`market_filter_options()`), not `MARKET_DISPLAY_NAMES`'s full static list -- a market with zero exported companies yet doesn't appear. Changes return to the list (clearing any open focus card) via `_on_filter_change`.

**Removed:** "Surprise me worldwide" checkbox -- use **All markets** instead.

**Phase 2 (deferred):** Metric range filters -- needs a mobile-friendly pattern (not a long scrollable popover with min/max widgets). Tracked in issue #13.

---

## What belongs in the header vs elsewhere

| Belongs in header | Belongs on card / overflow / filters |
|-----------------|--------------------------------------|
| Product name & tagline | Company name, ticker |
| Tab navigation | Sector headline + peer count |
| Active filter summary | Metric values and gloss |
| Scope stats line (`N match your filters`) | List row content: one type-aware lead metric per company (see [`discover_list.md`](discover_list.md)) |
| "Not investment advice" disclosure (permanent, every visit) | Focus card meta line: just the card's own listing venue (e.g. `FTSE 100`), same fallback Saved and Search use, no position |
| | Eligible pool breakdown (⋯ → About the data) |

---

## Do not repeat in the header

- **Market name** when it is already clear from filters or card sector header.
- **Full eligible-pool counts per market** -- keep in **⋯ → About the data** (`discover_pool_summary`, `eligible_breakdown_lines`).
- **Fundamentals as-of date** -- Saved list shows it once at tab top; card footer / overflow for Discover.
- **Filter state in stats line** -- scope is visible in filter summary; overflow "Right now" line may summarize.

---

## Overflow menu (⋯)

Popover content order:

1. **Right now** — tab-aware one-liner (`right_now_line`)
2. **Tip** — Discover / Saved / Search hint
3. Actions (clear saved -- confirms in place before wiping the list: swaps to a "Clear all
   N saved companies? This can't be undone." message with Cancel/Clear-all, no second popover)
4. **About the data** expander: refresh cadence, fundamentals-per-company gate, market breakdown; caption when `business_summary` export is missing

---

## Anti-patterns

- Two full-width filter dropdowns on the card face (use popover).
- Moving filters below the card or into the overflow menu (filters must stay discoverable on Discover).
- Duplicating “Exploring: UK · Technology” in both filters and a second banner under stats.
- Global counters divorced from scope (e.g. `1/834` with no filter context).

---

## 480px smoke

- [ ] Brand + tagline + disclosure + nav visible without scrolling
- [ ] **⋯** menu inline with Discover / Saved / Search (not on its own row)
- [ ] Discover list view: Filters row + stats + top of the list fit without horizontal scroll
- [ ] Discover focus view: Filters row is gone, back row shows just `[ ← Back to list ]`
      with no leftover gap where the Filters row or a saved count used to be
- [ ] Save / Not now reachable when a card is shown

---

## Related

- [`discover_list.md`](discover_list.md)
- [`saved_list.md`](saved_list.md)
- [`card_metric_cell.md`](card_metric_cell.md)
