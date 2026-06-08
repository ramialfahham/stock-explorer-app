"""On-demand live market price via yfinance (session cache, not in mart)."""

from __future__ import annotations

from dataclasses import dataclass

import streamlit as st
import yfinance as yf

# Active markets only — keep in sync with docs/market_registry.yml ingest_active entries.
_EXCHANGE_SUFFIX: dict[str, str] = {
    "us_sp500": "",
    "uk_ftse100": ".L",
    "jp_nikkei225": ".T",
    "au_asx200": ".AX",
    "de_dax": ".DE",
}

_SESSION_KEY = "_live_quotes"
QUOTE_UNAVAILABLE = "Live quote unavailable"
FETCH_FAILED = "Could not reach Yahoo — open link below or try again"


@dataclass(frozen=True)
class LiveQuote:
    price: float
    currency: str


@dataclass(frozen=True)
class LiveQuoteError:
    message: str


def yfinance_symbol(card: dict) -> str:
    ticker = str(card.get("ticker") or "").strip()
    market_code = str(card.get("market_code") or "")
    suffix = _EXCHANGE_SUFFIX.get(market_code, "")
    if "." in ticker:
        return ticker
    return f"{ticker}{suffix}"


def yahoo_finance_url(card: dict) -> str:
    symbol = yfinance_symbol(card)
    return f"https://finance.yahoo.com/quote/{symbol}"


def _cache_key(card: dict) -> str:
    return f"{card.get('market_code')}:{card.get('ticker')}"


def _quote_cache() -> dict[str, LiveQuote | LiveQuoteError]:
    if _SESSION_KEY not in st.session_state:
        st.session_state[_SESSION_KEY] = {}
    return st.session_state[_SESSION_KEY]


def get_cached_quote(card: dict) -> LiveQuote | LiveQuoteError | None:
    return _quote_cache().get(_cache_key(card))


def fetch_live_quote(card: dict) -> LiveQuote | LiveQuoteError:
    key = _cache_key(card)
    cache = _quote_cache()

    symbol = yfinance_symbol(card)
    if not symbol:
        result = LiveQuoteError(QUOTE_UNAVAILABLE)
        cache[key] = result
        return result

    try:
        info = yf.Ticker(symbol).info
        price = info.get("regularMarketPrice") or info.get("currentPrice")
        currency = info.get("currency") or card.get("currency") or ""
        if price is None:
            result = LiveQuoteError(QUOTE_UNAVAILABLE)
        else:
            result = LiveQuote(price=float(price), currency=str(currency))
    except Exception:  # noqa: BLE001
        result = LiveQuoteError(FETCH_FAILED)

    cache[key] = result
    return result


def format_quote(quote: LiveQuote) -> str:
    if quote.currency:
        return f"{quote.price:,.2f} {quote.currency}"
    return f"{quote.price:,.2f}"


def live_quote_button_label(card: dict) -> str:
    cached = get_cached_quote(card)
    if isinstance(cached, LiveQuote):
        return format_quote(cached)
    if isinstance(cached, LiveQuoteError):
        return "Tap to retry"
    return "Tap for live quote"
