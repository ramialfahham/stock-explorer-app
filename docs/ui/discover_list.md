# Discover list: UI spec

**Scope:** Discover tab list view (not focus view).
**Authority:** [`north_star.md`](../north_star.md) (explore model v2.5).
**Implementation:** `frontend/app.py` (`_render_discover_tab`), `frontend/row_ui.py`
(`build_rich_row_html`/`render_rich_row_list`, `.ss-row-rich*`, see
[`design_system.md`](design_system.md) for the base row-primitive tokens this builds on),
`frontend/card_copy.py` (`lead_metric_for_row`).

---

## Primary job

Filtering produces a visible result. The reader scans a list of every company matching the
current market/sector filter, then opens **one** at a time to learn more.

**Entry point:** Discover tab **always** opens to the list for the current filter scope, even
when only one company matches. No auto-focus on tab load, matching Saved's own rule.

---

## Why this list is richer than Saved's or Search's

Saved and Search rows are picking rows, title and subtitle only, deliberately no numbers
(`saved_list.md`'s own anti-pattern: "list is for picking, not reading numbers"). Discover's
filter narrows a large, unfamiliar pool (up to hundreds of companies), so the row carries one
extra signal that helps a reader decide which company to open first: one glance metric.

A verdict dot used to sit alongside the metric here; removed after it stayed visually
misaligned even past its known emoji-glyph-metrics cause being fixed, see
`frontend/row_ui.py`'s `build_rich_row_html` docstring.

**The lead metric is not a free choice per row.** It's exactly the one metric that is a CORE,
verdict-deciding axis for that company type's own verdict rule in `scripts/assessment_rules.py`,
not merely any input of any weight to it:

| Company type | Lead metric | Why this one |
|---|---|---|
| Operating | Operating margin (TTM) | One of the three core axes (`net_debt_to_ebitda`, `ebit_margin_pct`, `fcf_margin_pct`) that alone decide red/green in `_verdict_operating`; `statement_roe_pct` was considered but is only a supporting axis there, which "can break a tie but never rescue a red flag" (that function's own comment) |
| Financial | Return on equity | Co-primary in `_verdict_financial`: checked first, alone can force red, and required good for green |
| Pre-revenue | Cash runway (months) | The central axis of `_verdict_pre_revenue`'s "survival story" framing |

A row with no value for its type's lead metric still renders, just without that slot. Never a
blank space or an invented number (`lead_metric_for_row` returns `None`, not a placeholder, when
the value is missing).

---

## List row wireframe (480px)

```
┌─────────────────────────────────────────────┐
│ 924 match your filters · 0 saved             │  ← stats line (header, not this spec)
├─────────────────────────────────────────────┤
│ ┌─────────────────────────────────────────┐ │
│ │ Diageo                            31.4% │ │  ← whole row tappable
│ │ DGE · Consumer Defensive  Operating m...│ │
│ └─────────────────────────────────────────┘ │
│ ┌─────────────────────────────────────────┐ │
│ │ Unilever                          28.9% │ │
│ │ ULVR · Consumer Defensive Operating m...│ │
│ └─────────────────────────────────────────┘ │
│         ... (up to DISCOVER_PAGE_SIZE) ...   │
│                                               │
│    [ Previous ]   Page 1 of 31   [ Next ]    │  ← hidden entirely on a
│                                               │     pool that fits one page
└─────────────────────────────────────────────┘
```

**Left (`.ss-row-main`):** title is the company display name (`.ss-row-title`), subtitle is
`{ticker} · {sector}` via `saved_row_subtitle()` (`.ss-row-sub`), the same function Saved and
Search already use, so the two-line identity reads identically everywhere in the app.
**Right (`.ss-row-side`):** the lead metric's value and label stacked (`.ss-row-metric-value` /
`.ss-row-metric-label`). Absent entirely when the card has no value for its type's lead metric;
the row degrades gracefully, never to a blank box.
**Footer (pagination):** Previous/Next either side of a "Page N of M" label
(`.ss-discover-page-label`), below the last row on the page. Disabled at the first/last page;
hidden entirely, not just disabled, when the whole filtered pool already fits on one page.

---

## Layout rules

| Rule | Detail |
|------|--------|
| Row structure | Same tap mechanics as the plain row (`st.container` plus an invisible overlay `st.button`), different HTML via `build_rich_row_html`, see `design_system.md`'s row primitive |
| Ordering | Alphabetical by company name, not the retired walk's round-robin/skip order: a list should be stable and re-findable |
| Pagination | `DISCOVER_PAGE_SIZE` (30) rows per page, Previous/Next below the list, hidden entirely (not just disabled) when the filtered pool already fits on one page. Mounting the full ~923-row pool unconditionally (~931 tap-target buttons, ~20,600 DOM nodes) measures at ~2.4s before Streamlit even registers a click. Changing market/sector resets to page 1; the page index is clamped to the pool's current bounds regardless of why it shrank |
| Focus mode | `← Back to list`, then the Company Snapshot, the same `render_stock_card` Saved and Search already use, unchanged |
| Sticky actions | Save / Not now render on the **focus card only** (matching where they already lived), not on list rows. A second per-row tap target would break "the row itself is the control," the same anti-pattern `saved_list.md` already rejects |
| Empty state | One `st.info`, no fake rows |
| Not now | Recorded as an interaction, with **no visible effect on the list**. There is no walk position left to deprioritize it from; see `north_star.md`'s "Not now (Skip)" section |

---

## Anti-patterns (do not ship)

- **A second tap target per row** (a save icon, a checkbox). Save and Not now live on the
  focus card, matching Saved's own precedent.
- **The full metric grid in list mode.** One lead metric only; list is for picking, the focus
  card is for reading numbers.
- **Reviving the retired walk's ordering** for the list. Round-robin/skip-deprioritization is
  session-interaction-dependent, which is confusing in something a reader re-scans, not
  something they walk through once.
- **A placeholder or invented number when the lead metric is missing.** Omit the slot, exactly
  like a metric with no value is omitted from the full card (`metrics_for_card`).
- **Auto-opening focus view** when only one company matches the filter. Breaks "Back to list,"
  the same rule `saved_list.md` states for Saved.

---

## 480px smoke

- [ ] No horizontal scroll on the list, even with the metric column present
- [ ] Company name + ticker · sector readable on the left, metric readable on the right,
      neither column crowding the other
- [ ] Whole row tappable, no tiny separate control
- [ ] Filters row + stats + top of the list fit without horizontal scroll
- [ ] Save / Not now reachable when a card is focused
- [ ] Previous/Next reachable without horizontal scroll, disabled state visibly distinct from
      enabled

---

## Related

- [`design_system.md`](design_system.md): row primitive tokens this spec builds on
- [`saved_list.md`](saved_list.md): the plain row variant and the "row is the control" precedent this spec follows
- [`card_metric_cell.md`](card_metric_cell.md): metric layout on the focused snapshot
- [`discover_header.md`](discover_header.md): shared chrome above tabs
