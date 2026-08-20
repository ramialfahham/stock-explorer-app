"""Supabase mart pagination helpers."""

from __future__ import annotations

from supabase_cards import (  # noqa: E402
    PAGE_SIZE,
    fetch_all_assessment_rows,
    fetch_all_eligible_rows,
    fetch_card_assessments,
    fetch_eligible_cards,
    fetch_eligible_cards_with_assessments,
)


class _FakeResponse:
    def __init__(self, data: list[dict]) -> None:
        self.data = data


class _FakeQuery:
    def __init__(self, pages: list[list[dict]]) -> None:
        self._pages = pages
        self._offset = 0

    def select(self, *_args, **_kwargs) -> _FakeQuery:
        return self

    def eq(self, *_args, **_kwargs) -> _FakeQuery:
        return self

    def order(self, *_args, **_kwargs) -> _FakeQuery:
        return self

    def range(self, start: int, end: int) -> _FakeQuery:
        self._offset = start
        self._end = end
        return self

    def execute(self) -> _FakeResponse:
        page_index = self._offset // PAGE_SIZE
        return _FakeResponse(self._pages[page_index])


class _FakeClient:
    def __init__(self, pages: list[list[dict]]) -> None:
        self._pages = pages

    def table(self, _name: str) -> _FakeQuery:
        return _FakeQuery(self._pages)


def test_fetch_all_eligible_rows_paginates_past_1000() -> None:
    first = [{"market_code": "us_sp500", "ticker": f"T{i}", "snapshot_date": "2026-06-01"} for i in range(PAGE_SIZE)]
    second = [{"market_code": "us_sp500", "ticker": "EXTRA", "snapshot_date": "2026-06-02"}]
    client = _FakeClient([first, second])
    rows = fetch_all_eligible_rows(client)
    assert len(rows) == PAGE_SIZE + 1


class _FakeMultiTableClient:
    """Unlike _FakeClient, returns different page data per table name — needed to test
    a join across mart_stock_cards and card_assessments, two genuinely different tables."""

    def __init__(self, tables: dict[str, list[list[dict]]]) -> None:
        self._tables = tables

    def table(self, name: str) -> _FakeQuery:
        return _FakeQuery(self._tables[name])


def test_fetch_all_assessment_rows_paginates_past_1000() -> None:
    first = [{"market_code": "us_sp500", "ticker": f"T{i}"} for i in range(PAGE_SIZE)]
    second = [{"market_code": "us_sp500", "ticker": "EXTRA"}]
    client = _FakeMultiTableClient({"card_assessments": [first, second]})
    rows = fetch_all_assessment_rows(client)
    assert len(rows) == PAGE_SIZE + 1


def test_fetch_card_assessments_keys_by_market_and_ticker() -> None:
    pages = [[
        {"market_code": "us_sp500", "ticker": "ADI", "health_verdict": "green", "ai_read": "text"},
    ]]
    client = _FakeMultiTableClient({"card_assessments": pages})
    result = fetch_card_assessments(client)
    assert result[("us_sp500", "ADI")]["health_verdict"] == "green"


def test_fetch_eligible_cards_with_assessments_joins_across_tables() -> None:
    mart_pages = [[
        {
            "market_code": "us_sp500",
            "ticker": "ADI",
            "snapshot_date": "2026-06-09",
            "is_card_eligible": True,
            "business_summary": "Latest Yahoo summary.",
        },
    ]]
    assessment_pages = [[
        {"market_code": "us_sp500", "ticker": "ADI", "health_verdict": "green", "ai_read": "Sturdy."},
    ]]
    client = _FakeMultiTableClient(
        {"mart_stock_cards": mart_pages, "card_assessments": assessment_pages}
    )
    cards = fetch_eligible_cards_with_assessments(client)
    assert len(cards) == 1
    assert cards[0]["health_verdict"] == "green"
    assert cards[0]["ai_read"] == "Sturdy."


def test_fetch_eligible_cards_with_assessments_omits_missing_assessment() -> None:
    """A card with no matching card_assessments row (pipeline lag) still comes back —
    just without the assessment fields, never a placeholder."""
    mart_pages = [[
        {
            "market_code": "us_sp500",
            "ticker": "NEW",
            "snapshot_date": "2026-06-09",
            "is_card_eligible": True,
        },
    ]]
    client = _FakeMultiTableClient({"mart_stock_cards": mart_pages, "card_assessments": [[]]})
    cards = fetch_eligible_cards_with_assessments(client)
    assert len(cards) == 1
    assert "health_verdict" not in cards[0]


def test_fetch_eligible_cards_keeps_latest_snapshot() -> None:
    pages = [[
        {
            "market_code": "us_sp500",
            "ticker": "ADI",
            "snapshot_date": "2026-06-09",
            "is_card_eligible": True,
            "business_summary": "Latest Yahoo summary.",
        },
        {
            "market_code": "us_sp500",
            "ticker": "ADI",
            "snapshot_date": "2026-05-01",
            "is_card_eligible": True,
            "business_summary": None,
        },
    ]]
    cards = fetch_eligible_cards(_FakeClient(pages))
    assert len(cards) == 1
    assert cards[0]["business_summary"] == "Latest Yahoo summary."
