"""Discover session filters — market, sector, and scoped card pool."""

from __future__ import annotations

from collections.abc import Iterable
from typing import Any

from markets import MARKET_DISPLAY_NAMES, market_display_name

ALL_MARKETS = "all"
ALL_SECTORS = "all"


def market_filter_options(cards: list[dict[str, Any]]) -> list[tuple[str, str]]:
    """Only markets with at least one eligible card, so the Filters popover never offers a
    choice that silently returns an empty list -- a market can be registered in
    `MARKET_DISPLAY_NAMES` (onboarded) with zero exported data yet (pipeline hasn't run for it
    since onboarding). Preserves `MARKET_DISPLAY_NAMES`'s own registry-ingest-order ordering
    among the markets actually shown, matching `sectors_for_market()`'s pattern of deriving
    options from live cards rather than a static list."""
    eligible_codes = {
        card.get("market_code") for card in cards if card.get("is_card_eligible")
    }
    options: list[tuple[str, str]] = [(ALL_MARKETS, "All markets")]
    options.extend(
        (code, market_display_name(code))
        for code in MARKET_DISPLAY_NAMES
        if code in eligible_codes
    )
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


_ASSESSMENT_FIELDS = ("health_verdict", "ai_read")


def attach_assessments(
    cards: list[dict[str, Any]],
    assessments: dict[tuple[str, str], dict[str, Any]],
) -> list[dict[str, Any]]:
    """Copy health_verdict/ai_read onto each card when a matching card_assessments row
    exists AND was computed from the snapshot the card is showing. No match (the assessments
    pipeline runs after export and can lag a newly-eligible card) -> card returned unchanged.
    Callers must treat a missing health_verdict key as "omit the health block", never a
    placeholder.

    The snapshot check is what keeps a card from contradicting itself. A verdict and AI read
    computed from one snapshot printed over another snapshot's numbers is worse than no
    verdict: the badge is the product's central claim and the reader cannot see the mismatch.
    Both directions are real. The assessments step can fail after a successful export, leaving
    an older verdict over newer numbers; and the export can roll a card back to an earlier
    snapshot while the verdict stays on the newer one. A healthy run writes both from the same
    mart, so a working pipeline never trips this.

    One case does NOT self-heal, and the card stays verdict-less indefinitely: a ticker the
    export evicted from its newest snapshot keeps its old assessment row forever, because
    generate_assessments.py builds records only from mart rows and never deletes."""
    result: list[dict[str, Any]] = []
    for card in cards:
        row = assessments.get(_card_key(card))
        if row is None:
            result.append(card)
            continue
        if _snapshot_sort_key(row) != _snapshot_sort_key(card):
            result.append(card)
            continue
        merged = dict(card)
        for field in _ASSESSMENT_FIELDS:
            merged[field] = row.get(field)
        result.append(merged)
    return result


def saved_keys_with_order(interactions: list[dict[str, Any]]) -> dict[tuple[str, str], str]:
    """Currently-saved (market_code, ticker) keys, each mapped to its latest save
    timestamp. A key's most recent action (save or unsave) determines current state --
    absent entirely if unsaved, or never saved. Shared with app.py's `_saved_count`/
    `_saved_cards`, which is why this is public rather than the usual module-private
    underscore convention -- it's the single source of truth for "is this saved" so
    Discover's exclusion and the Saved tab's own list can never disagree."""
    latest: dict[tuple[str, str], tuple[str, str]] = {}
    for row in interactions:
        action = row.get("action")
        if action not in ("save", "unsave"):
            continue
        key = _card_key(row)
        created = row.get("created_at") or ""
        if key not in latest or created >= latest[key][0]:
            latest[key] = (created, action)
    return {key: created for key, (created, action) in latest.items() if action == "save"}


def filter_pool(
    cards: list[dict[str, Any]],
    interactions: list[dict[str, Any]],
    *,
    market_code: str,
    sector: str,
) -> list[dict[str, Any]]:
    """Return card-eligible rows in scope, excluding saved tickers."""
    saved = saved_keys_with_order(interactions)
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


def deck_rows_lack_columns(
    cards: list[dict[str, Any]], columns: Iterable[str]
) -> bool:
    """True when a held deck row is missing a column the current code reads.

    A cheap shape invariant, not a cross-deploy guard: both the deck cache and session_state
    are in-process (`@st.cache_data` defaults to `persist=None`), so a redeploy drops both and
    the reachable case is narrow -- a long-lived session holding rows from before an in-place
    change to what the list paths read. Callers must clear the deck CACHE as well as
    session_state when this fires, or the same rows come straight back (see app.py's
    `_ensure_all_cards`).

    This replaces an earlier `business_summary`-specific version: that column is deliberately
    no longer in the deck (66% of the mart payload, read only by the card face), so the old
    check would have fired on every run and re-fetched forever.
    """
    if not cards:
        return False
    required = set(columns)
    return any(not required.issubset(card) for card in cards)
