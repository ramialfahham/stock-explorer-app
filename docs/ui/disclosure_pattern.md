# Disclosure pattern — Read more / Show less

**Scope:** Reusable preview + expand interaction for long copy on cards and Saved headlines.  
**Implementation:** `frontend/disclosure_html.py`, `.ss-disclosure-*` in `frontend/styles.py`.

---

## Pattern

| Element | Rule |
|---------|------|
| Preview | Static text — **not** clickable |
| Toggle | Gold **Read …** link on `<summary>` only |
| Expanded | Full content; **Show less** collapses |
| CSS | `.ss-disclosure-wrap`, `.ss-disclosure`, `.ss-disclosure-more` / `-less` |

Helper: `disclosure_html(preview, full_body_html, more_label=..., less_label=...)`.

---

## Placements

| Surface | Status | Labels |
|---------|--------|--------|
| Saved tab headlines | Shipped | Read full headline / Show less |
| Company description (card face) | Shipped | Read more / Show less |
| AI-written read (card face) | Shipped | Read more / Show less |
| Learn panel metric bodies | Shipped | Read more / Show less |
| Sector gloss long copy | Backlog | — |

**Company description (Discover/Saved card) uses this pattern directly on the card face**
(`frontend/card_ui.py`'s `_company_summary_html`) — a real reversal of the Slice 6c
consolidation, made deliberately after the owner found the consolidated version's UX bad in
practice: the full text used to live inside the card's one learn panel
(`st.expander("Understand these numbers")`) as an "About this company" section, reachable
only after opening the panel and scrolling past every metric's explanation. It no longer
lives in the learn panel at all — the toggle sits inline, right where the truncated preview
ends, so reading the rest of the description needs no navigation and no scrolling past
unrelated content.

**The AI-written read folds to its first lines** (`_health_block_html`, preview length
`AI_READ_PREVIEW_WORDS` in `frontend/card_copy.py`, about three lines at 375px) so the
verdict badge, its first reasons and the first metric value share one phone screen. The
badge and the block label stay outside the toggle; a read short enough to fit renders
plain. The financial caveat is not in this block at all: it sits under the metric stack on
every financial-type card, present whether or not the block renders. Owner composition call after the type scale pushed the first metric
below the fold on long cards.

**Learn panel metric bodies also use this pattern now** (`_metric_learn_blocks()` in
`frontend/card_ui.py`) — each metric's full explanation gets its own toggle instead of every
metric's paragraph rendering concatenated and always-visible once the panel opens. The
label and analogy line stay unconditionally visible per metric (the scannable part);
only the longer technical paragraph sits behind Read more. Native `<details>` are
independent by default, so more than one metric can stay expanded at once if a reader wants
to compare a couple — no extra state needed for that.

---

## Anti-patterns

- Making the preview paragraph itself the click target
- Putting disclosure inside a scrollable popover (use full-width card or focus view instead)
- Writing widget-backed `session_state` after Streamlit widgets mount (see #117 revert)

---

## Related

- [`saved_list.md`](saved_list.md) — headline wireframe on focus view
- Issue #112
