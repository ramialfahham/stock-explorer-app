"""Row primitive HTML helpers."""

from __future__ import annotations

from row_ui import build_rich_row_html, build_row_html  # noqa: E402


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


def test_build_rich_row_html_includes_verdict_and_metric() -> None:
    html = build_rich_row_html(
        "Diageo", "DGE · Consumer Defensive", ("green", "Healthy"), ("Return on equity", "31.4%")
    )
    assert "ss-row-verdict" in html
    assert "ss-row-verdict--green" in html
    assert 'aria-label="Healthy"' in html
    assert "ss-row-metric-value" in html
    assert "31.4%" in html
    assert "ss-row-metric-label" in html
    assert "Return on equity" in html


def test_build_rich_row_html_renders_a_dot_not_an_emoji_character() -> None:
    """A colored-circle emoji's internal vertical metrics vary by platform/font, which is
    what made the list misalign row to row despite pixel-identical layout. The verdict is
    a plain CSS-drawn circle now, with no glyph content, so nothing to misalign."""
    html = build_rich_row_html(
        "Diageo", "DGE · Consumer Defensive", ("yellow", "Mixed"), None
    )
    assert "🟢" not in html and "🟡" not in html and "🔴" not in html
    assert "ss-row-verdict--yellow" in html


def test_build_rich_row_html_degrades_without_a_metric() -> None:
    """A row with no lead metric (missing value, or a type with none defined) still
    renders the verdict and title/subtitle, never a blank slot or an invented number."""
    html = build_rich_row_html("Diageo", "DGE · Consumer Defensive", ("green", "Healthy"), None)
    assert "ss-row-verdict" in html
    assert "ss-row-metric" not in html
    assert "Diageo" in html


def test_build_rich_row_html_degrades_without_a_verdict() -> None:
    """A card with no assessment yet (health_verdict_token returns None) still renders the
    row with its metric, just without the verdict dot slot."""
    html = build_rich_row_html(
        "Diageo", "DGE · Consumer Defensive", None, ("Return on equity", "31.4%")
    )
    assert "ss-row-verdict" not in html
    assert "31.4%" in html


def test_build_rich_row_html_keeps_the_base_row_class() -> None:
    """Must inherit every tap-target and hover rule the plain row already has (styles.py):
    losing the base `ss-row` class would silently break tap targeting for this variant."""
    html = build_rich_row_html("Diageo", "DGE · Consumer Defensive", ("green", "Healthy"), None)
    assert 'class="ss-row ss-row-rich"' in html


def test_build_rich_row_html_escapes_special_characters() -> None:
    html = build_rich_row_html(
        "<script>alert(1)</script>", "A & B", ("green", "<b>Healthy</b>"), ("<b>label</b>", "1 & 2")
    )
    assert "<script>" not in html
    assert "&lt;script&gt;" in html
    assert "&lt;b&gt;label&lt;/b&gt;" in html
    assert "1 &amp; 2" in html
    assert "&lt;b&gt;Healthy&lt;/b&gt;" in html
