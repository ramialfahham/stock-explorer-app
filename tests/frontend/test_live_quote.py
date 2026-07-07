"""Tests for Yahoo Finance symbol and quote-page URLs."""

from __future__ import annotations

from live_quote import yahoo_finance_url, yfinance_symbol  # noqa: E402


def test_yfinance_symbol_us_ticker() -> None:
    assert yfinance_symbol({"market_code": "us_sp500", "ticker": "AAPL"}) == "AAPL"


def test_yfinance_symbol_german_suffix() -> None:
    assert yfinance_symbol({"market_code": "de_dax", "ticker": "SAP"}) == "SAP.DE"


def test_yfinance_symbol_preserves_dotted_ticker() -> None:
    assert yfinance_symbol({"market_code": "de_dax", "ticker": "AIR.PA"}) == "AIR.PA"


def test_yahoo_finance_url() -> None:
    url = yahoo_finance_url({"market_code": "us_sp500", "ticker": "MSFT"})
    assert url == "https://finance.yahoo.com/quote/MSFT"
