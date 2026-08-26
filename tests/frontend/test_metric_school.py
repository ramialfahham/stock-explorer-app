"""Tests for metric playground seed values."""

from __future__ import annotations

import pathlib

from metric_school import (  # noqa: E402
    seed_ebit_margin_playground,
    seed_fcf_margin_playground,
    seed_net_debt_playground,
    seed_revenue_growth_playground,
)


def test_negative_net_debt_ratio_seeds_within_bounds() -> None:
    """Cash-rich companies can have negative net debt / EBITDA on the card."""
    debt, ebitda = seed_net_debt_playground({"net_debt_to_ebitda": -3.62})
    assert debt < 0
    assert debt >= -500.0
    assert ebitda >= 0.1


def test_extreme_negative_net_debt_ratio_clamps_to_min() -> None:
    debt, _ebitda = seed_net_debt_playground({"net_debt_to_ebitda": -100.0})
    assert debt == -500.0


def test_extreme_negative_ebit_margin_clamps_operating_profit() -> None:
    """Deep-loss companies can have margins below widget min (e.g. -601%)."""
    _revenue, operating = seed_ebit_margin_playground({"ebit_margin_pct": -601.5})
    assert operating == -500.0


def test_extreme_positive_ebit_margin_clamps_operating_profit() -> None:
    _revenue, operating = seed_ebit_margin_playground({"ebit_margin_pct": 800.0})
    assert operating == 500.0


def test_extreme_negative_fcf_margin_clamps_cash_flow() -> None:
    _revenue, fcf = seed_fcf_margin_playground({"fcf_margin_pct": -601.5})
    assert fcf == -500.0


def test_extreme_negative_revenue_growth_clamps_current_revenue() -> None:
    prior, current = seed_revenue_growth_playground({"revenue_growth_yoy_pct": -150.0})
    assert prior == 100.0
    assert current == 0.0


def test_every_hardcoded_metric_label_key_exists_in_the_catalogue() -> None:
    """Closes the bug class that shipped a live crash on 2026-08-26.

    `metric_school.py` renders playgrounds with hard-coded `METRIC_LABELS['<id>']`
    subscripts, and `METRIC_LABELS` is built from the generated `frontend/metrics.json`.
    Dropping `forward_pe` from the catalogue therefore turned tab 0 into a `KeyError` on
    every card that opened "Understand these numbers" -- and the suite stayed green,
    because these tests import only the `seed_*` helpers and never touch the render path.

    Reading the ids straight out of the source is deliberate: a test that repeated the list
    by hand would drift the same way the code did. This fails the moment a catalogued metric
    is removed while a playground still asks for its label.
    """
    import re

    from card_copy import METRIC_LABELS

    source = (pathlib.Path(__file__).resolve().parents[2] / "frontend" / "metric_school.py").read_text(
        encoding="utf-8"
    )
    keys = set(re.findall(r"METRIC_LABELS\[['\"]([a-z0-9_]+)['\"]\]", source))
    assert keys, "no METRIC_LABELS subscripts found -- has the render path been rewritten?"
    missing = sorted(k for k in keys if k not in METRIC_LABELS)
    assert not missing, (
        f"metric_school.py asks METRIC_LABELS for {missing}, which the catalogue no longer "
        f"defines. Rendering a playground for it raises KeyError on the live card. Remove "
        f"the playground alongside the metric, as the forward_pe one was."
    )
