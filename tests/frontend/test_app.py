"""Tests for app.py's pure HTML-building helpers."""

from __future__ import annotations

from app import brand_header_html
from brand import PRODUCT_NAME, PRODUCT_TAGLINE


def test_brand_header_html_includes_the_disclaimer() -> None:
    """The header is the only place this renders now that the landing screen is gone."""
    html = brand_header_html()
    assert PRODUCT_NAME in html
    assert PRODUCT_TAGLINE in html
    assert "Not investment advice." in html


def test_brand_header_html_orders_name_then_tagline_then_disclaimer() -> None:
    html = brand_header_html()
    name_pos = html.index(PRODUCT_NAME)
    tagline_pos = html.index(PRODUCT_TAGLINE)
    disclaimer_pos = html.index("Not investment advice.")
    assert name_pos < tagline_pos < disclaimer_pos
