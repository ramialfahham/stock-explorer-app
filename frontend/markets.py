"""Market labels and hero-market config (sync display names with docs/market_registry.yml)."""

from __future__ import annotations

from typing import Any

# v1 hero market — intentional starting experience for discovery queue.
HERO_MARKET_CODE = "us_sp500"

# Active ingest markets only; order matches registry ingest_active set.
MARKET_DISPLAY_NAMES: dict[str, str] = {
    "us_sp500": "S&P 500",
    "uk_ftse100": "FTSE 100",
    "jp_nikkei225": "Nikkei 225",
    "au_asx200": "ASX 200",
    "de_dax": "DAX",
}


def market_display_name(market_code: str | None) -> str:
    if not market_code:
        return "—"
    return MARKET_DISPLAY_NAMES.get(market_code, market_code.replace("_", " ").title())


def eligible_counts_by_market(cards: list[dict[str, Any]]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for card in cards:
        if not card.get("is_card_eligible"):
            continue
        code = card.get("market_code")
        if not code:
            continue
        counts[str(code)] = counts.get(str(code), 0) + 1
    return dict(sorted(counts.items()))


def discover_pool_summary(counts: dict[str, int]) -> str:
    total = sum(counts.values())
    if total == 0:
        return "No card-ready companies yet"
    hero_count = counts.get(HERO_MARKET_CODE, 0)
    hero_label = market_display_name(HERO_MARKET_CODE)
    if hero_count:
        return (
            f"{total} card-ready · {hero_label} ({hero_count}) first, "
            f"then rotating worldwide"
        )
    return f"{total} card-ready companies"


def eligible_breakdown_lines(counts: dict[str, int]) -> list[str]:
    lines: list[str] = []
    for code in sorted(counts.keys(), key=lambda c: (c != HERO_MARKET_CODE, c)):
        lines.append(f"{market_display_name(code)}: {counts[code]}")
    return lines
