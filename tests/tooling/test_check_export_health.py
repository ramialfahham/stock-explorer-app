"""Tests for export health pre-export gates."""

from __future__ import annotations

from check_export_health import (  # noqa: E402
    assess_export_health,
    dedupe_to_latest_snapshot,
)


def _eligible_row(
    *,
    market_code: str = "us_sp500",
    ticker: str = "TEST",
    snapshot_date: str = "2026-06-01",
    business_summary: str | None = "Summary text.",
) -> dict:
    return {
        "market_code": market_code,
        "ticker": ticker,
        "is_card_eligible": True,
        "snapshot_date": snapshot_date,
        "business_summary": business_summary,
    }


def test_dedupe_coalesces_summary_from_older_snapshot() -> None:
    cards = [
        _eligible_row(ticker="TEST", snapshot_date="2026-06-09", business_summary=None),
        _eligible_row(ticker="TEST", snapshot_date="2026-05-01", business_summary="Older summary."),
    ]
    deduped = dedupe_to_latest_snapshot(cards)
    assert len(deduped) == 1
    assert deduped[0]["business_summary"] == "Older summary."


def test_assess_export_health_passes_when_fill_rate_high() -> None:
    cards = [
        _eligible_row(ticker=f"T{i}", business_summary=f"Summary {i}.")
        for i in range(100)
    ]
    cards.append(_eligible_row(ticker="MISSING", business_summary=None))
    report, failures = assess_export_health(cards, min_fill_rate=0.95, max_missing=5)
    assert failures == []
    assert report.deduped_eligible == 101
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
