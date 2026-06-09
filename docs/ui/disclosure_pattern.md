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
| Company description (Discover/Saved card) | Shipped | Read full description / Show less |
| Saved tab headlines | Shipped | Read full headline / Show less |
| Learn panel metric bodies | Backlog | — |
| Sector gloss long copy | Backlog | — |

Company description keeps legacy `.ss-company-about-*` classes **and** `.ss-disclosure-*` for shared styling.

---

## Anti-patterns

- Making the preview paragraph itself the click target
- Putting disclosure inside a scrollable popover (use full-width card or focus view instead)
- Writing widget-backed `session_state` after Streamlit widgets mount (see #117 revert)

---

## Related

- [`saved_list.md`](saved_list.md) — headline wireframe on focus view
- Issue #112
