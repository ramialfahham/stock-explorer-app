"""Discovery queue ordering per docs/north_star.md."""

from __future__ import annotations

from collections import defaultdict
from typing import Any


def _ticker_key(row: dict[str, Any]) -> tuple[str, str]:
    return (row["market_code"], row["ticker"])


def build_queue(
    cards: list[dict[str, Any]],
    interactions: list[dict[str, Any]],
    *,
    market_index: int = 0,
    sector_shown: dict[tuple[str, str], int] | None = None,
) -> list[dict[str, Any]]:
    """Return card-eligible rows in discovery order (round-robin, unseen first, sector-balanced)."""
    sector_shown = sector_shown or {}
    eligible = [c for c in cards if c.get("is_card_eligible")]
    if not eligible:
        return []

    saved = {
        _ticker_key(i)
        for i in interactions
        if i.get("action") == "save"
    }
    skip_counts: dict[tuple[str, str], int] = defaultdict(int)
    seen: set[tuple[str, str]] = set()
    for row in interactions:
        key = _ticker_key(row)
        seen.add(key)
        if row.get("action") == "skip":
            skip_counts[key] += 1

    pool = [c for c in eligible if _ticker_key(c) not in saved]
    if not pool:
        return []

    by_market: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for card in pool:
        by_market[card["market_code"]].append(card)

    markets = sorted(by_market.keys())
    if not markets:
        return []

    def sort_candidates(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
        def sort_key(card: dict[str, Any]) -> tuple:
            key = _ticker_key(card)
            sector = card.get("sector") or "Unknown"
            sector_key = (card["market_code"], sector)
            return (
                key in seen,
                skip_counts.get(key, 0),
                sector_shown.get(sector_key, 0),
                card.get("ticker", ""),
            )

        return sorted(items, key=sort_key)

    for market in by_market:
        by_market[market] = sort_candidates(by_market[market])

    ordered: list[dict[str, Any]] = []
    remaining = {m: list(by_market[m]) for m in markets}
    idx = market_index % len(markets)
    total = sum(len(v) for v in remaining.values())

    while len(ordered) < total:
        progressed = False
        for _ in range(len(markets)):
            market = markets[idx % len(markets)]
            idx += 1
            candidates = remaining[market]
            if not candidates:
                continue
            card = candidates.pop(0)
            ordered.append(card)
            sector = card.get("sector") or "Unknown"
            sector_shown[(market, sector)] = sector_shown.get((market, sector), 0) + 1
            progressed = True
        if not progressed:
            break

    return ordered
