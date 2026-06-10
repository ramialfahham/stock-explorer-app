"""Discover session filters — market, sector, and scoped card pool."""

from __future__ import annotations

from typing import Any

from markets import MARKET_DISPLAY_NAMES, market_display_name

ALL_MARKETS = "all"
ALL_SECTORS = "all"


def market_filter_options() -> list[tuple[str, str]]:
    options: list[tuple[str, str]] = [(ALL_MARKETS, "All markets")]
    options.extend((code, market_display_name(code)) for code in MARKET_DISPLAY_NAMES)
    return options


def default_market_filter() -> str:
    return ALL_MARKETS


def market_filter_label(market_code: str) -> str:
    if market_code == ALL_MARKETS:
        return "All markets"
    return market_display_name(market_code)


def sector_filter_label(sector: str) -> str:
    if sector == ALL_SECTORS:
        return "All sectors"
    return sector


def filter_scope_summary(*, market_code: str, sector: str) -> str:
    """Compact label for the closed Filters row on Discover."""
    return f"{market_filter_label(market_code)} · {sector_filter_label(sector)}"


def _card_key(card: dict[str, Any]) -> tuple[str, str]:
    return (card["market_code"], card["ticker"])


def _snapshot_sort_key(card: dict[str, Any]) -> str:
    raw = card.get("snapshot_date")
    if raw is None:
        return ""
    return str(raw)[:10]


def _has_business_summary(card: dict[str, Any]) -> bool:
    raw = card.get("business_summary") or card.get("longBusinessSummary")
    return bool(str(raw or "").strip())


def dedupe_to_latest_snapshot(cards: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Keep one row per (market_code, ticker) — latest snapshot_date wins."""
    latest: dict[tuple[str, str], dict[str, Any]] = {}
    for card in cards:
        key = _card_key(card)
        prev = latest.get(key)
        if prev is None:
            latest[key] = card
            continue
        card_key = _snapshot_sort_key(card)
        prev_key = _snapshot_sort_key(prev)
        if card_key > prev_key:
            winner, loser = card, prev
        elif card_key < prev_key:
            winner, loser = prev, card
        else:
            winner, loser = prev, card
        merged = dict(winner)
        if not _has_business_summary(merged) and _has_business_summary(loser):
            merged["business_summary"] = loser.get("business_summary")
        latest[key] = merged
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
) -> list[dict[str, Any]]:
    """Return card-eligible rows in scope, excluding saved tickers."""
    saved = _saved_keys(interactions)
    pool: list[dict[str, Any]] = []
    for card in cards:
        if not card.get("is_card_eligible"):
            continue
        if _card_key(card) in saved:
            continue
        if market_code != ALL_MARKETS and card.get("market_code") != market_code:
            continue
        if sector != ALL_SECTORS and (card.get("sector") or "Unknown") != sector:
            continue
        pool.append(card)
    return pool


def sectors_for_market(
    cards: list[dict[str, Any]],
    *,
    market_code: str,
) -> list[str]:
    sectors: set[str] = set()
    for card in cards:
        if not card.get("is_card_eligible"):
            continue
        if market_code != ALL_MARKETS and card.get("market_code") != market_code:
            continue
        sectors.add(card.get("sector") or "Unknown")
    return sorted(sectors, key=str.lower)


def scope_summary(
    *,
    market_code: str,
    sector: str,
    pool_size: int,
) -> str:
    if market_code == ALL_MARKETS:
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
) -> str:
    if total <= 0:
        return ""
    if market_code == ALL_MARKETS:
        if sector != ALL_SECTORS:
            return f"{position} of {total} worldwide · {sector}"
        return f"{position} of {total} worldwide"
    market_label = market_display_name(market_code)
    if sector != ALL_SECTORS:
        return f"{position} of {total} in {market_label} · {sector}"
    return f"{position} of {total} in {market_label}"


def cards_lack_business_summary(cards: list[dict[str, Any]]) -> bool:
    """True when export/schema has no usable company descriptions."""
    eligible = [c for c in cards if c.get("is_card_eligible")]
    if not eligible:
        return False
    if any("business_summary" not in c for c in eligible):
        return True
    filled = sum(1 for c in eligible if str(c.get("business_summary") or "").strip())
    return filled == 0
