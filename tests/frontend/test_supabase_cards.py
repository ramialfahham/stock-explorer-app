"""Supabase deck/card fetching: pagination, column narrowing, and the card-detail join."""

from __future__ import annotations

from supabase_cards import (  # noqa: E402
    DECK_COLUMNS,
    UNDEFINED_COLUMN_SQLSTATE,
    PAGE_SIZE,
    export_lacks_business_summary,
    fetch_card_detail,
    fetch_deck,
    fetch_deck_rows,
    is_undefined_column_error,
)


class _FakeResponse:
    def __init__(self, data: list[dict]) -> None:
        self.data = data


class _FakeQuery:
    def __init__(self, table: str, pages: list[list[dict]], log: list[tuple]) -> None:
        self._table = table
        self._pages = pages
        self._log = log
        self._offset = 0

    def select(self, columns: str = "*", *_args, **_kwargs) -> _FakeQuery:
        self._log.append(("select", self._table, columns))
        return self

    def eq(self, column: str, value: object) -> _FakeQuery:
        self._log.append(("eq", self._table, column, value))
        return self

    def gt(self, column: str, value: object) -> _FakeQuery:
        self._log.append(("gt", self._table, column, value))
        return self

    def order(self, *_args, **_kwargs) -> _FakeQuery:
        return self

    def range(self, start: int, end: int) -> _FakeQuery:
        self._offset = start
        self._end = end
        return self

    def execute(self) -> _FakeResponse:
        page_index = self._offset // PAGE_SIZE
        if page_index >= len(self._pages):
            return _FakeResponse([])
        return _FakeResponse(self._pages[page_index])


class _FakeClient:
    """Per-table page data, plus a log of every select/filter the code issued."""

    def __init__(self, tables: dict[str, list[list[dict]]]) -> None:
        self._tables = tables
        self.log: list[tuple] = []

    def table(self, name: str) -> _FakeQuery:
        return _FakeQuery(name, self._tables.get(name, [[]]), self.log)

    def selects_for(self, table: str) -> list[str]:
        return [c for kind, t, c in (e for e in self.log if e[0] == "select") if t == table]

    def tables_touched(self) -> set[str]:
        return {entry[1] for entry in self.log}


def _mart(**overrides) -> dict:
    row = {
        "market_code": "us_sp500",
        "ticker": "ADI",
        "snapshot_date": "2026-06-09",
        "is_card_eligible": True,
    }
    row.update(overrides)
    return row


def test_fetch_deck_rows_paginates_past_1000() -> None:
    first = [_mart(ticker=f"T{i}") for i in range(PAGE_SIZE)]
    second = [_mart(ticker="EXTRA", snapshot_date="2026-06-02")]
    client = _FakeClient({"mart_stock_cards": [first, second]})
    assert len(fetch_deck_rows(client)) == PAGE_SIZE + 1


def test_fetch_deck_requests_only_the_slim_column_set() -> None:
    """The cold path's whole cost is this select list. `select=*` here is the regression that
    put ~9-18 MB in front of every first-time visitor."""
    client = _FakeClient({"mart_stock_cards": [[_mart()]]})
    fetch_deck(client)
    selects = client.selects_for("mart_stock_cards")
    assert selects == [",".join(DECK_COLUMNS)]
    assert "*" not in selects


def test_deck_columns_exclude_the_heavy_card_face_fields() -> None:
    """business_summary is 66% of the mart payload and ai_read is per-card narrative text.
    Neither is read by any list, filter, count or search path."""
    assert "business_summary" not in DECK_COLUMNS
    assert "ai_read" not in DECK_COLUMNS
    assert not [c for c in DECK_COLUMNS if c.startswith("sector_")]


def test_fetch_deck_does_not_query_card_assessments() -> None:
    """health_verdict/ai_read are card-face only, so joining them into the deck would buy two
    round trips and ~900 KB of text nothing on screen reads yet."""
    client = _FakeClient({"mart_stock_cards": [[_mart()]]})
    fetch_deck(client)
    assert client.tables_touched() == {"mart_stock_cards"}


def test_fetch_deck_keeps_latest_snapshot_per_ticker() -> None:
    pages = [[_mart(snapshot_date="2026-06-09"), _mart(snapshot_date="2026-05-01")]]
    cards = fetch_deck(_FakeClient({"mart_stock_cards": pages}))
    assert len(cards) == 1
    assert cards[0]["snapshot_date"] == "2026-06-09"


def test_fetch_card_detail_returns_full_row_with_assessment() -> None:
    mart = [[_mart(business_summary="Latest Yahoo summary.", ebit_margin_pct=12.5)]]
    assessments = [[{
        "market_code": "us_sp500",
        "ticker": "ADI",
        "health_verdict": "green",
        "ai_read": "Sturdy.",
    }]]
    client = _FakeClient({"mart_stock_cards": mart, "card_assessments": assessments})
    card = fetch_card_detail(client, "us_sp500", "ADI")
    assert card is not None
    assert card["business_summary"] == "Latest Yahoo summary."
    assert card["ebit_margin_pct"] == 12.5
    assert card["health_verdict"] == "green"
    assert card["ai_read"] == "Sturdy."
    assert client.selects_for("mart_stock_cards") == ["*"]


