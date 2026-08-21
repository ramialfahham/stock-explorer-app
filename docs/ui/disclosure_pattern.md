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
| Learn panel metric bodies | Backlog | — |
| Sector gloss long copy | Backlog | — |

**Company description (Discover/Saved card) no longer uses this pattern (Slice 6c).** The
card face shows only the word-limited preview (`frontend/card_ui.py`'s `_company_summary_html`);
the full text, when the preview is truncated, moved into the card's one learn panel
(`st.expander("Understand these numbers")` — see [`design_system.md`](design_system.md)'s
Expander primitive) as an "About this company" section, not its own toggle. This was a
deliberate consolidation, not drift — the "approved mock" called for one disclosure per card,
and a second small toggle for the description would have left two.

**Renders LAST within the panel, not first** (`build_learn_panel_body_html()` in
`frontend/card_ui.py`) — the panel is labeled "Understand these numbers," so a control
opened for that reason should lead with numbers content (benchmark compare, then metric
definitions), not unrelated company prose. Keep any future section added to this panel
ordered the same way: numbers content before company description.

---

## Anti-patterns

- Making the preview paragraph itself the click target
- Putting disclosure inside a scrollable popover (use full-width card or focus view instead)
- Writing widget-backed `session_state` after Streamlit widgets mount (see #117 revert)

---

## Related

- [`saved_list.md`](saved_list.md) — headline wireframe on focus view
- Issue #112
