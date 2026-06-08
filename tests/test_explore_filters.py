"""Tests for explore filter pool logic."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FRONTEND = ROOT / "frontend"
sys.path.insert(0, str(FRONTEND))

from explore_filters import ALL_SECTORS, filter_pool  # noqa: E402


def _card(ticker: str, sector: str, market: str = "us_sp500") -> dict:
    return {
        "market_code": market,
        "ticker": ticker,
        "sector": sector,
        "is_card_eligible": True,
    }


def test_filter_pool_respects_sector() -> None:
    cards = [
        _card("AAPL", "Technology"),
        _card("ALB", "Basic Materials"),
    ]
    pool = filter_pool(
        cards,
        [],
        market_code="us_sp500",
        sector="Basic Materials",
        surprise_me=False,
    )
    tickers = {c["ticker"] for c in pool}
    assert tickers == {"ALB"}


def test_filter_pool_excludes_saved() -> None:
    cards = [_card("AAPL", "Technology"), _card("MSFT", "Technology")]
    interactions = [{"market_code": "us_sp500", "ticker": "AAPL", "action": "save"}]
    pool = filter_pool(
        cards,
        interactions,
        market_code="us_sp500",
        sector=ALL_SECTORS,
        surprise_me=False,
    )
    assert [c["ticker"] for c in pool] == ["MSFT"]
