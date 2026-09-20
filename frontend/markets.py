"""Market labels and hero-market config (sync display names with docs/market_registry.yml)."""

from __future__ import annotations

from datetime import date
from typing import Any

from card_copy import format_snapshot_date

# v1 hero market: named first in the About panel's Markets line (markets_in_deck_order below).
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


def markets_in_deck_order(counts: dict[str, int]) -> list[str]:
    """Hero market first, then alphabetical by code -- the order the About panel's
    `markets_line` names markets in."""
    return sorted(counts, key=lambda code: (code != HERO_MARKET_CODE, code))


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
