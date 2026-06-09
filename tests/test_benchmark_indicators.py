"""Benchmark indicator helpers (Task 2 scanability)."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FRONTEND = ROOT / "frontend"
if str(FRONTEND) not in sys.path:
    sys.path.insert(0, str(FRONTEND))

from card_copy import (  # noqa: E402
    benchmark_indicator,
    benchmark_indicator_label,
    benchmark_position,
)


def _card(**overrides: object) -> dict:
    base = {
        "sector_peer_count": 10,
        "forward_pe": 20.0,
        "sector_median_forward_pe": 18.0,
    }
    base.update(overrides)
    return base


def test_benchmark_position_above_below_at() -> None:
    card = _card(forward_pe=20.0, sector_median_forward_pe=18.0)
    assert benchmark_position(card, "forward_pe", "sector_median_forward_pe") == "above"

    card = _card(forward_pe=15.0, sector_median_forward_pe=18.0)
    assert benchmark_position(card, "forward_pe", "sector_median_forward_pe") == "below"

    card = _card(forward_pe=18.0, sector_median_forward_pe=18.0)
    assert benchmark_position(card, "forward_pe", "sector_median_forward_pe") == "at"


def test_benchmark_indicator_neutral_symbols() -> None:
    card = _card(forward_pe=20.0, sector_median_forward_pe=18.0)
    assert benchmark_indicator(card, "forward_pe", "sector_median_forward_pe") == "↑"
    assert benchmark_indicator_label(card, "forward_pe", "sector_median_forward_pe") == (
        "Higher than sector median"
    )


def test_benchmark_hidden_when_peer_threshold_not_met() -> None:
    card = _card(sector_peer_count=7)
    assert benchmark_indicator(card, "forward_pe", "sector_median_forward_pe") is None


def test_benchmark_compare_unavailable_learn() -> None:
    from card_copy import benchmark_compare_unavailable_learn

    card = _card(sector_peer_count=7)
    line = benchmark_compare_unavailable_learn(card)
    assert line is not None
    assert "Fewer than 8" in line
    assert benchmark_compare_unavailable_learn(_card(sector_peer_count=10)) is None
