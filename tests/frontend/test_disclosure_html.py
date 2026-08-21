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


def test_disclosure_html_omits_preview_paragraph_when_empty() -> None:
    """Callers whose own always-visible teaser lives outside this component (e.g. a
    metric's analogy line) pass preview="" — the <p> wrapper must not render at all,
    not render empty."""
    html_out = disclosure_html(
        "",
        "<p>Full body</p>",
        more_label="Read more",
        less_label="Show less",
    )
    assert "ss-disclosure-preview" not in html_out
    assert "Full body" in html_out


def test_disclosure_html_keeps_preview_paragraph_when_present() -> None:
    html_out = disclosure_html(
        "Short preview",
        "<p>Full body</p>",
        more_label="Read more",
        less_label="Show less",
    )
    assert 'class="ss-disclosure-preview"' in html_out
    assert "Short preview" in html_out
