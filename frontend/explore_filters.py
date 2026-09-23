"""Discover session filters -- market, sector, and scoped card pool."""

from __future__ import annotations

from collections.abc import Callable, Iterable
from typing import Any

from markets import MARKET_DISPLAY_NAMES, market_display_name

ALL_MARKETS = "all"
ALL_SECTORS = "all"


def market_filter_options(cards: list[dict[str, Any]]) -> list[tuple[str, str]]:
    """Only markets with at least one eligible card, so the Filters popover never offers a
    choice that silently returns an empty list -- a market can be onboarded with zero
    exported data yet. Preserves `MARKET_DISPLAY_NAMES`'s registry order among the markets
    actually shown."""
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


METRIC_PRESETS: dict[str, dict[str, Any]] = {
    "high_margin": {
        "label": "High margin",
        "checks": (
            ("operating", "ebit_margin_pct", "gt", 20.0),
            ("financial", "net_margin_pct", "gt", 20.0),
        ),
    },
    "low_debt": {
        "label": "Low debt",
        "checks": (("operating", "net_debt_to_ebitda", "lt", 2.0),),
    },
    "growing_revenue": {
        "label": "Growing revenue",
        "checks": (
            ("operating", "revenue_growth_yoy_pct", "gt", 0.0),
            ("financial", "revenue_growth_yoy_pct", "gt", 0.0),
        ),
    },
    "strong_returns": {
        "label": "Strong returns",
        "checks": (
            ("operating", "statement_roe_pct", "gt", 15.0),
            ("financial", "statement_roe_pct", "gt", 15.0),
        ),
    },
    "cash_safe": {
        "label": "Cash-safe",
        "checks": (("pre_revenue", "cash_runway_months", "gt", 18.0),),
    },
}


def metric_preset_options(cards: Iterable[dict[str, Any]] = ()) -> list[str]:
    """Preset IDs to offer, excluding any whose target company_type(s) have zero eligible
    cards in the current deck -- a preset that can never match anything looks identical to
    a genuinely broken filter. An omitted `cards` (no deck in scope) offers every preset;
    a `cards` that was passed but has no eligible rows offers none."""
    cards = list(cards)
    if not cards:
        return list(METRIC_PRESETS)
    types_present = {card.get("company_type") for card in cards if card.get("is_card_eligible")}
    return [
        preset_id
        for preset_id, spec in METRIC_PRESETS.items()
        if any(company_type in types_present for company_type, *_ in spec["checks"])
    ]


def metric_preset_label(preset_id: str) -> str:
    return METRIC_PRESETS[preset_id]["label"]


def _card_matches_preset(card: dict[str, Any], preset_id: str) -> bool:
    """Checks are scoped by `card["company_type"]`, not by which metric happens to be
    non-null -- `ebit_margin_pct` and `net_margin_pct` are not mutually exclusive in the
    data, so presence alone would silently AND the two margins together for an operating
    card. A card whose type has no check in this preset, or is missing that metric's value,
    passes through untouched rather than being excluded."""
    checks = METRIC_PRESETS[preset_id]["checks"]
    card_type = card.get("company_type")
    applicable = [(m, op, t) for ctype, m, op, t in checks if ctype == card_type]
    if not applicable:
        return True
    for metric, op, threshold in applicable:
        value = card.get(metric)
        if value is None:
            continue
        if op == "gt" and not value > threshold:
            return False
        if op == "lt" and not value < threshold:
            return False
    return True


def card_matches_metric_presets(card: dict[str, Any], preset_ids: Iterable[str]) -> bool:
    return all(_card_matches_preset(card, preset_id) for preset_id in preset_ids)


def filter_scope_summary(
    *, market_code: str, sector: str, metric_presets: Iterable[str] = ()
) -> str:
    """Compact label for the closed Filters row on Discover."""
    base = f"{market_filter_label(market_code)} · {sector_filter_label(sector)}"
    active = [pid for pid in METRIC_PRESETS if pid in set(metric_presets)]
    if not active:
        return base
    return f"{base} · {', '.join(metric_preset_label(pid) for pid in active)}"


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


