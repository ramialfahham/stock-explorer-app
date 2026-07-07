"""Tests for shared disclosure HTML helper."""

from __future__ import annotations

from disclosure_html import disclosure_html, is_truncated, preview_words  # noqa: E402


def test_preview_words_truncates() -> None:
    text = " ".join(f"word{i}" for i in range(20))
    preview = preview_words(text, max_words=12)
    assert preview.endswith("…")
    assert len(preview.split()) == 12


def test_disclosure_html_includes_toggle_labels() -> None:
    html_out = disclosure_html(
        "Short preview",
        "<p>Full body</p>",
        more_label="Read more",
        less_label="Show less",
    )
    assert "Read more" in html_out
    assert "Show less" in html_out
    assert "ss-disclosure" in html_out


def test_is_truncated() -> None:
    assert is_truncated("one two three", max_words=2) is True
    assert is_truncated("one two", max_words=2) is False
