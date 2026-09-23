"""Load cards (current_cards view, mart_stock_cards) and card_assessments from Supabase."""

from __future__ import annotations

from typing import Any, Callable, Protocol

from explore_filters import attach_assessments, dedupe_to_latest_snapshot

# PostgREST default max rows per request.
PAGE_SIZE = 1000

# The only columns the Discover/Saved list, filter, count, sort, and search paths read. The card
# FACE needs the other ~67 columns, but it needs them for one card at a time -- fetching all of
# them for the whole deck downloads ~9-18 MB before anything can render, and `business_summary`
# alone is 66% of that. Keep this list minimal and justified:
#   market_code, ticker            -- the card key, plus search matching
#   company_name, sector           -- row title/subtitle, search matching, sector filter
#   is_card_eligible               -- filter_pool's eligibility gate
#   snapshot_date                  -- dedupe_to_latest_snapshot, Saved's freshness line
#   company_type, currency         -- pick and format the row's lead metric
#   ebit_margin_basis              -- metric_label()'s "(annual)" variant
#   ebit/roe/runway                -- card_copy._LEAD_METRIC_BY_TYPE, one per company type
#   net_debt_to_ebitda             -- explore_filters.METRIC_PRESETS "Low debt"
#   revenue_growth_yoy_pct         -- explore_filters.METRIC_PRESETS "Growing revenue"
# net_debt_to_ebitda/revenue_growth_yoy_pct were missing here until a real card_matches_metric_
# presets() bug: a metric absent from the row is treated as "unknown, don't exclude" (the same
# omit-never-fake rule as everywhere else in this app), so both presets silently matched every
# card regardless of its actual debt or growth. Two more floats per row costs ~50-60 KB across
# the whole deck (measured), against an already-~1.4 MB payload -- not the kind of cost this
# column list exists to keep out. Adding a column here costs every visitor on the cold path;
# adding one to the card face costs nobody until that card is opened.
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


# Postgres SQLSTATE for "column does not exist". PostgREST passes it through as the error
# `code`. Named because the probe below MUST treat it as an answer, not a failure: an export
# predating migration 004 has no `business_summary` column at all, which is precisely the
# state the overflow menu's caption exists to announce.
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
