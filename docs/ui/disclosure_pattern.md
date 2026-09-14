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
| Learn panel metric bodies | Shipped | Read more / Show less |
| Sector gloss long copy | Backlog | — |

**The AI-written read does NOT use this pattern.** It renders as an always-visible bullet
list (`_bullets_html` in `frontend/card_ui.py`, one `<li>` per sentence, `.ss-ai-read-list` /
`.ss-verdict-fallback-list` in `frontend/styles.py`) -- no preview, no toggle, nothing folded.
Reversed from an earlier fold (owner decision, 2026-09-14): the fold traded full legibility
for screen space, and the owner judged the wall-of-text-behind-a-tap tradeoff wrong the other
way.

**Company description (Discover/Saved card) uses this pattern directly on the card face**
(`frontend/card_ui.py`'s `_company_summary_html`) — a real reversal of the Slice 6c
consolidation, made deliberately after the owner found the consolidated version's UX bad in
practice: the full text used to live inside the card's one learn panel
(`st.expander("Understand these numbers")`) as an "About this company" section, reachable
only after opening the panel and scrolling past every metric's explanation. It no longer
lives in the learn panel at all — the toggle sits inline, right where the truncated preview
ends, so reading the rest of the description needs no navigation and no scrolling past
unrelated content.

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
