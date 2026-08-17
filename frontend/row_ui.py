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
    st.markdown('<div class="ss-row-group" aria-hidden="true"></div>', unsafe_allow_html=True)
    for item in items:
        title = title_fn(item)
        with st.container():
            st.markdown(
                build_row_html(title, subtitle_fn(item)),
                unsafe_allow_html=True,
            )
            if st.button(
                title,
                key=f"{key_prefix}_{row_key_fn(item)}",
                use_container_width=True,
                type="secondary",
            ):
                on_select(item)
                st.rerun()
