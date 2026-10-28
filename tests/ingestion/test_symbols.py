"""The Yahoo symbol rules decide which tickers a download asks for, so each branch is pinned."""

from __future__ import annotations

import pytest

from ingestion.yfinance.symbols import to_yfinance_download_ticker, to_yfinance_ticker


@pytest.mark.parametrize(
    ("local", "suffix", "expected"),
    [
        ("AAPL", "", "AAPL"),
        ("SAP", ".DE", "SAP.DE"),
        ("BT-A.L", ".L", "BT-A.L"),
        ("  AAPL ", "", "AAPL"),
    ],
)
def test_info_symbol_adds_the_suffix_unless_the_ticker_already_has_a_dot(local, suffix, expected) -> None:
    assert to_yfinance_ticker(local, suffix) == expected


@pytest.mark.parametrize(
    ("local", "suffix", "expected"),
    [
        ("BRK.B", "", "BRK-B"),
        ("AAPL", "", "AAPL"),
        ("SAP", ".DE", "SAP.DE"),
        ("BT.A", ".L", "BT.A"),
    ],
)
def test_download_symbol_turns_a_us_class_share_dot_into_a_hyphen_only(local, suffix, expected) -> None:
    assert to_yfinance_download_ticker(local, suffix) == expected
