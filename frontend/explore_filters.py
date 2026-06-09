"""Discover session filters — market, sector, and scoped card pool."""

from __future__ import annotations

from typing import Any

from card_copy import ALL_METRICS, METRIC_LABELS, format_metric_value, format_snapshot_date
from markets import MARKET_DISPLAY_NAMES, market_display_name

ALL_MARKETS = "all"
ALL_SECTORS = "all"

MetricRange = tuple[float | None, float | None]
MetricFilters = dict[str, MetricRange]

METRIC_FILTER_SPECS: dict[str, dict[str, float]] = {
    "forward_pe": {"lo": 0.0, "hi": 500.0, "step": 0.5},
    "ebit_margin_pct": {"lo": -500.0, "hi": 500.0, "step": 1.0},
    "revenue_growth_yoy_pct": {"lo": -100.0, "hi": 500.0, "step": 1.0},
    "net_debt_to_ebitda": {"lo": -50.0, "hi": 50.0, "step": 0.5},
    "fcf_margin_pct": {"lo": -500.0, "hi": 500.0, "step": 1.0},
}


def default_metric_filter_bounds(metric: str) -> tuple[float, float]:
    spec = METRIC_FILTER_SPECS[metric]
    return spec["lo"], spec["hi"]


def normalize_metric_filter_input(
    metric: str,
    *,
    min_value: float,
    max_value: float,
) -> MetricRange:
    lo_bound, hi_bound = default_metric_filter_bounds(metric)
    min_active = None if min_value <= lo_bound else min_value
    max_active = None if max_value >= hi_bound else max_value
    if min_active is not None and max_active is not None and min_active > max_active:
        return max_active, min_active
    return min_active, max_active


def metric_filters_from_inputs(inputs: dict[str, tuple[float, float]]) -> MetricFilters:
    return {
        metric: normalize_metric_filter_input(
            metric,
            min_value=inputs[metric][0],
            max_value=inputs[metric][1],
        )
        for metric in ALL_METRICS
    }


def metric_filters_active(metric_filters: MetricFilters) -> bool:
    return any(lo is not None or hi is not None for lo, hi in metric_filters.values())


def card_passes_metric_filters(card: dict[str, Any], metric_filters: MetricFilters) -> bool:
    for metric, (min_value, max_value) in metric_filters.items():
        if min_value is None and max_value is None:
            continue
        raw = card.get(metric)
        if raw is None:
            return False
        value = float(raw)
        if min_value is not None and value < min_value:
            return False
        if max_value is not None and value > max_value:
            return False
    return True


def metric_filter_summary(metric_filters: MetricFilters, *, max_parts: int = 2) -> str:
    parts: list[str] = []
    for metric in ALL_METRICS:
        min_value, max_value = metric_filters.get(metric, (None, None))
        label = METRIC_LABELS[metric]
        if min_value is not None and max_value is not None:
            parts.append(
                f"{label} {format_metric_value(metric, min_value)}–"
                f"{format_metric_value(metric, max_value)}"
            )
        elif min_value is not None:
            parts.append(f"{label} ≥ {format_metric_value(metric, min_value)}")
        elif max_value is not None:
            parts.append(f"{label} ≤ {format_metric_value(metric, max_value)}")
    if not parts:
        return ""
    if len(parts) > max_parts:
        return f"{len(parts)} metric filters"
    return " · ".join(parts)


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


def filter_scope_summary(
    *,
    market_code: str,
    sector: str,
    metric_filters: MetricFilters | None = None,
) -> str:
    """Compact label for the closed Filters row on Discover."""
    base = f"{market_filter_label(market_code)} · {sector_filter_label(sector)}"
    if metric_filters and metric_filters_active(metric_filters):
        extra = metric_filter_summary(metric_filters)
        if extra:
            return f"{base} · {extra}"
    return base


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
    metric_filters: MetricFilters | None = None,
) -> list[dict[str, Any]]:
    """Return card-eligible rows in scope, excluding saved tickers."""
    saved = _saved_keys(interactions)
    use_metric_filters = metric_filters is not None and metric_filters_active(metric_filters)
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
        if use_metric_filters and not card_passes_metric_filters(card, metric_filters):
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


def browse_row_subtitle(card: dict[str, Any]) -> str:
    sector = card.get("sector") or "Unknown sector"
    snapshot = format_snapshot_date(card.get("snapshot_date"))
    if snapshot:
        return f"{sector} · {snapshot}"
    return sector


def cards_lack_business_summary(cards: list[dict[str, Any]]) -> bool:
    """True when export/schema has no usable company descriptions."""
    eligible = [c for c in cards if c.get("is_card_eligible")]
    if not eligible:
        return False
    if any("business_summary" not in c for c in eligible):
        return True
    filled = sum(1 for c in eligible if str(c.get("business_summary") or "").strip())
    return filled == 0
