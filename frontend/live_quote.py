"""Yahoo Finance symbol and quote-page URLs for cards (used by footer + saved news)."""

from __future__ import annotations

# Active markets only — keep in sync with docs/market_registry.yml ingest_active entries.
_EXCHANGE_SUFFIX: dict[str, str] = {
    "us_sp500": "",
    "uk_ftse100": ".L",
    "jp_nikkei225": ".T",
    "au_asx200": ".AX",
    "de_dax": ".DE",
    "fr_cac40": ".PA",
    "nl_aex": ".AS",
    "ch_smi": ".SW",
    "es_ibex35": ".MC",
}


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
