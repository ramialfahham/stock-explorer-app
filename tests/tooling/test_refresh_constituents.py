"""scripts/refresh_constituents.py: a failed market turns into exit 1 without stopping the others."""

from __future__ import annotations

import pytest

import refresh_constituents
from ingestion.constituents.refresh import RefreshConfig
from ingestion.registry import Market


def _market(code: str) -> Market:
    return Market(market_code=code, index_name="^X", exchange_suffix="", source="yfinance", ingest_active=True)


def _config(code: str) -> RefreshConfig:
    return RefreshConfig(market_code=code, provider="wikipedia", refresh_enabled=True)


@pytest.fixture
def two_markets(monkeypatch: pytest.MonkeyPatch) -> list[str]:
    monkeypatch.setattr(
        refresh_constituents, "load_refresh_configs", lambda: {"bad": _config("bad"), "good": _config("good")}
    )
    monkeypatch.setattr(refresh_constituents, "load_markets", lambda active_only=False: [_market("bad"), _market("good")])
    refreshed: list[str] = []

    def fake_refresh(config: RefreshConfig) -> int:
        if config.market_code == "bad":
            raise RuntimeError("boom")
        refreshed.append(config.market_code)
        return 2

    monkeypatch.setattr(refresh_constituents, "refresh_market", fake_refresh)
    return refreshed


def test_a_failed_market_returns_one_names_the_market_and_the_others_still_refresh(two_markets, capsys) -> None:
    assert refresh_constituents.main([]) == 1

    captured = capsys.readouterr()
    assert "bad: failed: boom" in captured.err
    assert "good: refreshed 2 tickers" in captured.out
    assert two_markets == ["good"]


def test_all_markets_refreshing_returns_zero(two_markets, capsys) -> None:
    assert refresh_constituents.main(["--market", "good"]) == 0
    assert two_markets == ["good"]


def test_no_selected_market_returns_one(two_markets, capsys) -> None:
    assert refresh_constituents.main(["--market", "nothing"]) == 1
    assert "No refresh-enabled markets selected." in capsys.readouterr().err
    assert two_markets == []
