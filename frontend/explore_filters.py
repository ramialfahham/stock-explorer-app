"""Discover session filters — market, sector, and scoped card pool."""

from __future__ import annotations

from typing import Any

from card_copy import format_snapshot_date
from markets import MARKET_DISPLAY_NAMES, market_display_name

ALL_MARKETS = "all"
ALL_SECTORS = "all"
SURPRISE_ME_LABEL = "Surprise me worldwide"


def market_filter_options() -> list[tuple[str, str]]:
    options = [(code, market_display_name(code)) for code in MARKET_DISPLAY_NAMES]
    options.append((ALL_MARKETS, "All markets"))
    return options


def default_market_filter() -> str:
    return ALL_MARKETS


def _card_key(card: dict[str, Any]) -> tuple[str, str]:
    return (card["market_code"], card["ticker"])


def _snapshot_sort_key(card: dict[str, Any]) -> str:
    raw = card.get("snapshot_date")
    if raw is None:
        return ""
    return str(raw)[:10]


def dedupe_to_latest_snapshot(cards: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Keep one row per (market_code, ticker) — latest snapshot_date wins."""
    latest: dict[tuple[str, str], dict[str, Any]] = {}
    for card in cards:
        key = _card_key(card)
        prev = latest.get(key)
        if prev is None or _snapshot_sort_key(card) > _snapshot_sort_key(prev):
            latest[key] = card
    return list(latest.values())


def _saved_keys(interactions: list[dict[str, Any]]) -> set[tuple[str, str]]:
    return {
        _card_key(row)
        for row in interactions
        if row.get("action") == "save"
    }


def filter_pool(
    cards: list[dict[str, Any]],
    interactions: list[dict[str, Any]],
    *,
    market_code: str,
    sector: str,
    surprise_me: bool,
) -> list[dict[str, Any]]:
    """Return card-eligible rows in scope, excluding saved tickers."""
    saved = _saved_keys(interactions)
    pool: list[dict[str, Any]] = []
    for card in cards:
        if not card.get("is_card_eligible"):
            continue
        if _card_key(card) in saved:
            continue
        if not surprise_me and market_code != ALL_MARKETS:
            if card.get("market_code") != market_code:
                continue
        if sector != ALL_SECTORS and (card.get("sector") or "Unknown") != sector:
            continue
        pool.append(card)
    return pool


def sectors_for_market(
    cards: list[dict[str, Any]],
    *,
    market_code: str,
    surprise_me: bool,
) -> list[str]:
    sectors: set[str] = set()
    for card in cards:
        if not card.get("is_card_eligible"):
            continue
        if not surprise_me and market_code != ALL_MARKETS:
            if card.get("market_code") != market_code:
                continue
        sectors.add(card.get("sector") or "Unknown")
    return sorted(sectors, key=str.lower)


def scope_summary(
    *,
    market_code: str,
    sector: str,
    surprise_me: bool,
    pool_size: int,
) -> str:
    if surprise_me or market_code == ALL_MARKETS:
        if sector != ALL_SECTORS:
            return f"{pool_size} worldwide · {sector}"
        return f"{pool_size} companies worldwide"
    market_label = market_display_name(market_code)
    if sector != ALL_SECTORS:
        return f"{pool_size} in {market_label} · {sector}"
    return f"{pool_size} in {market_label}"


def walk_progress_line(*, position: int, total: int) -> str:
    if total <= 0:
        return ""
    return f"{position} of {total}"


def walk_meta_line(
    *,
    position: int,
    total: int,
    market_code: str,
    sector: str,
    surprise_me: bool,
) -> str:
    if total <= 0:
        return ""
    if surprise_me:
        return f"{position} of {total} worldwide"
    market_label = market_display_name(market_code)
    if sector != ALL_SECTORS:
        return f"{position} of {total} in {market_label} · {sector}"
    return f"{position} of {total} in {market_label}"


def browse_row_subtitle(card: dict[str, Any]) -> str:
    sector = card.get("sector") or "Unknown sector"
    snapshot = format_snapshot_date(card.get("snapshot_date"))
    if snapshot:
        return f"{sector} · {snapshot}"
    return sector
