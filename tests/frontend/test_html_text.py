"""esc is the one HTML-safe text helper behind the card and row builders."""

from __future__ import annotations

from html_text import esc


def test_esc_escapes_markup_and_quotes() -> None:
    assert esc('<b>"A" & B</b>') == "&lt;b&gt;&quot;A&quot; &amp; B&lt;/b&gt;"


def test_esc_turns_none_into_an_empty_string_and_other_values_into_text() -> None:
    assert esc(None) == ""
    assert esc(12.5) == "12.5"
