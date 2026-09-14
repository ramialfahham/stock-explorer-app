"""Shared row primitive — bordered, tappable HTML row + invisible overlay button.

Used by Saved-list and Search results (Slice 6a). Mirrors card_ui.py's split: a pure
build_*_html() function plus a render_*() function that calls Streamlit. See
docs/ui/design_system.md for the token/primitive spec this implements.
"""

from __future__ import annotations

import html
from typing import Callable, TypeVar

import streamlit as st

_T = TypeVar("_T")


def _esc(value: object) -> str:
    return html.escape("" if value is None else str(value))


def build_row_html(title: str, subtitle: str) -> str:
    return (
        f'<div class="ss-row">'
        f'<p class="ss-row-title">{_esc(title)}</p>'
        f'<p class="ss-row-sub">{_esc(subtitle)}</p>'
        f"</div>"
    )


def build_rich_row_html(
    title: str,
    subtitle: str,
    metric: tuple[str, str] | None,
) -> str:
    """A row with one lead metric alongside title/subtitle.

    Keeps the base `ss-row` class so it inherits every tap-target and hover rule the plain
    row already has (see styles.py); only the internal layout differs. `metric` is optional:
    a card with no value for its type's lead metric still renders the row, just without it.

    Previously also carried a health-verdict dot; removed by owner instruction
    after it stayed visually misaligned even once its known emoji-glyph-metrics cause was
    fixed.
    """
    metric_html = ""
    if metric:
        label, value = metric
        metric_html = (
            f'<span class="ss-row-metric">'
            f'<span class="ss-row-metric-value">{_esc(value)}</span>'
            f'<span class="ss-row-metric-label">{_esc(label)}</span>'
            f"</span>"
        )
    side_html = f'<div class="ss-row-side">{metric_html}</div>' if metric_html else ""
    return (
        f'<div class="ss-row ss-row-rich">'
        f'<div class="ss-row-main">'
        f'<p class="ss-row-title">{_esc(title)}</p>'
        f'<p class="ss-row-sub">{_esc(subtitle)}</p>'
        f"</div>"
        f"{side_html}"
        f"</div>"
    )


def render_row_list(
    items: list[_T],
    *,
    key_prefix: str,
    on_select: Callable[[_T], None],
    title_fn: Callable[[_T], str],
    subtitle_fn: Callable[[_T], str],
    row_key_fn: Callable[[_T], str],
) -> None:
    """Render a list of bordered, tappable rows.

    Each row's whole surface is the tap target: HTML row content plus an invisible,
    full-row overlay st.button (the button's own label is never shown — Streamlit centers
    button text, so visible row copy always comes from the HTML, never the button label).
    """
    _render_tappable_rows(
        items,
        key_prefix=key_prefix,
        on_select=on_select,
        title_fn=title_fn,
        row_key_fn=row_key_fn,
        html_fn=lambda item: build_row_html(title_fn(item), subtitle_fn(item)),
    )


def render_rich_row_list(
    items: list[_T],
    *,
    key_prefix: str,
    on_select: Callable[[_T], None],
    title_fn: Callable[[_T], str],
    subtitle_fn: Callable[[_T], str],
    metric_fn: Callable[[_T], tuple[str, str] | None],
    row_key_fn: Callable[[_T], str],
) -> None:
    """Same tap-target mechanics as `render_row_list`, using the richer row instead."""
    _render_tappable_rows(
        items,
        key_prefix=key_prefix,
        on_select=on_select,
        title_fn=title_fn,
        row_key_fn=row_key_fn,
        html_fn=lambda item: build_rich_row_html(
            title_fn(item), subtitle_fn(item), metric_fn(item)
        ),
    )


def _render_tappable_rows(
    items: list[_T],
    *,
    key_prefix: str,
    on_select: Callable[[_T], None],
    title_fn: Callable[[_T], str],
    row_key_fn: Callable[[_T], str],
    html_fn: Callable[[_T], str],
) -> None:
    st.markdown('<div class="ss-row-group" aria-hidden="true"></div>', unsafe_allow_html=True)
    for item in items:
        with st.container():
            st.markdown(html_fn(item), unsafe_allow_html=True)
            if st.button(
                title_fn(item),
                key=f"{key_prefix}_{row_key_fn(item)}",
                use_container_width=True,
                type="secondary",
            ):
                on_select(item)
                st.rerun()
