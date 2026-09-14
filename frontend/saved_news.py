"""On-demand news headlines for saved companies (Saved tab only)."""

from __future__ import annotations

import html
from dataclasses import dataclass

import streamlit as st

from disclosure_html import disclosure_html, is_truncated, preview_words
from live_quote import yfinance_symbol

_SESSION_KEY = "_saved_news"
_MAX_HEADLINES = 3
_HEADLINE_PREVIEW_WORDS = 12


@dataclass(frozen=True)
class NewsHeadline:
    title: str
    publisher: str
    link: str


@dataclass(frozen=True)
class NewsError:
    message: str


def _cache_key(card: dict) -> str:
    return f"{card.get('market_code')}:{card.get('ticker')}"


def _store() -> dict[str, list[NewsHeadline] | NewsError]:
    return st.session_state.setdefault(_SESSION_KEY, {})


def _url_from_field(raw: object) -> str:
    if isinstance(raw, dict):
        return str(raw.get("url") or "").strip()
    if raw:
        return str(raw).strip()
    return ""


def _publisher_label(raw: object) -> str:
    if isinstance(raw, dict):
        return str(raw.get("displayName") or raw.get("name") or "Source").strip()
    if raw:
        text = str(raw).strip()
        if text.startswith("{") and "displayName" in text:
            return "Source"
        return text
    return "Source"


def _article_url(item: dict, content: dict) -> str:
    candidates = [
        _url_from_field(content.get("clickThroughUrl")),
        _url_from_field(content.get("canonicalUrl")),
        _url_from_field(item.get("link")),
        _url_from_field(content.get("url")),
    ]
    for url in candidates:
        if "finance.yahoo.com" in url:
            return url
    return next((url for url in candidates if url), "")


def parse_yfinance_news_item(item: dict) -> NewsHeadline | None:
    """Normalize Yahoo news payloads (legacy flat and nested content shapes)."""
    content = item.get("content") if isinstance(item.get("content"), dict) else {}
    title = str(item.get("title") or content.get("title") or "").strip()
    if not title:
        return None
    link = _article_url(item, content)
    publisher = _publisher_label(
        item.get("publisher") or content.get("provider") or content.get("source")
    )
    return NewsHeadline(title=title, publisher=publisher, link=link)


def parse_yfinance_news(items: list[dict], *, limit: int = _MAX_HEADLINES) -> list[NewsHeadline]:
    headlines: list[NewsHeadline] = []
    for item in items:
        parsed = parse_yfinance_news_item(item)
        if parsed is not None:
            headlines.append(parsed)
        if len(headlines) >= limit:
            break
    return headlines


def headline_title_html(headline: NewsHeadline) -> str:
    title = html.escape(headline.title)
    link = headline.link.strip()
    if link.startswith(("http://", "https://")):
        return (
            f'<a href="{html.escape(link)}" target="_blank" '
            f'rel="noopener noreferrer">{title}</a>'
        )
    return title


def headline_item_html(
    headline: NewsHeadline,
    *,
    max_words: int = _HEADLINE_PREVIEW_WORDS,
) -> str:
    publisher = html.escape(headline.publisher)
    title_html = headline_title_html(headline)
    if not is_truncated(headline.title, max_words=max_words):
        return (
            f'<div class="ss-saved-news-item">'
            f'<p class="ss-saved-news-line">{title_html} · '
            f'<span class="ss-saved-news-pub">{publisher}</span></p>'
            f"</div>"
        )

    preview = html.escape(preview_words(headline.title, max_words=max_words))
    full_body = (
        f'<p class="ss-saved-news-line ss-disclosure-full">'
        f"{title_html} · <span class=\"ss-saved-news-pub\">{publisher}</span></p>"
    )
    block = disclosure_html(
        preview,
        full_body,
        more_label="Read full headline",
        less_label="Show less",
    )
    return f'<div class="ss-saved-news-item">{block}</div>'


def headlines_block_html(headlines: list[NewsHeadline]) -> str:
    if not headlines:
        return ""
    items = "".join(headline_item_html(h) for h in headlines)
    return f'<div class="ss-saved-news-list">{items}</div>'


@st.cache_data(ttl=3600, show_spinner=False)
def _fetch_news(symbol: str) -> list[dict]:
    # Imported here, not at module level: yfinance brings pandas and numpy with it, a large
    # share of the app's import time, and only the Saved tab's headlines use it.
    import yfinance as yf  # noqa: PLC0415

    ticker = yf.Ticker(symbol)
    raw = ticker.news or []
    return raw[: _MAX_HEADLINES * 2]


def fetch_saved_news(card: dict) -> None:
    symbol = yfinance_symbol(card)
    key = _cache_key(card)
    try:
        items = _fetch_news(symbol)
    except Exception:  # noqa: BLE001
        _store()[key] = NewsError("Could not load headlines right now.")
        return

    headlines = parse_yfinance_news(items, limit=_MAX_HEADLINES)
    if headlines:
        _store()[key] = headlines
    else:
        _store()[key] = NewsError("No recent headlines found for this ticker.")


def clear_cached_news(card: dict) -> None:
    _store().pop(_cache_key(card), None)


def get_cached_news(card: dict) -> list[NewsHeadline] | NewsError | None:
    return _store().get(_cache_key(card))


def render_saved_news(card: dict, *, widget_key_prefix: str = "saved") -> None:
    """Load and show up to three headlines on Saved focus view (not on Discover)."""
    market = card.get("market_code") or "unknown"
    ticker = card.get("ticker") or "unknown"
    retry_key = f"{widget_key_prefix}_news_retry_{market}_{ticker}"

    st.markdown('<p class="ss-saved-news-heading">Recent headlines</p>', unsafe_allow_html=True)

    cached = get_cached_news(card)
    if cached is None:
        fetch_saved_news(card)
        cached = get_cached_news(card)
        if cached is None:
            st.caption("Loading headlines…")
            return

    if isinstance(cached, NewsError):
        st.caption(cached.message)
        if st.button("Try again", key=retry_key):
            clear_cached_news(card)
            fetch_saved_news(card)
            st.rerun()
        return

    st.markdown(headlines_block_html(cached), unsafe_allow_html=True)
    st.caption("Headlines from Yahoo Finance — Saved tab only, cached about an hour.")