def _dedupe_by_latest_snapshot(
    cards: list[dict[str, Any]], key_fn: Callable[[dict[str, Any]], Any]
) -> list[dict[str, Any]]:
    """Keep one row per key_fn(card) -- latest snapshot_date wins. Shared by
    `dedupe_to_latest_snapshot` and `_dedupe_by_ticker` so the business_summary backfill
    below stays in one place rather than two copies that can drift apart."""
    latest: dict[Any, dict[str, Any]] = {}
    for card in cards:
        key = key_fn(card)
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


def dedupe_to_latest_snapshot(cards: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Keep one row per (market_code, ticker) -- latest snapshot_date wins."""
    return _dedupe_by_latest_snapshot(cards, _card_key)


_ASSESSMENT_FIELDS = ("health_verdict", "ai_read")


def attach_assessments(
    cards: list[dict[str, Any]],
    assessments: dict[tuple[str, str], dict[str, Any]],
) -> list[dict[str, Any]]:
    """Copy health_verdict/ai_read onto each card when a card_assessments row matches it AND
    was computed from the same snapshot the card is showing -- printing a verdict from a
    different snapshot over the card's own numbers would contradict them, so a mismatch (or
    no match; the assessments pipeline runs after export and can lag) returns the card
    unchanged. Callers must treat a missing health_verdict key as "omit the health block",
    never a placeholder.

    A ticker evicted from its newest export snapshot keeps its old assessment row forever
    (`generate_assessments.py` never deletes), so it stays verdict-less indefinitely.
    Compare via `_snapshot_sort_key`, not bare equality, so a `snapshot_date` column gaining
    a time component can't silently blank every badge."""
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


def _latest_action_keys(
    interactions: list[dict[str, Any]], *, add_action: str, remove_action: str
) -> dict[tuple[str, str], str]:
    """Currently-active (market_code, ticker) keys for one add/remove action pair, each
    mapped to its latest action's timestamp. A key's most recent action determines current
    state -- absent entirely if removed, or never added. Parameterized by action pair
    rather than hardcoded to save/unsave, the only pair this app tracks."""
    latest: dict[tuple[str, str], tuple[str, str]] = {}
    for row in interactions:
        action = row.get("action")
        if action not in (add_action, remove_action):
            continue
        key = _card_key(row)
        created = row.get("created_at") or ""
        if key not in latest or created >= latest[key][0]:
            latest[key] = (created, action)
    return {key: created for key, (created, action) in latest.items() if action == add_action}


def saved_keys_with_order(interactions: list[dict[str, Any]]) -> dict[tuple[str, str], str]:
    """Currently-saved (market_code, ticker) keys, each mapped to its latest save
    timestamp. Public (not underscore-prefixed) because app.py's `_saved_count`/
    `_saved_cards` share it as the single source of truth for "is this saved", so
    Discover's exclusion and the Saved tab's own list can never disagree."""
    return _latest_action_keys(interactions, add_action="save", remove_action="unsave")


def _dedupe_by_ticker(cards: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Keep one row per ticker -- latest snapshot_date wins. A company listed in two
    indices (e.g. Airbus in both the DAX and CAC 40) resolves to the same yfinance ticker
    and would otherwise appear as two cards differing only by market_code. Only meaningful
    for the ALL_MARKETS scope -- a single-market filter never has two rows sharing a ticker."""
    return _dedupe_by_latest_snapshot(cards, lambda card: card["ticker"])


def filter_pool(
    cards: list[dict[str, Any]],
    interactions: list[dict[str, Any]],
    *,
    market_code: str,
    sector: str,
    metric_presets: Iterable[str] = (),
) -> list[dict[str, Any]]:
    """Return card-eligible rows in scope, excluding saved tickers."""
    saved = saved_keys_with_order(interactions)
    preset_ids = list(metric_presets)
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
        if preset_ids and not card_matches_metric_presets(card, preset_ids):
            continue
        pool.append(card)
    if market_code == ALL_MARKETS:
        pool = _dedupe_by_ticker(pool)
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
    are in-process (`@st.cache_data` defaults to `persist=None`), so a redeploy drops both
    and the reachable case is narrow -- a long-lived session holding rows from before an
    in-place change to what the list paths read. Callers must clear the deck cache as well
    as session_state when this fires, or the same rows come straight back (see app.py's
    `_ensure_all_cards`).
    """
    if not cards:
        return False
    required = set(columns)
    return any(not required.issubset(card) for card in cards)
