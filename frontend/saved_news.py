"""On-demand news headlines for saved companies (Saved tab only)."""

from __future__ import annotations

from dataclasses import dataclass

import streamlit as st
import yfinance as yf

from live_quote import yfinance_symbol

_SESSION_KEY = "_saved_news"
_MAX_HEADLINES = 3


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


@st.cache_data(ttl=3600, show_spinner=False)
def _fetch_news(symbol: str) -> list[dict]:
    ticker = yf.Ticker(symbol)
    raw = ticker.news or []
    return raw[:_MAX_HEADLINES]


def fetch_saved_news(card: dict) -> None:
    symbol = yfinance_symbol(card)
    key = _cache_key(card)
    try:
        items = _fetch_news(symbol)
    except Exception:  # noqa: BLE001
        _store()[key] = NewsError("Could not load headlines right now.")
        return

    headlines: list[NewsHeadline] = []
    for item in items:
        title = str(item.get("title") or "").strip()
        if not title:
            continue
        publisher = str(item.get("publisher") or "Source").strip()
        link = str(item.get("link") or "").strip()
        headlines.append(NewsHeadline(title=title, publisher=publisher, link=link))

    if headlines:
        _store()[key] = headlines
    else:
        _store()[key] = NewsError("No recent headlines found for this ticker.")


def get_cached_news(card: dict) -> list[NewsHeadline] | NewsError | None:
    return _store().get(_cache_key(card))


def render_saved_news(card: dict, *, widget_key_prefix: str = "saved") -> None:
    """Show 2–3 headlines when user requests them on Saved focus view."""
    market = card.get("market_code") or "unknown"
    ticker = card.get("ticker") or "unknown"
    button_key = f"{widget_key_prefix}_news_{market}_{ticker}"

    st.markdown('<p class="ss-saved-news-heading">Recent headlines</p>', unsafe_allow_html=True)
    if st.button("Load headlines", key=button_key, use_container_width=True):
        fetch_saved_news(card)
        st.rerun()

    cached = get_cached_news(card)
    if cached is None:
        st.caption("Headlines load on demand — not on Discover cards.")
        return
    if isinstance(cached, NewsError):
        st.caption(cached.message)
        return

    for headline in cached:
        if headline.link:
            st.markdown(f"- [{headline.title}]({headline.link}) · _{headline.publisher}_")
        else:
            st.markdown(f"- {headline.title} · _{headline.publisher}_")
