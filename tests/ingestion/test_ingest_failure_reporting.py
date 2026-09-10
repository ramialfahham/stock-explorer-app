"""Issue #9 finding A3: a price-ingestion failure must not pass unreported.

A failed batch still writes what it did retrieve over the previous complete parquet, with a
fresh mtime and a fresh `ingested_at`. `dbt source freshness` (warn 20d / error 30d) therefore
reads green over missing prices, eligibility is fundamentals-driven so the completeness and
baseline gates do not see it either, and no `check_*` script looks at prices at all.

The run does NOT fail: nothing downstream reads prices, and `call_with_retry` retries rate
limits only, so gating would abort the cycle on unretried transient noise. The counters and the
stderr warning are therefore the whole signal, which is what these tests pin.

No network: `ingest_market` is faked, so these tests pin the reporting contract between it and
`main()`, not the fetch itself."""

from __future__ import annotations

import ingestion.main as main_module
from ingestion.registry import Market

MARKET = Market(
    market_code="test_market",
    index_name="^TEST",
    exchange_suffix="",
    source="yfinance",
    ingest_active=True,
)

_CLEAN = {
    "constituents": 4,
    "tickers_requested": 4,
    "price_rows": 40,
    "price_batches": 2,
    "price_batches_failed": 0,
    "price_batches_empty": 0,
    "price_tickers_missing": 0,
    "fundamentals_rows": 4,
    "fundamentals_ok": 4,
    "fundamentals_failed": 0,
    "fundamentals_skipped": 0,
}


def _run(monkeypatch, stats: dict) -> int:
    monkeypatch.setattr(main_module, "load_markets", lambda active_only=True: [MARKET])
    monkeypatch.setattr(
        main_module, "ingest_market", lambda market, **kwargs: dict(_CLEAN, **stats)
    )
    return main_module.main([])


def test_the_fixture_matches_what_ingest_market_really_returns():
    """`_CLEAN` is hand-written, so it can drift from the real summary and leave these tests
    passing over a shape production never produces. `ingest_market`'s own key set is pinned in
    test_ingest_resume.py; this asserts the fixture agrees with it."""
    assert set(_CLEAN) == {
        "constituents",
        "tickers_requested",
        "price_rows",
        "price_batches",
        "price_batches_failed",
        "price_batches_empty",
        "price_tickers_missing",
        "fundamentals_rows",
        "fundamentals_ok",
        "fundamentals_failed",
        "fundamentals_skipped",
    }


def test_every_price_counter_reaches_the_summary_line(monkeypatch, capsys):
    """The counts exist to be read by an operator. A counter that never prints is a counter
    that does not do its job."""
    _run(monkeypatch, {"price_batches_empty": 2, "price_tickers_missing": 5})
    out = capsys.readouterr().out
    for field in (
        "price_batches=",
        "price_batches_failed=",
        "price_batches_empty=2",
        "price_tickers_missing=5",
    ):
        assert field in out


def test_a_clean_run_still_exits_zero(monkeypatch):
    assert _run(monkeypatch, {}) == 0


def test_a_failed_price_batch_does_not_fail_the_run(monkeypatch):
    """Nothing downstream reads prices, and call_with_retry retries rate limits only, so gating
    would abort the cycle's dbt build, export and assessments on an unretried connection blip
    over data nobody consumes. Owner-decided; the reasoning lives beside the check in
    ingestion/main.py."""
    assert _run(monkeypatch, {"price_batches_failed": 1}) == 0


def test_a_failed_price_batch_still_warns_loudly(monkeypatch, capsys):
    """Not failing the run is only defensible if the loss is impossible to miss in the log. The
    message must name the market and say why no other check will catch it."""
    _run(monkeypatch, {"price_batches_failed": 2})
    err = capsys.readouterr().err
    assert "test_market" in err
    assert "failed" in err
    assert "freshness" in err


def test_a_clean_run_says_nothing_on_stderr(monkeypatch, capsys):
    """A warning that prints every run is a warning nobody reads."""
    _run(monkeypatch, {})
    assert capsys.readouterr().err == ""


def test_empty_batches_and_missing_tickers_do_not_fail_the_run(monkeypatch):
    """Neither is reported as a failure. An empty batch or a symbol absent from the response is
    data missing at source (a delisted ticker, a market with no trading that day), not an error;
    only a raised exception is. Nothing fails the run either way, so the distinction decides
    what the warning fires on, not what the exit code is."""
    assert _run(monkeypatch, {"price_batches_empty": 1, "price_tickers_missing": 3}) == 0
