"""Tests for Saved tab headline parsing and HTML."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FRONTEND = ROOT / "frontend"
sys.path.insert(0, str(FRONTEND))

from saved_news import (  # noqa: E402
    NewsHeadline,
    headline_item_html,
    parse_yfinance_news,
    parse_yfinance_news_item,
)


def test_parse_yfinance_news_item_flat_shape() -> None:
    item = {
        "title": "Apple unveils new product line",
        "publisher": "Reuters",
        "link": "https://example.com/story",
    }
    headline = parse_yfinance_news_item(item)
    assert headline == NewsHeadline(
        title="Apple unveils new product line",
        publisher="Reuters",
        link="https://example.com/story",
    )


def test_parse_yfinance_news_item_nested_content_shape() -> None:
    item = {
        "content": {
            "title": "Nested headline title",
            "canonicalUrl": "https://example.com/nested",
            "provider": "Bloomberg",
        }
    }
    headline = parse_yfinance_news_item(item)
    assert headline is not None
    assert headline.title == "Nested headline title"
    assert headline.link == "https://example.com/nested"
    assert headline.publisher == "Bloomberg"


def test_parse_yfinance_news_skips_empty_and_limits() -> None:
    items = [
        {"title": "   "},
        {"title": "First"},
        {"title": "Second"},
        {"title": "Third"},
        {"title": "Fourth"},
    ]
    headlines = parse_yfinance_news(items, limit=3)
    assert [h.title for h in headlines] == ["First", "Second", "Third"]


def test_headline_item_html_uses_disclosure_for_long_title() -> None:
    long_title = " ".join(f"word{i}" for i in range(20))
    html_out = headline_item_html(
        NewsHeadline(title=long_title, publisher="Reuters", link="https://example.com"),
    )
    assert "Read full headline" in html_out
    assert "ss-disclosure" in html_out


def test_headline_item_html_short_title_no_disclosure() -> None:
    html_out = headline_item_html(
        NewsHeadline(title="Short title", publisher="Reuters", link=""),
    )
    assert "Read full headline" not in html_out
    assert "Short title" in html_out
