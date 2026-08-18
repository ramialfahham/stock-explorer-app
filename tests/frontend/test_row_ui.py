"""Row primitive HTML helpers."""

from __future__ import annotations

from row_ui import build_row_html  # noqa: E402


def test_build_row_html_includes_title_and_subtitle() -> None:
    html = build_row_html("Apple Inc.", "AAPL · Technology")
    assert "ss-row-title" in html
    assert "ss-row-sub" in html
    assert "Apple Inc." in html
    assert "AAPL · Technology" in html


def test_build_row_html_escapes_special_characters() -> None:
    html = build_row_html("<script>alert(1)</script>", "A & B")
    assert "<script>" not in html
    assert "&lt;script&gt;" in html
    assert "A &amp; B" in html


def test_build_row_html_handles_none() -> None:
    html = build_row_html(None, None)
    assert "ss-row-title" in html
    assert "ss-row-sub" in html
