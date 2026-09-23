"""Load cards (current_cards view, mart_stock_cards) and card_assessments from Supabase."""

from __future__ import annotations

from typing import Any, Callable, Protocol

from explore_filters import attach_assessments, dedupe_to_latest_snapshot

# PostgREST default max rows per request.
PAGE_SIZE = 1000

# Only what the list, search, filter and sort paths read: every column added here is paid by
# every visitor, while the card face fetches its other ~67 columns one card at a time.
DECK_COLUMNS: tuple[str, ...] = (
    "market_code",
    "ticker",
    "company_name",
    "sector",
    "is_card_eligible",
    "snapshot_date",
    "company_type",
    "currency",
    "ebit_margin_basis",
    "ebit_margin_pct",
    "statement_roe_pct",
    "cash_runway_months",
    # A preset metric missing from the rows makes that preset silently match every card.
    "net_debt_to_ebitda",
    "revenue_growth_yoy_pct",
)


class _TableQuery(Protocol):
    def select(self, *args: Any, **kwargs: Any) -> _TableQuery: ...
    def eq(self, *args: Any, **kwargs: Any) -> _TableQuery: ...
    def gt(self, *args: Any, **kwargs: Any) -> _TableQuery: ...
    def order(self, *args: Any, **kwargs: Any) -> _TableQuery: ...
    def range(self, *args: Any, **kwargs: Any) -> _TableQuery: ...
    def execute(self) -> Any: ...


class _SupabaseClient(Protocol):
    def table(self, name: str) -> _TableQuery: ...


def _paginate(build_query: Callable[[int], _TableQuery]) -> list[dict[str, Any]]:
    """Drain a PostgREST select, which caps an unbounded response at PAGE_SIZE rows."""
    rows: list[dict[str, Any]] = []
    offset = 0
    while True:
        batch = build_query(offset).execute().data or []
        rows.extend(batch)
        if len(batch) < PAGE_SIZE:
            break
        offset += PAGE_SIZE
    return rows


def fetch_deck_rows(client: _SupabaseClient) -> list[dict[str, Any]]:
    """Every eligible current card, narrowed to DECK_COLUMNS; stale companies are already out."""
    select = ",".join(DECK_COLUMNS)
    return _paginate(
        lambda offset: (
            client.table("current_cards")
            .select(select)
            .eq("is_card_eligible", True)
            .order("snapshot_date", desc=True)
            .range(offset, offset + PAGE_SIZE - 1)
        )
    )


def fetch_deck(client: _SupabaseClient) -> list[dict[str, Any]]:
    """The deck: latest snapshot per (market_code, ticker), slim columns only.

    No card_assessments join -- `health_verdict`/`ai_read` are read only by the card face
    (card_ui/card_copy), never by a list row, so fetching them here would add two round trips
    and ~900 KB to the cold path for data nothing on screen uses yet.
    """
    return dedupe_to_latest_snapshot(fetch_deck_rows(client))


def fetch_card_detail(
    client: _SupabaseClient, market_code: str, ticker: str
) -> dict[str, Any] | None:
    """The full row for one card, assessment attached. None when the ticker has no rows.

    Runs the same dedupe_to_latest_snapshot as the deck, over just this ticker's snapshots, so
    the cross-snapshot `business_summary` backfill it performs is preserved rather than
    reimplemented.
    """
    rows = (
        client.table("mart_stock_cards")
        .select("*")
        .eq("market_code", market_code)
        .eq("ticker", ticker)
        .order("snapshot_date", desc=True)
        .execute()
        .data
        or []
    )
    if not rows:
        return None

    assessment_rows = (
        client.table("card_assessments")
        .select("*")
        .eq("market_code", market_code)
        .eq("ticker", ticker)
        .execute()
        .data
        or []
    )
    assessments = {(market_code, ticker): assessment_rows[0]} if assessment_rows else {}
    return attach_assessments(dedupe_to_latest_snapshot(rows), assessments)[0]


# Postgres "column does not exist": the probe below treats it as an answer (a pre-migration-004
# export), not a failure.
UNDEFINED_COLUMN_SQLSTATE = "42703"


def is_undefined_column_error(exc: BaseException) -> bool:
    code = getattr(exc, "code", None)
    if code is not None and str(code) == UNDEFINED_COLUMN_SQLSTATE:
        return True
    return UNDEFINED_COLUMN_SQLSTATE in str(exc)


def export_lacks_business_summary(client: _SupabaseClient) -> bool:
    """True when no eligible card in the export has a company description.

    Answers the overflow menu's export diagnostic without putting `business_summary` back on
    the deck. `gt("business_summary", "")` is NULL-safe in Postgres (NULL fails the comparison
    rather than passing it), so one row coming back proves at least one description survived
    the export; the range caps the response at that single row.
    """
    rows = (
        client.table("mart_stock_cards")
        .select("ticker")
        .eq("is_card_eligible", True)
        .gt("business_summary", "")
        .range(0, 0)
        .execute()
        .data
        or []
    )
    return not rows
