"""The guards in load_constituents and refresh_market each refuse a bad input with a message."""

from __future__ import annotations

from pathlib import Path

import pytest

from ingestion.constituents import refresh, seeds
from ingestion.constituents.refresh import RefreshConfig


def test_a_seed_with_a_dropped_column_names_it(tmp_path: Path, monkeypatch) -> None:
    path = tmp_path / "constituents.csv"
    path.write_text("market_code,ticker,company_name,refreshed_at\nca_tsx60,AEM,Agnico,2026-10-01\n", encoding="utf-8")
    monkeypatch.setattr(seeds, "seed_path", lambda code: path)

    with pytest.raises(ValueError, match=r"missing columns: \['source'\]"):
        seeds.load_constituents("ca_tsx60")


def test_a_missing_seed_file_points_at_the_scripts_that_create_it(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(seeds, "seed_path", lambda code: tmp_path / "absent.csv")

    with pytest.raises(FileNotFoundError, match="refresh_constituents.py or scripts/import_constituents.py"):
        seeds.load_constituents("ca_tsx60")


def _wikipedia(**changes) -> RefreshConfig:
    config = {
        "market_code": "xx_test",
        "provider": "wikipedia",
        "refresh_enabled": True,
        "url": "https://example.test/page",
        "table_index": 0,
        "ticker_column": "Symbol",
        "name_column": "Company",
    }
    config.update(changes)
    return RefreshConfig(**config)


def test_a_manual_market_is_refused_with_its_note() -> None:
    config = RefreshConfig(market_code="xx_test", provider="manual", refresh_enabled=False, notes="update the CSV")
    with pytest.raises(ValueError, match="xx_test uses manual seeds: update the CSV"):
        refresh.refresh_market(config)


def test_a_disabled_market_is_refused_even_with_a_wikipedia_provider() -> None:
    with pytest.raises(ValueError, match="uses manual seeds"):
        refresh.refresh_market(_wikipedia(refresh_enabled=False))


def test_an_unsupported_provider_is_refused() -> None:
    with pytest.raises(ValueError, match="Unsupported provider for xx_test: csv"):
        refresh.refresh_market(_wikipedia(provider="csv"))


@pytest.mark.parametrize("missing", ["url", "table_index", "ticker_column", "name_column"])
def test_an_incomplete_wikipedia_config_is_refused(missing: str, monkeypatch) -> None:
    def _no_network(*args, **kwargs):
        raise AssertionError("the guard must refuse before any request")

    monkeypatch.setattr(refresh.requests, "get", _no_network)
    with pytest.raises(ValueError, match="Incomplete wikipedia config for xx_test"):
        refresh.refresh_market(_wikipedia(**{missing: None}))


def test_a_table_index_beyond_the_page_is_refused(monkeypatch) -> None:
    class _Response:
        text = "<table><tr><th>Symbol</th></tr><tr><td>AAA</td></tr></table>"

        def raise_for_status(self) -> None:
            pass

    monkeypatch.setattr(refresh.requests, "get", lambda *args, **kwargs: _Response())

    with pytest.raises(IndexError, match=r"table_index 3 out of range \(found 1 tables\)"):
        refresh.refresh_market(_wikipedia(table_index=3))
