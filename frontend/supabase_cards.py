"""Load mart_stock_cards and card_assessments from Supabase with PostgREST pagination."""

from __future__ import annotations

from typing import Any, Protocol

from explore_filters import attach_assessments, dedupe_to_latest_snapshot

# PostgREST default max rows per request.
PAGE_SIZE = 1000


class _TableQuery(Protocol):
    def select(self, *args: Any, **kwargs: Any) -> _TableQuery: ...
    def eq(self, *args: Any, **kwargs: Any) -> _TableQuery: ...
    def order(self, *args: Any, **kwargs: Any) -> _TableQuery: ...
    def range(self, *args: Any, **kwargs: Any) -> _TableQuery: ...
    def execute(self) -> Any: ...


class _SupabaseClient(Protocol):
    def table(self, name: str) -> _TableQuery: ...


def fetch_all_eligible_rows(client: _SupabaseClient) -> list[dict[str, Any]]:
    """Fetch every eligible mart row — PostgREST caps unbounded selects at 1000."""
    raw: list[dict[str, Any]] = []
    offset = 0
    while True:
        response = (
            client.table("mart_stock_cards")
            .select("*")
            .eq("is_card_eligible", True)
            .order("snapshot_date", desc=True)
            .range(offset, offset + PAGE_SIZE - 1)
            .execute()
        )
        batch = response.data or []
        raw.extend(batch)
        if len(batch) < PAGE_SIZE:
            break
        offset += PAGE_SIZE
    return raw


def fetch_eligible_cards(client: _SupabaseClient) -> list[dict[str, Any]]:
    """Latest snapshot per (market_code, ticker) for all eligible cards."""
    return dedupe_to_latest_snapshot(fetch_all_eligible_rows(client))


def fetch_all_assessment_rows(client: _SupabaseClient) -> list[dict[str, Any]]:
    """Fetch every card_assessments row — one row per (market_code, ticker), already
    latest-only (no snapshot_date in its key, unlike mart_stock_cards)."""
    raw: list[dict[str, Any]] = []
    offset = 0
    while True:
        response = (
            client.table("card_assessments")
            .select("*")
            .range(offset, offset + PAGE_SIZE - 1)
            .execute()
        )
        batch = response.data or []
        raw.extend(batch)
        if len(batch) < PAGE_SIZE:
            break
        offset += PAGE_SIZE
    return raw


def fetch_card_assessments(client: _SupabaseClient) -> dict[tuple[str, str], dict[str, Any]]:
    """(market_code, ticker) -> assessment row, ready for a keyed join."""
    return {
        (row["market_code"], row["ticker"]): row for row in fetch_all_assessment_rows(client)
    }


def fetch_eligible_cards_with_assessments(client: _SupabaseClient) -> list[dict[str, Any]]:
    """Eligible cards joined with their card_assessments row, when one exists."""
    return attach_assessments(fetch_eligible_cards(client), fetch_card_assessments(client))
