# Design system — UI spec

**Scope:** Design tokens (spacing, radius, type scale) and shared row/button primitives —
the system underneath every other [`docs/ui/`](.) spec.
**Authority:** [`north_star.md`](../north_star.md) (dark-editorial visual language,
monochrome-only constraint, the Scan/Gloss/Deep progressive-disclosure model extended
conceptually to the component layer).
**Implementation:** `frontend/styles.py` (`:root` token block, row-primitive section,
button-variant section), `frontend/row_ui.py`.

---

## Why this doc exists

Every other `docs/ui/*.md` spec is scoped to one component (the card, a list, the header
chrome). None of them define what's underneath — the actual color/spacing/radius values and
the row/button building blocks those specs assume. This doc is that missing layer.

---

## Tokens

| Token | Value | Used by |
|---|---|---|
| `--ss-space-1` | `0.35rem` | Tight spacing (bottom-nav row gap) |
| `--ss-space-2` | `0.55rem` | Row vertical padding |
| `--ss-space-3` | `0.75rem` | Section heading top margin (e.g. Saved-tab news heading) |
| `--ss-space-4` | `0.85rem` | Row horizontal padding, page gutter |
| `--ss-radius-control` | `0.5rem` (8px) | Buttons, icon-button trigger |
| `--ss-radius-surface` | `0.75rem` (12px) | The card, Saved/Search rows |
| `--ss-row-title` | `0.85rem` | List-row primary text only — do not reuse `--ss-title` (reserved for in-card identity) or reuse this outside a row |

Two radius tiers, not one flat value: **control** (small interactive chrome — buttons,
icon triggers) and **surface** (content containers — the card, rows). A row and the card
share the surface tier; a button never does.

---

## Row primitive

```
┌─────────────────────────────────────────────┐
│ CI Fixture CI01                              │  ← .ss-row-title
│ CI01 · Technology                            │  ← .ss-row-sub
└─────────────────────────────────────────────┘
```

Bordered, filled (`var(--ss-surface)`), `var(--ss-radius-surface)` corners. The whole row is
the tap target — an invisible, full-row overlay `st.button` sits over the HTML row (never a
visible button label; Streamlit centers button text, so visible copy always comes from the
HTML). Implementation: `frontend/row_ui.py` — `build_row_html()` (pure) + `render_row_list()`
(Streamlit-calling), mirroring `card_ui.py`'s own pure/render split.

**Who uses this today:** Saved-list rows, Search results (both via `row_ui.render_row_list`).
**Who doesn't:** Discover and the Saved/Search focus view — those render the full card, not a
row.

---

## Button variants

- **Base radius** (global): every `st.button` gets `var(--ss-radius-control)` by default —
  one rule, `[data-testid="stButton"] button`. Colors/backgrounds are **not** set globally;
  each surface still skins its own buttons (fixed action bar's primary/secondary, the
  overflow icon trigger). Landing and Overflow-menu button reskinning beyond radius is 6b's
  job, not this doc's.
- **Icon-button variant:** a marker div (`.ss-icon-btn-marker`) rendered immediately before
  the trigger, e.g. `st.popover("⋯")`. Styled via `:has()` rather than DOM position
  (`:last-child`) — position-based selectors silently jump to the wrong element if the row
  is ever reordered. Any future icon-only trigger opts in by dropping the same marker
  immediately before it.
- **Segmented control excluded.** The Discover/Saved/Search nav pills are a native Streamlit
  widget (`st.segmented_control`), not our HTML/button markup — it is deliberately outside
  this variant system and keeps its own theming.

---

## Anti-patterns (do not ship)

- A new hardcoded radius or padding value on any button or row — use an existing token, or
  add one to the table above in the same PR.
- Reusing `--ss-title` for list-row text, or `--ss-row-title` for anything inside a card.
- Extending the primary/secondary button color skin to Overflow/Landing under this doc's
  authority — that's 6b.
- A position-based selector (`:last-child`, `:first-child`) for anything that could be
  reordered — use an explicit marker.

---

## 480px smoke

- [ ] Saved row and Search row render with identical corner radius and padding
- [ ] Overflow trigger's icon-button radius matches other control-tier elements
- [ ] No new bare `border-radius:`/`padding:` literal introduced in touched sections of
      `styles.py` — every value traces to a token in the table above

---

## Related

- [`saved_list.md`](saved_list.md) — the row primitive's first consumer
- [`discover_header.md`](discover_header.md) — shared chrome above tabs
- [`card_metric_cell.md`](card_metric_cell.md) — the surface-tier component this system
  doesn't replace, just sits underneath
- [`disclosure_pattern.md`](disclosure_pattern.md)
