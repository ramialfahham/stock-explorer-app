"""Shared preview + Read more / Show less HTML (north_star disclosure pattern)."""

from __future__ import annotations

import html


def preview_words(text: str, *, max_words: int) -> str:
    words = text.split()
    if len(words) <= max_words:
        return text
    return " ".join(words[:max_words]) + "…"


def is_truncated(text: str, *, max_words: int) -> bool:
    return len(text.split()) > max_words


def disclosure_html(
    preview: str,
    full_body_html: str,
    *,
    more_label: str,
    less_label: str,
    wrap_class: str = "ss-disclosure-wrap",
    details_class: str = "ss-disclosure",
) -> str:
    """Preview is plain text (escaped by caller), or "" to omit the preview paragraph
    entirely — for callers whose own always-visible teaser lives outside this component.
    full_body_html is trusted inner HTML."""
    preview_html = f'<p class="ss-disclosure-preview">{preview}</p>' if preview else ""
    return (
        f'<div class="{wrap_class}">'
        f"{preview_html}"
        f'<details class="{details_class}">'
        f'<summary class="ss-disclosure-toggle">'
        f'<span class="ss-disclosure-more">{html.escape(more_label)}</span>'
        f'<span class="ss-disclosure-less">{html.escape(less_label)}</span>'
        f"</summary>"
        f"{full_body_html}"
        f"</details>"
        f"</div>"
    )
