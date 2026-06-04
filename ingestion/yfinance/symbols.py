"""Yahoo Finance symbol mapping for local constituent tickers."""

from __future__ import annotations


def to_yfinance_ticker(local_ticker: str, exchange_suffix: str) -> str:
    """Build Yahoo symbol for Ticker.info / statements."""
    local_ticker = str(local_ticker).strip()
    if "." in local_ticker:
        return local_ticker
    return f"{local_ticker}{exchange_suffix}"


def to_yfinance_download_ticker(local_ticker: str, exchange_suffix: str) -> str:
    """Build Yahoo symbol for yf.download (US class shares use hyphen, not dot)."""
    symbol = to_yfinance_ticker(local_ticker, exchange_suffix)
    if exchange_suffix == "" and "." in symbol:
        return symbol.replace(".", "-")
    return symbol
