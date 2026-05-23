"""Load and validate docs/market_registry.yml."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import yaml

from ingestion.paths import REGISTRY_PATH


@dataclass(frozen=True)
class Market:
    market_code: str
    index_name: str
    exchange_suffix: str
    source: str
    ingest_active: bool


def load_markets(*, active_only: bool = False) -> list[Market]:
    data = yaml.safe_load(REGISTRY_PATH.read_text(encoding="utf-8"))
    markets_raw = data.get("markets") or []
    markets: list[Market] = []

    for row in markets_raw:
        if not isinstance(row, dict):
            continue
        market = Market(
            market_code=str(row["market_code"]),
            index_name=str(row["index_name"]),
            exchange_suffix=str(row.get("exchange_suffix", "")),
            source=str(row.get("source", "yfinance")),
            ingest_active=bool(row.get("ingest_active", False)),
        )
        if active_only and not market.ingest_active:
            continue
        markets.append(market)

    return markets


def get_market(market_code: str) -> Market:
    for market in load_markets():
        if market.market_code == market_code:
            return market
    raise KeyError(f"Unknown market_code: {market_code}")
