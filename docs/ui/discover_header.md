# Discover header — UI spec

**Scope:** Top chrome shared across Discover and Saved (`_discovery_page` in `frontend/app.py`).  
**Authority:** [`north_star.md`](../north_star.md) (explore model v2.5).

---

## Vertical order (top → bottom)

```
┌─────────────────────────────────────────────┐
│ Stock Explorer                              │  1. Brand
│ Understand companies through five…          │  2. Tagline (`PRODUCT_TAGLINE`)
│ Not investment advice.                      │  3. Disclosure (permanent caption)
├─────────────────────────────────────────────┤
│ [ Discover ] [ Saved ] [ About ⌄ ]           │  4. Nav (+ About popover)
├─────────────────────────────────────────────┤
│ [ Search ticker or company name        ]     │  5. Persistent search (Discover list only)
├─────────────────────────────────────────────┤
│ [ Filters ▾ ]          All markets · All sectors │  6. Filters (Discover list only,
├─────────────────────────────────────────────┤     hidden while row 5 has a query)
│ 47 companies                                 │  7. Stats (list views; Discover shown
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
│ [ Discover ] [ Saved ] [ About ⌄ ]           │  4. Nav
│ [ ← Back to list ]                  3 saved │  6. Back row, Saved tab (`_render_back_row()`)
│ … the card …                                │
```

On Discover the same back row has no saved count: `[ ← Back to list ]` alone, nothing right-aligned.

| # | Block | Source | Notes |
|---|--------|--------|-------|
| 1 | Brand | `_render_brand_header()` | Product name only — no market name |
| 2 | Tagline | `_render_brand_header()` | One line under brand. List views only |
| 3 | Disclosure | `_render_brand_header()` | "Not investment advice." Permanent caption, not a one-time screen -- replaced the old first-run landing gate so it stays reachable every visit. List views only |
| 4 | Nav | `_render_bottom_nav()` | One flex row, three equal-width siblings, uniform gap: Discover / Saved (`st.button()`, primary/secondary by active tab -- not `st.segmented_control`, which misses a click on the tab already active) plus **About** (`st.popover`), dimmer label + chevron kept (signals "opens in place") |
| 5 | Persistent search | `_render_discover_search_box()` | **Discover list view only**: always-visible, global lookup across the full deck. A query replaces row 6 and the pool with results. Hidden while a card is focused. The only search entry point -- an earlier separate Search tab duplicated this and was removed |
| 6 | Filters | `_render_explore_filters()` | **Discover list only, while row 5 is empty**: **Filters** popover (market + sector + metric-preset pills); closed row shows `filter_scope_summary()`. Hidden while a card is focused or a query is active |
| 7 | Stats | `_render_discover_scope_stats()` / `_render_saved_scope_stats()` / `_render_back_row()` | Discover shows `{remaining} companies` (singular `{remaining} company` at 1), same form whether row 5 has a query or not -- counts whatever pool row 6/row 5 narrowed to; Saved shows `{saved} saved` plus its own `Clear saved` control (confirms in place); a focused card shows the back button alone on Discover, plus `{saved} saved` on Saved |

The sticky **Save** action renders **below** the card body on Discover -- not in the header. A second sticky action, **Not now**, was removed: it only ever returned to the list, same as `← Back to list`, and logged a `skip` interaction `filter_pool` never read.

---

## Filters popover

**Closed state:** `Filters` button + right-aligned summary. Not shown once a card is focused -- see the vertical-order table above.

**Open state:** Market selectbox, Sector selectbox (respects current market), then five metric-preset pills (`st.pills`, multi-select: High margin, Low debt, Growing revenue, Strong returns, Cash-safe -- `METRIC_PRESETS` in `frontend/explore_filters.py`). Market options come from live eligible cards (`market_filter_options()`), not the full static list. Changes return to the list via `_on_filter_change`.

**Pills, not numeric min/max (issue #13):** a prior numeric attempt was too tall on mobile, had confusing sentinel defaults, and crashed on Clear. Plain-language toggles avoid all three: compact, unselected already means "no filter," no Clear control needed -- tap a pill again to deselect. A card whose company_type has no corresponding metric passes through untouched.

**Removed:** "Surprise me worldwide" checkbox -- use **All markets** instead.

---

## What belongs in the header vs elsewhere

| Belongs in header | Belongs on card / About / filters |
|-----------------|--------------------------------------|
| Product name & tagline | Company name, ticker |
| Tab navigation | Sector headline + peer count |
| Active filter summary | Metric values and gloss |
| Scope stats line (`N companies`) | List row content: one type-aware lead metric per company (see [`discover_list.md`](discover_list.md)) |
| "Not investment advice" disclosure (permanent, every visit) | Focus card meta line: just the card's own listing venue (e.g. `FTSE 100`), same fallback Saved and a search result card use, no position |
| | What the app and its AI read do, data sourcing, market coverage (About) |

---

## Do not repeat in the header

- **Market name** when it is already clear from filters or card sector header.
- **Fundamentals as-of date** -- Saved list shows it once at tab top; card footer / About for Discover.
- **Filter state in stats line** -- scope is visible in filter summary, not restated in the count.

---

## About panel

One click, no nested `st.expander` -- tapping `⋯` then expanding "About" was one click too
many. Content, in order (`render_about_panel` in `frontend/overflow_menu.py`):

1. **Intro** (`MENU_ABOUT_INTRO`): what the app does, how the AI-written read is grounded
   in the card's own numbers -- describes the app, never its own tone ("plain-language
   read" was cut: don't say you're plain, be plain)
2. **Sourcing line**: `Sourced from Yahoo Finance, refreshed every two weeks. Data as of
   {snapshot}.` -- two plain sentences, no `·` (that's the chip separator, not prose)
3. **Metrics line** (`MENU_METRICS_LINE`): "Fundamentals per company, no substitutes"
4. **Markets line** (`markets_line`): which markets have cards, derived from live counts,
   empty when there are none -- no per-market count breakdown (dropped: internal pipeline
   detail, redundant with this line)
5. `business_summary`-missing caption, only when the export lacks it

`Clear saved` is on the Saved tab itself, next to the count it acts on -- not here.

---

## Anti-patterns

- Two full-width filter dropdowns on the card face (use popover).
- Moving filters below the card or into the About panel (filters must stay discoverable on Discover).
- Duplicating “Exploring: UK · Technology” in both filters and a second banner under stats.
- Global counters divorced from scope (e.g. `1/834` with no filter context).
- A sticky action that does nothing but return to the list -- `Not now` did exactly that,
  which is what `← Back to list` is already for.

---

## 480px smoke

- [ ] Brand + tagline + disclosure + nav visible without scrolling
- [ ] **About** inline with Discover / Saved (not on its own row), same width and gap,
      distinguished only by its dimmer label and chevron
- [ ] Discover list view: Filters row + stats + top of the list fit without horizontal scroll
- [ ] Discover focus view: Filters row is gone, back row shows just `[ ← Back to list ]`
      with no leftover gap where the Filters row or a saved count used to be
- [ ] Save reachable when a card is shown

---

## Related

- [`discover_list.md`](discover_list.md)
- [`saved_list.md`](saved_list.md)
- [`card_metric_cell.md`](card_metric_cell.md)
