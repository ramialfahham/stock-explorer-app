"""Tests for metric playground seed values."""

from __future__ import annotations

from streamlit.testing.v1 import AppTest

from card_copy import ALL_METRICS, metric_label
from metric_school import (  # noqa: E402
    _PLAYGROUNDS,
    _money,
    playgrounds_for_card,
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


def _card(company_type: str, **overrides) -> dict:
    card = {"ticker": "TST", "market_code": "us_sp500", "currency": "USD", "company_type": company_type}
    for metric in ALL_METRICS:
        card[metric] = 1.5
    card.update(overrides)
    return card


def test_every_playground_metric_is_in_the_catalogue() -> None:
    """Closes the bug class that shipped a live crash: a playground for a metric the
    catalogue no longer defines (forward_pe) raised KeyError on every opened card."""
    missing = sorted(m for m in _PLAYGROUNDS if m not in ALL_METRICS)
    assert not missing, f"playgrounds for {missing}, which the catalogue no longer defines"


def test_operating_card_gets_all_four_playgrounds_in_face_order() -> None:
    assert set(playgrounds_for_card(_card("operating"))) == set(_PLAYGROUNDS)
    assert playgrounds_for_card(_card("operating")) == tuple(
        m for m in ALL_METRICS if m in _PLAYGROUNDS
    )


def test_financial_card_gets_only_the_playgrounds_its_face_shows() -> None:
    assert playgrounds_for_card(_card("financial")) == ("revenue_growth_yoy_pct",)


def test_pre_revenue_card_gets_no_playground() -> None:
    assert playgrounds_for_card(_card("pre_revenue")) == ()


def test_a_metric_missing_on_the_face_loses_its_playground() -> None:
    assert "fcf_margin_pct" not in playgrounds_for_card(_card("operating", fcf_margin_pct=None))


def test_margin_playground_label_follows_the_face_basis() -> None:
    card = _card("operating", ebit_margin_basis="annual_latest")
    assert metric_label("ebit_margin_pct", card) == "Operating margin (annual)"
    assert metric_label("ebit_margin_pct", _card("operating")) == "Operating margin (TTM)"


def test_money_inputs_carry_the_card_currency() -> None:
    assert _money("Revenue", {"currency": "GBP"}) == "Revenue (£B)"
    assert _money("Revenue", {"currency": "CHF"}) == "Revenue (CHF B)"
    assert _money("Revenue", {}) == "Revenue (B)"


def _render(card: dict) -> AppTest:
    def script(card: dict) -> None:
        from metric_school import render_metric_playgrounds

        render_metric_playgrounds(card)

    at = AppTest.from_function(script, args=(card,), default_timeout=30)
    at.run()
    assert not at.exception, at.exception
    return at


def test_render_operating_card_shows_four_tabs_with_face_labels_and_currency() -> None:
    card = _card("operating", currency="GBP", ebit_margin_basis="annual_latest")
    at = _render(card)
    tabs = at.tabs
    metrics = playgrounds_for_card(card)
    assert [t.label for t in tabs] == [metric_label(m, card) for m in metrics]
    assert tabs[0].label == "Operating margin (annual)"
    assert not at.markdown, "the tab name carries the metric; no heading repeats it"
    assert [n.label for n in tabs[0].number_input] == ["Revenue (£B)", "Operating profit (£B)"]
    assert [n.label for n in tabs[2].number_input][0] == "Hypothetical net debt (£B)"
    labels = [n.label for n in at.number_input]
    assert len(labels) == 8
    assert all(label.endswith("(£B)") for label in labels), labels


def test_render_financial_card_shows_only_growth_and_pre_revenue_nothing() -> None:
    at = _render(_card("financial"))
    assert [t.label for t in at.tabs] == ["Rev growth YoY (quarter)"]
    assert [n.label for n in at.tabs[0].number_input] == ["Revenue one year ago ($B)", "Revenue today ($B)"]
    at = _render(_card("pre_revenue"))
    assert len(at.tabs) == 0 and len(at.number_input) == 0
