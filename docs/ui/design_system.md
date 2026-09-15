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
| `--ss-space-1` | `0.35rem` | Tight spacing (bottom-nav row gap, metric-label chip padding) |
| `--ss-space-2` | `0.55rem` | Row vertical padding, metric-label/verdict-badge chip padding |
| `--ss-space-3` | `0.75rem` | Section heading top margin (e.g. Saved-tab news heading) |
| `--ss-space-4` | `0.85rem` | Row horizontal padding, page gutter |
| `--ss-radius-control` | `0.5rem` (8px) | Buttons, icon-button trigger, metric-label chips, verdict badge |
| `--ss-radius-surface` | `0.75rem` (12px) | The card, Saved/Search rows |
| `--ss-row-title` | `0.9375rem` (15px) | List-row primary text only -- do not reuse `--ss-title` (reserved for in-card identity) or reuse this outside a row |
| `--ss-title` | `1.0625rem` (17px) | In-card identity: company name and ticker |
| `--ss-body` | `0.875rem` (14px) | Reading text: AI read, company summary, metric gloss, learn panel, menu body, alerts, nav buttons |
| `--ss-caption-size` | `0.8125rem` (13px) | Meta lines, freshness, filter summary, range-mark axis labels, row subtitles, toggles |
| `--ss-label` | `0.75rem` (12px) | Chips and small uppercase headings; the floor, nothing renders smaller |
| `--ss-value` | `1.5rem` (24px) | The metric value |

Every `font-size` in `frontend/styles.py` is one of these tokens; the brand wordmark and the
icon-button glyph are the two literal exceptions, and `tests/frontend/test_styles.py` refuses
any other. Which text is body and which is caption is decided by what the text is, not by
where it sits: an explanation is body even inside a small panel.

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

**Who uses this today:** Saved-list rows and Search results, via the plain row
(`row_ui.render_row_list`); Discover's list, via the richer variant that adds one lead
metric (`row_ui.render_rich_row_list`, see [`discover_list.md`](discover_list.md)).
**Who doesn't:** every focus view (Discover, Saved, Search): those render the full card,
not a row.

---

## Button variants

- **Base radius + color** (global, Slice 6a + 6b): every `st.button` gets `var(--ss-radius-control)`
  by default (`[data-testid="stButton"] button`), and every `button[kind="primary"]`/
  `button[kind="secondary"]` gets the same accent-gold / bordered-surface skin app-wide — one
  rule each, no per-surface scoping. Overflow's button and the Discover action bar render
  identically as a result.
- **Icon-button variant:** a marker div (`.ss-icon-btn-marker`) rendered immediately before
  the trigger, e.g. `st.popover("⋯")`. Styled via `:has()` rather than DOM position
  (`:last-child`) — position-based selectors silently jump to the wrong element if the row
  is ever reordered. Any future icon-only trigger opts in by dropping the same marker
  immediately before it.
- **Segmented control excluded.** The Discover/Saved/Search nav pills are a native Streamlit
  widget (`st.segmented_control`), not our HTML/button markup — it is deliberately outside
  this variant system and keeps its own theming.

---

## Popover trigger (Slice 6b)

Every `st.popover` trigger gets a base surface/border/`var(--ss-radius-control)` skin —
one rule, `[data-testid="stPopoverButton"]` — so a text-labeled trigger like **Filters** and
an icon-only one like **⋯** both read as the same control-tier chrome. The icon-button
variant above layers its own square sizing on top of this base; it doesn't replace it.

## Expander (Slice 6b)

`st.expander` gets the same surface-tier treatment as the card and rows —
`var(--ss-surface)` fill, `var(--ss-radius-surface)` corners, one rule,
`[data-testid="stExpander"]` — instead of default Streamlit chrome. Covers every instance
app-wide (currently: Overflow's "About the data", the card's one learn panel — "Understand
these numbers", Slice 6c — which consolidated what used to be a separate HTML `<details>`
plus a second "Practice with hypothetical numbers" expander into this single one); no
per-surface exceptions.

## Link button (Slice 6b)

`st.link_button` renders as `<a data-testid="stBaseLinkButton-{kind}">`, not
`<button kind="...">` — the button-variant rules above never reach it. All three kinds
Streamlit's `link_button` supports are covered so a future variant never silently ships
unstyled: `-primary` gets the same accent skin as `button[kind="primary"]`;
`-secondary`/`-tertiary` share the surface skin (this app has no separate visual tier for
"tertiary" anywhere else, so it doesn't invent one here). **Watch this testid if a future
Streamlit upgrade changes it** — it was already wrong once (a pre-existing footer-scoped
rule assumed `"stLinkButton"`, which never matched anything; fixed alongside this one).
Currently one consumer (the card footer's "Yahoo Finance" link, type `secondary`).

---

## Anti-patterns (do not ship)

- A new hardcoded radius or padding value on any button or row — use an existing token, or
  add one to the table above in the same PR.
- Reusing `--ss-title` for list-row text, or `--ss-row-title` for anything inside a card.
- Scoping a button/popover/expander/link-button skin to one surface instead of the shared
  global rule — the whole point of Slice 6b was closing exactly that kind of per-surface
  exception.
- Trusting a `data-testid` from memory instead of the live DOM — `stLinkButton` looked
  right and was wrong (`stBaseLinkButton-{kind}` is real); a rule against a stale testid
  ships silently dead.
- A position-based selector (`:last-child`, `:first-child`) for anything that could be
  reordered — use an explicit marker.
- A bare `:has(.ss-row)` to scope a row-only rule to "the stVerticalBlock containing a row" --
  `:has()` matches at any descendant depth, so it also matches the single big stVerticalBlock
  wrapping the *entire* list, not just each row's own small container. Confirmed live:
  Discover's pagination Previous/Next buttons, the first other `st.button()` ever rendered
  inside that same big wrapper, silently inherited the row-tap-target's `position: absolute;
  inset: 0` and stretched to the full list's height. Use
  `:has(> [data-testid="stElementContainer"] .ss-row)` (direct child) instead, which only
  matches each row's own container -- see `frontend/styles.py`'s row-primitive comment block and
  `tests/frontend/test_styles.py`'s guard for the full account.

---

## 480px smoke

- [ ] Saved row and Search row render with identical corner radius and padding
- [ ] Overflow trigger's icon-button radius matches other control-tier elements
- [ ] Overflow's "Clear saved" button renders with the same accent/surface skin as the
      Discover action bar
- [ ] Filters trigger and the ⋯ trigger render with the same surface/border chrome
- [ ] Both `st.expander` instances (Overflow "About the data", the card's one "Understand
      these numbers" learn panel) render bordered/filled, not default Streamlit grey
- [ ] Metric-label chips and the verdict badge render with the same control-tier radius
      as buttons/popover triggers
- [ ] The card footer's "Yahoo Finance" link renders with the same secondary-button skin
      as "Not now" on the sticky actions below it
- [ ] No new bare `border-radius:`/`padding:` literal introduced in touched sections of
      `styles.py` — every value traces to a token in the table above

---

## Related

- [`saved_list.md`](saved_list.md) — the row primitive's first consumer
- [`discover_header.md`](discover_header.md) — shared chrome above tabs
- [`card_metric_cell.md`](card_metric_cell.md) — the surface-tier component this system
  doesn't replace, just sits underneath
- [`disclosure_pattern.md`](disclosure_pattern.md)
