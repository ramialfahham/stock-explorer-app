"""Supabase mart pagination helpers."""

from __future__ import annotations

from supabase_cards import PAGE_SIZE, fetch_all_eligible_rows, fetch_eligible_cards  # noqa: E402


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
