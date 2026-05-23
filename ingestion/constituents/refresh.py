"""Fetch constituent lists from configured external sources."""

from __future__ import annotations

from dataclasses import dataclass
from io import StringIO

import pandas as pd
import requests
import yaml

from ingestion.constituents.seeds import write_constituents
from ingestion.paths import CONSTITUENT_SOURCES_PATH

WIKIPEDIA_USER_AGENT = (
    "stock-swipe-app/1.0 (https://github.com/ramialfahham/stock-swipe-app)"
)


@dataclass(frozen=True)
class RefreshConfig:
    market_code: str
    provider: str
    refresh_enabled: bool
    url: str | None = None
    table_index: int | None = None
    ticker_column: str | None = None
    name_column: str | None = None
    notes: str | None = None


def load_refresh_configs() -> dict[str, RefreshConfig]:
    data = yaml.safe_load(CONSTITUENT_SOURCES_PATH.read_text(encoding="utf-8"))
    configs: dict[str, RefreshConfig] = {}

    for market_code, row in (data.get("markets") or {}).items():
        if not isinstance(row, dict):
            continue
        configs[market_code] = RefreshConfig(
            market_code=market_code,
            provider=str(row.get("provider", "manual")),
            refresh_enabled=bool(row.get("refresh_enabled", True)),
            url=row.get("url"),
            table_index=row.get("table_index"),
            ticker_column=row.get("ticker_column"),
            name_column=row.get("name_column"),
            notes=row.get("notes"),
        )

    return configs


def _fetch_wikipedia_table(url: str, table_index: int) -> pd.DataFrame:
    response = requests.get(
        url,
        headers={"User-Agent": WIKIPEDIA_USER_AGENT},
        timeout=30,
    )
    response.raise_for_status()
    tables = pd.read_html(StringIO(response.text), flavor="lxml")
    if table_index >= len(tables):
        raise IndexError(f"table_index {table_index} out of range (found {len(tables)} tables)")
    return tables[table_index]


def refresh_market(config: RefreshConfig) -> int:
    if config.provider == "manual" or not config.refresh_enabled:
        raise ValueError(
            f"{config.market_code} uses manual seeds"
            + (f": {config.notes}" if config.notes else "")
        )

    if config.provider != "wikipedia":
        raise ValueError(f"Unsupported provider for {config.market_code}: {config.provider}")

    if not all([config.url, config.table_index is not None, config.ticker_column, config.name_column]):
        raise ValueError(f"Incomplete wikipedia config for {config.market_code}")

    table = _fetch_wikipedia_table(config.url, config.table_index)
    tickers = table[config.ticker_column]
    names = table[config.name_column]
    write_constituents(
        config.market_code,
        tickers,
        names,
        source="wikipedia",
    )
    return len(tickers)
