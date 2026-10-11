"""HTML-safe text for the card and row builders."""

from __future__ import annotations

import html


def esc(value: object) -> str:
    return html.escape("" if value is None else str(value))