def test_fetch_card_detail_omits_missing_assessment() -> None:
    """A card with no card_assessments row (the assessments step runs after export and can lag
    a newly-eligible card) still renders, just without the health block."""
    client = _FakeClient({"mart_stock_cards": [[_mart()]], "card_assessments": [[]]})
    card = fetch_card_detail(client, "us_sp500", "ADI")
    assert card is not None
    assert "health_verdict" not in card


def test_fetch_card_detail_backfills_business_summary_across_snapshots() -> None:
    """The newest snapshot can be missing a description Yahoo returned on an older one. The
    deck no longer carries business_summary at all, so this backfill only survives if the
    card-detail fetch runs the same dedupe over that ticker's own snapshots."""
    mart = [[
        _mart(snapshot_date="2026-06-09", business_summary=None),
        _mart(snapshot_date="2026-05-01", business_summary="Older but real."),
    ]]
    client = _FakeClient({"mart_stock_cards": mart, "card_assessments": [[]]})
    card = fetch_card_detail(client, "us_sp500", "ADI")
    assert card is not None
    assert card["snapshot_date"] == "2026-06-09"
    assert card["business_summary"] == "Older but real."


def test_fetch_card_detail_returns_none_for_unknown_ticker() -> None:
    client = _FakeClient({"mart_stock_cards": [[]], "card_assessments": [[]]})
    assert fetch_card_detail(client, "us_sp500", "NOPE") is None


def test_export_lacks_business_summary_is_false_when_any_row_has_one() -> None:
    client = _FakeClient({"mart_stock_cards": [[{"ticker": "ADI"}]]})
    assert export_lacks_business_summary(client) is False
    assert ("gt", "mart_stock_cards", "business_summary", "") in client.log


def test_export_lacks_business_summary_is_true_when_none_do() -> None:
    client = _FakeClient({"mart_stock_cards": [[]]})
    assert export_lacks_business_summary(client) is True


def test_deck_columns_cover_every_lead_metric() -> None:
    """The list row's lead metric is chosen per company_type. Adding a fourth type with a
    fourth lead metric and forgetting DECK_COLUMNS would blank that metric on every row of
    that type with the rest of the suite green, because the fixtures derive their keys from
    DECK_COLUMNS rather than pinning it."""
    from card_copy import _LEAD_METRIC_BY_TYPE

    assert set(_LEAD_METRIC_BY_TYPE.values()) <= set(DECK_COLUMNS)


def test_deck_columns_cover_the_row_and_filter_fields() -> None:
    """A hand-copied literal of the fields read by filter_pool, sectors_for_market,
    eligible_counts_by_market, latest_snapshot_label, saved_row_subtitle, metric_label and the
    title/sort lambdas. Deliberately a literal, not a derivation: it catches a REMOVAL from
    DECK_COLUMNS, but it cannot catch a newly-read field that nobody adds here. The lead-metric
    test above is the derived one."""
    required = {
        "market_code",
        "ticker",
        "company_name",
        "sector",
        "is_card_eligible",
        "snapshot_date",
        "company_type",
        "currency",
        "ebit_margin_basis",
    }
    assert required <= set(DECK_COLUMNS)


class _RaisingClient:
    """Raises on `.gt()`, the way PostgREST does when the column does not exist."""

    def __init__(self, exc: Exception) -> None:
        self._exc = exc

    def table(self, _name: str) -> _RaisingClient:
        return self

    def select(self, *_a, **_k) -> _RaisingClient:
        return self

    def eq(self, *_a, **_k) -> _RaisingClient:
        return self

    def gt(self, *_a, **_k):
        raise self._exc


class _ApiError(Exception):
    def __init__(self, code: str) -> None:
        super().__init__("column mart_stock_cards.business_summary does not exist")
        self.code = code


def test_is_undefined_column_error_matches_the_sqlstate_attribute() -> None:
    assert is_undefined_column_error(_ApiError(UNDEFINED_COLUMN_SQLSTATE)) is True


def test_is_undefined_column_error_matches_the_sqlstate_in_the_message() -> None:
    assert is_undefined_column_error(RuntimeError(f"PGRST: {UNDEFINED_COLUMN_SQLSTATE}")) is True


def test_is_undefined_column_error_ignores_unrelated_failures() -> None:
    """A transient network blip must not raise an operator data-quality alarm."""
    assert is_undefined_column_error(TimeoutError("connection reset")) is False


def test_export_probe_propagates_an_undefined_column_error() -> None:
    """It must NOT be swallowed inside the probe -- app.py maps it to "descriptions missing",
    which is exactly what a pre-migration-004 export means."""
    client = _RaisingClient(_ApiError(UNDEFINED_COLUMN_SQLSTATE))
    try:
        export_lacks_business_summary(client)
    except _ApiError:
        return
    raise AssertionError("expected the undefined-column error to propagate")
