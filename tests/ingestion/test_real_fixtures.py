"""The real-shaped fixtures: recorded yfinance and Wikipedia payloads replayed offline through
the real ingestion code. CI's `validate:full` takes the replay on through dbt to the golden mart
(`scripts/check_real_fixture_mart.py`); these pin the harness and the Wikipedia half."""

from __future__ import annotations

import dataclasses
import gzip
import json
import socket
from pathlib import Path
from unittest import mock

import pandas as pd
import pytest

import record_ingestion_fixtures as recorder
import replay_ingestion_fixtures as replay
from ingestion.constituents import refresh, seeds
from ingestion.registry import load_markets

FIXTURE_DIR = Path(__file__).resolve().parents[1] / "fixtures" / "real"
MANIFEST = json.loads((FIXTURE_DIR / "manifest.json").read_text(encoding="utf-8"))
ACTIVE = [m.market_code for m in load_markets(active_only=True)]

# A recorded page whose parse no longer reproduces the committed seed, each with its issue.
# The test below fails if an entry stops drifting, so a fixed one cannot linger here.
KNOWN_PAGE_DRIFT: dict[str, str] = {}
MIN_OVERLAP = refresh.MIN_SEED_OVERLAP


def test_every_active_market_is_recorded_with_its_listed_tickers() -> None:
    assert sorted(MANIFEST["markets"]) == sorted(ACTIVE)
    for code in ACTIVE:
        assert MANIFEST["markets"][code]["tickers"] == recorder.fixture_tickers(code), code


def test_recorded_files_stay_under_the_pre_commit_size_limit() -> None:
    oversized = [p.name for p in FIXTURE_DIR.rglob("*") if p.is_file() and p.stat().st_size > 500_000]
    assert oversized == []


def test_a_fixture_ticker_refuses_an_attribute_that_was_not_recorded() -> None:
    payload = json.loads((FIXTURE_DIR / "yfinance" / "us_sp500" / "AAPL.json").read_text(encoding="utf-8"))
    ticker = replay.FixtureTicker(payload)
    assert ticker.info
    with pytest.raises(AttributeError, match="not recorded"):
        _ = ticker.dividends


def test_a_fixture_download_refuses_an_unrecorded_symbol() -> None:
    fake = replay.FixtureYfinance("us_sp500", pd.Timestamp("2026-10-05").date())
    with pytest.raises(KeyError, match="no recorded prices"):
        fake.download(["MSFT"])


def test_replay_writes_every_market_offline(tmp_path, monkeypatch) -> None:
    def _no_network(*_args, **_kwargs):
        raise AssertionError("the replay opened a network connection")

    monkeypatch.setattr(socket, "socket", _no_network)
    results = replay.replay(tmp_path, pd.Timestamp("2026-10-05").date())
    assert sorted(results) == sorted(ACTIVE)
    for code, stats in results.items():
        recorded = len(MANIFEST["markets"][code]["tickers"])
        assert stats["fundamentals_rows"] == recorded, code
        assert stats["price_batches_failed"] == 0, code
        for name in ("yf_constituents", "yf_daily_prices", "yf_fundamentals"):
            assert (tmp_path / code / f"{name}.parquet").exists(), f"{code}/{name}"


@pytest.mark.parametrize("today, last_trading_day", [
    ("2026-10-05", "2026-10-05"),  # a Monday ends on itself
    ("2026-10-10", "2026-10-09"),  # a Saturday ends on the Friday before, never after
])
def test_replayed_prices_end_on_or_before_the_replay_date(tmp_path, today, last_trading_day) -> None:
    replay.replay(tmp_path, pd.Timestamp(today).date())
    prices = pd.read_parquet(tmp_path / "us_sp500" / "yf_daily_prices.parquet")
    assert str(max(prices["trading_date"])) == last_trading_day


def _parse_recorded_page(code: str, tmp_path: Path) -> tuple[pd.DataFrame, int]:
    html = gzip.open(FIXTURE_DIR / "wikipedia" / f"{code}.html.gz", "rt", encoding="utf-8").read()

    class _Response:
        text = html

        def raise_for_status(self) -> None:
            pass

    out = tmp_path / f"{code}.csv"
    with mock.patch.object(refresh.requests, "get", lambda *a, **k: _Response()), \
            mock.patch.object(seeds, "seed_path", lambda c: out):
        count = refresh.refresh_market(refresh.load_refresh_configs()[code])
    return pd.read_csv(out, dtype=str, na_filter=False), count


WIKIPEDIA_MARKETS = sorted(c for c in ACTIVE if MANIFEST["markets"][c].get("wikipedia"))


@pytest.mark.parametrize("code", WIKIPEDIA_MARKETS)
def test_recorded_wikipedia_page_reproduces_the_committed_seed(code: str, tmp_path) -> None:
    """The configured table_index and columns still parse the page into this market's seed:
    no blank or "nan" ticker, and most committed tickers present (index membership moves
    between a seed refresh and a recording, so this is an overlap, not equality)."""
    parsed, _ = _parse_recorded_page(code, tmp_path)
    committed = pd.read_csv(seeds.seed_path(code), dtype=str, na_filter=False)
    tickers = set(parsed["ticker"])
    assert not tickers & {"", "nan", "None"}
    overlap = len(tickers & set(committed["ticker"])) / len(committed)
    if code in KNOWN_PAGE_DRIFT:
        assert overlap < MIN_OVERLAP, f"{code} no longer drifts; remove it from KNOWN_PAGE_DRIFT"
    else:
        assert overlap >= MIN_OVERLAP, f"{code}: only {overlap:.0%} of the seed parsed from the page"


def test_recorded_obx_page_loses_its_exchange_prefix(tmp_path) -> None:
    parsed, count = _parse_recorded_page("no_obx", tmp_path)
    assert "AKRBP" in set(parsed["ticker"])
    assert not [t for t in parsed["ticker"] if t.startswith("OSE")]
    assert count == len(parsed)


def test_recorded_tsx60_page_counts_only_the_rows_written(tmp_path) -> None:
    """The table ends in an empty footer row the writer drops; the count must not include it."""
    parsed, count = _parse_recorded_page("ca_tsx60", tmp_path)
    assert count == len(parsed) == 60
    assert "NA" in set(parsed["ticker"])


def test_dax_page_without_strip_suffix_is_refused_against_the_committed_seed(tmp_path) -> None:
    """The DAX page writes ADS.DE where the seed keeps ADS. Without `strip_suffix` a refresh
    would re-key all 40 cards; the overlap check refuses it and leaves the seed as it was."""
    html = gzip.open(FIXTURE_DIR / "wikipedia" / "de_dax.html.gz", "rt", encoding="utf-8").read()

    class _Response:
        text = html

        def raise_for_status(self) -> None:
            pass

    seed = tmp_path / "constituents.csv"
    seed.write_bytes(seeds.seed_path("de_dax").read_bytes())
    config = dataclasses.replace(refresh.load_refresh_configs()["de_dax"], strip_suffix=None)
    with mock.patch.object(refresh.requests, "get", lambda *a, **k: _Response()), \
            mock.patch.object(seeds, "seed_path", lambda c: seed):
        with pytest.raises(ValueError, match="seed not written"):
            refresh.refresh_market(config)
    assert seed.read_bytes() == seeds.seed_path("de_dax").read_bytes()
