"""Tests for Saved tab headline parsing and HTML."""

from __future__ import annotations

import sys
import types

import saved_news
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
            "provider": {
                "displayName": "Bloomberg",
                "url": "https://www.bloomberg.com/",
                "sourceId": "bloomberg",
            },
            "canonicalUrl": {
                "url": "https://finance.yahoo.com/news/nested-headline-title-123.html",
                "site": "finance",
            },
            "clickThroughUrl": {
                "url": "https://finance.yahoo.com/news/nested-headline-title-123.html",
                "site": "finance",
            },
        }
    }
    headline = parse_yfinance_news_item(item)
    assert headline is not None
    assert headline.title == "Nested headline title"
    assert headline.link == "https://finance.yahoo.com/news/nested-headline-title-123.html"
    assert headline.publisher == "Bloomberg"
    assert "{" not in headline.publisher


def test_parse_yfinance_news_item_does_not_stringify_provider_dict() -> None:
    item = {
        "content": {
            "title": "Story",
            "provider": {
                "displayName": "MT Newswires",
                "url": "https://www.mtnewswires.com/",
            },
            "clickThroughUrl": {
                "url": "https://finance.yahoo.com/markets/stocks/articles/story-123.html",
            },
        }
    }
    headline = parse_yfinance_news_item(item)
    assert headline is not None
    assert headline.publisher == "MT Newswires"
    assert headline.link.startswith("https://finance.yahoo.com/")


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


def test_fetch_news_imports_yfinance_on_call_and_returns_the_raw_items(monkeypatch) -> None:
    """yfinance is imported inside _fetch_news, not with the app. This runs the real body
    against a fake yfinance in sys.modules, so a deleted or misspelt in-function import
    fails here instead of being swallowed by fetch_saved_news's except into "Could not
    load headlines"."""
    seen: list[str] = []

    class _Ticker:
        def __init__(self, symbol: str) -> None:
            seen.append(symbol)
            self.news = [{"id": str(i)} for i in range(10)]

    fake = types.ModuleType("yfinance")
    fake.Ticker = _Ticker
    monkeypatch.setitem(sys.modules, "yfinance", fake)
    saved_news._fetch_news.clear()

    items = saved_news._fetch_news("AAPL")
    assert seen == ["AAPL"]
    assert len(items) == saved_news._MAX_HEADLINES * 2
