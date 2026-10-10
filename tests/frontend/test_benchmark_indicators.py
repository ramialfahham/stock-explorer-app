"""Benchmark indicator helpers (Task 2 scanability)."""

from __future__ import annotations

import re
from pathlib import Path

from card_copy import (  # noqa: E402
    PEER_THRESHOLD,
    benchmark_indicator_label,
    benchmark_position,
)

_SECTOR_BENCHMARKS_SQL = (
    Path(__file__).resolve().parents[2]
    / "dbt_analytics"
    / "models"
    / "4_intermediate"
    / "int_stock__sector_benchmarks.sql"
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


def test_benchmark_indicator_label_above_median() -> None:
    card = _card(forward_pe=20.0, sector_median_forward_pe=18.0)
    assert benchmark_indicator_label(card, "forward_pe", "sector_median_forward_pe") == (
        "Higher than sector median"
    )


def test_benchmark_indicator_label_hidden_when_peer_threshold_not_met() -> None:
    card = _card(sector_peer_count=7)
    assert benchmark_indicator_label(card, "forward_pe", "sector_median_forward_pe") is None


def test_benchmark_compare_unavailable_learn() -> None:
    from card_copy import benchmark_compare_unavailable_learn

    card = _card(sector_peer_count=7)
    line = benchmark_compare_unavailable_learn(card)
    assert line is not None
    assert f"Fewer than {PEER_THRESHOLD}" in line
    assert benchmark_compare_unavailable_learn(_card(sector_peer_count=10)) is None


def test_peer_threshold_matches_the_dbt_benchmark_gate() -> None:
    """The mart nulls each metric's median/min/max below its own `peer_threshold`;
    `card_copy._benchmark_eligible` gates both the learn panel's compare section and the
    card-face range marks on `sector_peer_count`. Two copies of one number, so they must not
    drift apart."""
    sql = _SECTOR_BENCHMARKS_SQL.read_text(encoding="utf-8")
    match = re.search(r"\{%\s*set\s+peer_threshold\s*=\s*(\d+)\s*%\}", sql)
    assert match is not None, "int_stock__sector_benchmarks.sql no longer sets peer_threshold"
    assert PEER_THRESHOLD == int(match.group(1))
