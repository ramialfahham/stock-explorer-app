"""Market labels and hero-market config (sync display names with docs/market_registry.yml)."""

from __future__ import annotations

from datetime import date
from typing import Any

from card_copy import format_snapshot_date

# v1 hero market: the market called out by name in "About the data" summaries and listed
# first in its per-market breakdown (markets_in_deck_order below).
HERO_MARKET_CODE = "us_sp500"

# Active ingest markets only; order matches registry ingest_active set.
MARKET_DISPLAY_NAMES: dict[str, str] = {
    "us_sp500": "S&P 500",
    "uk_ftse100": "FTSE 100",
    "jp_nikkei225": "Nikkei 225",
    "au_asx200": "ASX 200",
    "de_dax": "DAX",
    "fr_cac40": "CAC 40",
    "nl_aex": "AEX",
    "ch_smi": "SMI",
    "es_ibex35": "IBEX 35",
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
        return f"{total} card-ready · {hero_count} in {hero_label}"
    return f"{total} card-ready companies"


def markets_in_deck_order(counts: dict[str, int]) -> list[str]:
    """Hero market first, then alphabetical by code.

    One definition because two lines in the same "About the data" panel render this order: the
    coverage line and the per-market breakdown under it. They were separate copies of the sort
    key in two modules, which meant they agreed only by coincidence and would drift apart in the
    same panel the moment one changed.
    """
    return sorted(counts, key=lambda code: (code != HERO_MARKET_CODE, code))


def eligible_breakdown_lines(counts: dict[str, int]) -> list[str]:
    return [
        f"{market_display_name(code)}: {counts[code]}"
        for code in markets_in_deck_order(counts)
    ]


def latest_snapshot_label(cards: list[dict[str, Any]]) -> str | None:
    """Latest fundamentals snapshot date across eligible cards."""
    latest: date | None = None
    for card in cards:
        if not card.get("is_card_eligible"):
            continue
        raw = card.get("snapshot_date")
        parsed: date | None
        if isinstance(raw, date):
            parsed = raw
        elif isinstance(raw, str):
            try:
                parsed = date.fromisoformat(raw[:10])
            except ValueError:
                parsed = None
        else:
            parsed = None
        if parsed is not None and (latest is None or parsed > latest):
            latest = parsed
    if latest is None:
        return None
    return format_snapshot_date(latest)
