"""Tests for export health pre-export gates."""

from __future__ import annotations

from check_export_health import assess_export_health  # noqa: E402


def _eligible_row(
    *,
    market_code: str = "us_sp500",
    ticker: str = "TEST",
    business_summary: str | None = "Summary text.",
) -> dict:
    return {
        "market_code": market_code,
        "ticker": ticker,
        "is_card_eligible": True,
        "business_summary": business_summary,
    }


def test_assess_export_health_passes_when_fill_rate_high() -> None:
    cards = [
        _eligible_row(ticker=f"T{i}", business_summary=f"Summary {i}.")
        for i in range(100)
    ]
    cards.append(_eligible_row(ticker="MISSING", business_summary=None))
    report, failures = assess_export_health(cards, min_fill_rate=0.95, max_missing=5)
    assert failures == []
    assert report.eligible == 101
    assert report.with_business_summary == 100
    assert report.fill_rate == 100 / 101


def test_assess_export_health_fails_when_fill_rate_too_low() -> None:
    cards = [
        _eligible_row(ticker="A", business_summary="Has text."),
        _eligible_row(ticker="B", business_summary=None),
        _eligible_row(ticker="C", business_summary=None),
    ]
    _report, failures = assess_export_health(cards, min_fill_rate=0.95, max_missing=5)
    assert any("fill rate" in msg for msg in failures)


def test_assess_export_health_fails_when_too_many_missing() -> None:
    cards = [_eligible_row(ticker=f"M{i}", business_summary=None) for i in range(6)]
    _report, failures = assess_export_health(cards, min_fill_rate=0.0, max_missing=5)
    assert any("exceeds max" in msg for msg in failures)


def test_assess_export_health_required_ticker() -> None:
    cards = [_eligible_row(ticker="CI01", business_summary="Fixture summary.")]
    _report, failures = assess_export_health(
        cards,
        min_fill_rate=0.0,
        max_missing=99,
        required_tickers={("us_sp500", "CI01")},
    )
    assert failures == []

    _report, failures = assess_export_health(
        cards,
        min_fill_rate=0.0,
        max_missing=99,
        required_tickers={("us_sp500", "ABNB")},
    )
    assert any("required ticker missing" in msg for msg in failures)


def test_assess_export_health_names_the_failure_in_plain_words() -> None:
    _report, failures = assess_export_health([], min_fill_rate=0.0, max_missing=99)
    assert failures == ["no card-eligible rows in mart_stock_cards"]

    cards = [_eligible_row(ticker="CI01", business_summary="Fixture summary.")]
    _report, failures = assess_export_health(
        cards,
        min_fill_rate=0.0,
        max_missing=99,
        required_tickers={("us_sp500", "ABNB")},
    )
    assert failures == ["required ticker missing from eligible cards: us_sp500:ABNB"]

    cards = [
        _eligible_row(ticker="A", business_summary="Has text."),
        _eligible_row(ticker="B", business_summary=None),
    ]
    _report, failures = assess_export_health(cards, min_fill_rate=0.95, max_missing=99)
    assert failures == ["business_summary fill rate 50.0% below minimum 95.0% (1/2 eligible)"]


def test_assess_export_health_counts_the_rows_it_is_given() -> None:
    cards = [
        _eligible_row(ticker="SAME", business_summary="First row."),
        _eligible_row(ticker="SAME", business_summary="Second row."),
    ]
    report, _failures = assess_export_health(cards, min_fill_rate=0.0, max_missing=99)
    assert report.eligible == 2


def test_assess_export_health_fails_a_required_ticker_with_an_empty_summary() -> None:
    cards = [_eligible_row(ticker="CI01", business_summary="  ")]
    _report, failures = assess_export_health(
        cards,
        min_fill_rate=0.0,
        max_missing=99,
        required_tickers={("us_sp500", "CI01")},
    )
    assert failures == ["required ticker us_sp500:CI01 has empty business_summary"]
