"""Unit tests for the deterministic health-verdict rules + regeneration hash (Slice 5a).

The verdict is health-only and must be total (always green|yellow|red), null-tolerant, and
reproducible; the input hash must be stable under float noise but sensitive to real changes.
A catalogue-mirror guard keeps INPUT_FIELDS_BY_TYPE / DIRECTION_BY_METRIC in sync with the seed.
"""

from __future__ import annotations

import csv
import math
from itertools import product
from pathlib import Path

import assessment_rules as rules

REPO = Path(__file__).resolve().parents[2]
CATALOGUE = REPO / "dbt_analytics" / "seeds" / "metric_catalogue.csv"


# --- Verdict: representative rows per type -------------------------------------------------

def test_operating_verdicts() -> None:
    green = {
        "company_type": "operating", "net_debt_to_ebitda": 1.1, "ebit_margin_pct": 24.0,
        "fcf_margin_pct": 16.0, "debt_to_equity": 0.7, "current_ratio_stmt": 1.8,
        "statement_roe_pct": 22.0,
    }
    red = {"company_type": "operating", "net_debt_to_ebitda": 4.5, "ebit_margin_pct": 6.0, "fcf_margin_pct": -2.0}
    yellow = {"company_type": "operating", "net_debt_to_ebitda": 2.0, "ebit_margin_pct": 12.0, "fcf_margin_pct": 8.0}
    assert rules.compute_verdict(green) == rules.VERDICT_GREEN
    assert rules.compute_verdict(red) == rules.VERDICT_RED
    assert rules.compute_verdict(yellow) == rules.VERDICT_YELLOW


def test_operating_supporting_weakness_blocks_green() -> None:
    # Core all good but a supporting metric is weak -> not green (yellow).
    row = {
        "company_type": "operating", "net_debt_to_ebitda": 1.0, "ebit_margin_pct": 20.0,
        "fcf_margin_pct": 12.0, "current_ratio_stmt": 0.8,  # weak liquidity
    }
    assert rules.compute_verdict(row) == rules.VERDICT_YELLOW


def test_financial_verdicts() -> None:
    green = {"company_type": "financial", "statement_roe_pct": 13.0, "net_margin_pct": 30.0, "roa_pct": 1.2}
    red = {"company_type": "financial", "statement_roe_pct": -5.0, "net_margin_pct": 10.0}
    yellow = {"company_type": "financial", "statement_roe_pct": 6.0, "net_margin_pct": 20.0, "roa_pct": 0.5}
    assert rules.compute_verdict(green) == rules.VERDICT_GREEN
    assert rules.compute_verdict(red) == rules.VERDICT_RED
    assert rules.compute_verdict(yellow) == rules.VERDICT_YELLOW


def test_financial_green_when_roa_absent() -> None:
    # roa may be null; green still reachable on ROE + margin.
    row = {"company_type": "financial", "statement_roe_pct": 12.0, "net_margin_pct": 22.0, "roa_pct": None}
    assert rules.compute_verdict(row) == rules.VERDICT_GREEN


def test_pre_revenue_verdicts() -> None:
    green = {"company_type": "pre_revenue", "cash_runway_months": 36.0, "net_cash_to_market_cap": 0.4, "working_capital": 2.1e9}
    red = {"company_type": "pre_revenue", "cash_runway_months": 8.0, "net_cash_to_market_cap": 0.1, "working_capital": -5.0e7}
    yellow = {"company_type": "pre_revenue", "cash_runway_months": 18.0, "net_cash_to_market_cap": 0.3, "working_capital": 1.0e6}
    assert rules.compute_verdict(green) == rules.VERDICT_GREEN
    assert rules.compute_verdict(red) == rules.VERDICT_RED
    assert rules.compute_verdict(yellow) == rules.VERDICT_YELLOW


def test_pre_revenue_null_runway_is_not_burning() -> None:
    # Null runway = not burning cash (positive); green still reachable via net-cash + WC.
    row = {"company_type": "pre_revenue", "cash_runway_months": None, "net_cash_to_market_cap": 0.5, "working_capital": 1.0e8}
    assert rules.compute_verdict(row) == rules.VERDICT_GREEN
    # ...but a net-debt position still caps it red regardless of runway.
    row_red = {"company_type": "pre_revenue", "cash_runway_months": None, "net_cash_to_market_cap": -0.1, "working_capital": 1.0e8}
    assert rules.compute_verdict(row_red) == rules.VERDICT_RED


# --- Boundaries (lock inclusivity) --------------------------------------------------------

def test_boundaries() -> None:
    op = lambda **k: {"company_type": "operating", "net_debt_to_ebitda": 1.0, "ebit_margin_pct": 20.0, "fcf_margin_pct": 12.0, **k}
    # ebit exactly 10 = good; exactly 0 = ok (not weak); just below 0 = weak.
    assert rules.compute_verdict(op(ebit_margin_pct=10.0)) == rules.VERDICT_GREEN
    assert rules.compute_verdict(op(ebit_margin_pct=0.0)) == rules.VERDICT_YELLOW
    assert rules.compute_verdict(op(ebit_margin_pct=-0.01)) == rules.VERDICT_RED
    # net_debt/ebitda exactly 1.5 = good; exactly 3 = ok; just above 3 = weak.
    assert rules.compute_verdict(op(net_debt_to_ebitda=1.5)) == rules.VERDICT_GREEN
    assert rules.compute_verdict(op(net_debt_to_ebitda=3.0)) == rules.VERDICT_YELLOW
    assert rules.compute_verdict(op(net_debt_to_ebitda=3.01)) == rules.VERDICT_RED
    # pre_revenue runway exactly 24 good, exactly 12 ok, below 12 weak.
    pr = lambda r: {"company_type": "pre_revenue", "cash_runway_months": r, "net_cash_to_market_cap": 0.5, "working_capital": 1.0}
    assert rules.compute_verdict(pr(24.0)) == rules.VERDICT_GREEN
    assert rules.compute_verdict(pr(12.0)) == rules.VERDICT_YELLOW
    assert rules.compute_verdict(pr(11.9)) == rules.VERDICT_RED


# --- Null tolerance + totality ------------------------------------------------------------

def test_operating_optional_metrics_null_still_resolves() -> None:
    row = {
        "company_type": "operating", "net_debt_to_ebitda": 1.0, "ebit_margin_pct": 20.0,
        "fcf_margin_pct": 12.0, "debt_to_equity": None, "current_ratio_stmt": None,
        "statement_roe_pct": None,
    }
    assert rules.compute_verdict(row) == rules.VERDICT_GREEN  # unknown supporting != weak


def test_all_unknown_falls_back_to_yellow() -> None:
    for ctype in rules.COMPANY_TYPES:
        assert rules.compute_verdict({"company_type": ctype}) == rules.VERDICT_YELLOW


def test_verdict_is_total_over_a_grid() -> None:
    vals = [None, float("nan"), -1.0, 0.0, 0.5, 10.0, 1000.0]
    fields = ["net_debt_to_ebitda", "ebit_margin_pct", "fcf_margin_pct", "cash_runway_months",
              "net_cash_to_market_cap", "working_capital", "statement_roe_pct", "net_margin_pct", "roa_pct"]
    for ctype in ("operating", "financial", "pre_revenue", "mystery", None):
        for combo in product(vals, repeat=3):
            row = {"company_type": ctype}
            for f, v in zip(fields, combo * 3):
                row[f] = v
            assert rules.compute_verdict(row) in rules.VERDICTS


def test_unknown_company_type_uses_operating() -> None:
    assert rules.normalize_company_type("mystery") == "operating"
    assert rules.normalize_company_type(None) == "operating"
    row = {"net_debt_to_ebitda": 1.0, "ebit_margin_pct": 20.0, "fcf_margin_pct": 12.0}  # no company_type
    assert rules.compute_verdict(row) == rules.VERDICT_GREEN


# --- Input hash ---------------------------------------------------------------------------

def _op_row() -> dict:
    return {"company_type": "operating", "forward_pe": 18.0, "ebit_margin_pct": 20.0,
            "revenue_growth_yoy_pct": 8.0, "net_debt_to_ebitda": 1.0, "fcf_margin_pct": 12.0,
            "debt_to_equity": 0.6, "current_ratio_stmt": 1.9, "statement_roe_pct": 15.0}


def test_hash_is_deterministic_and_64_hex() -> None:
    row = _op_row()
    v = rules.compute_verdict(row)
    h = rules.compute_input_hash(row, v)
    assert h == rules.compute_input_hash(row, v)
    assert len(h) == 64 and all(c in "0123456789abcdef" for c in h)


def test_hash_ignores_key_order() -> None:
    row = _op_row()
    reordered = dict(reversed(list(row.items())))
    v = rules.compute_verdict(row)
    assert rules.compute_input_hash(row, v) == rules.compute_input_hash(reordered, v)


def test_hash_stable_under_float_noise_but_sensitive_to_real_change() -> None:
    row = _op_row()
    v = rules.compute_verdict(row)
    base = rules.compute_input_hash(row, v)
    noisy = {**row, "ebit_margin_pct": 20.0000001}  # < 5e-7 -> rounds to 20.0
    assert rules.compute_input_hash(noisy, v) == base
    real = {**row, "ebit_margin_pct": 21.0}
    assert rules.compute_input_hash(real, v) != base


def test_hash_sensitive_to_version_and_verdict() -> None:
    row = _op_row()
    v = rules.compute_verdict(row)
    base = rules.compute_input_hash(row, v)
    assert rules.compute_input_hash(row, v, version="different") != base
    assert rules.compute_input_hash(row, rules.VERDICT_RED) != base


def test_hash_only_covers_the_per_type_input_set() -> None:
    # Changing a metric NOT in the operating input set (a pre_revenue-only field) is inert.
    row = _op_row()
    v = rules.compute_verdict(row)
    base = rules.compute_input_hash(row, v)
    assert rules.compute_input_hash({**row, "cash_runway_months": 5.0}, v) == base


def test_hash_handles_nan_like_none() -> None:
    row = _op_row()
    v = rules.compute_verdict(row)
    with_none = {**row, "forward_pe": None}
    with_nan = {**row, "forward_pe": float("nan")}
    assert rules.compute_input_hash(with_none, v) == rules.compute_input_hash(with_nan, v)


# --- Catalogue mirror (the schema-drift guard) --------------------------------------------

def _catalogue_rows() -> list[dict[str, str]]:
    with CATALOGUE.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def test_input_fields_mirror_catalogue_applies_to() -> None:
    expected: dict[str, set[str]] = {t: set() for t in rules.COMPANY_TYPES}
    for row in _catalogue_rows():
        mid = row["metric_id"].strip()
        for t in (row.get("applies_to") or "").split("|"):
            t = t.strip()
            if t in expected:
                expected[t].add(mid)
    for t in rules.COMPANY_TYPES:
        assert set(rules.INPUT_FIELDS_BY_TYPE[t]) == expected[t], f"{t}: INPUT_FIELDS drift vs catalogue"


def test_directions_mirror_catalogue() -> None:
    expected = {row["metric_id"].strip(): row["direction"].strip() for row in _catalogue_rows()}
    assert rules.DIRECTION_BY_METRIC == expected


# --- Slice 5b: the prose "read" prompt (build_read_messages) -------------------------------

def test_read_brief_covers_every_input_field() -> None:
    # Every metric any card can display must have a beginner brief, or the facts block
    # raises KeyError. Guards against INPUT_FIELDS_BY_TYPE drifting ahead of the brief.
    union = {m for fields in rules.INPUT_FIELDS_BY_TYPE.values() for m in fields}
    assert union <= set(rules.READ_METRIC_BRIEF)
    for brief in rules.READ_METRIC_BRIEF.values():
        assert {"label", "gloss", "fmt"} <= set(brief)
        assert brief["fmt"] in {"pct", "ratio", "months", "currency"}


def test_build_read_messages_operating_has_system_verdict_and_facts() -> None:
    row = {
        "company_type": "operating",
        "forward_pe": 18.5,
        "ebit_margin_pct": 24.0,
        "revenue_growth_yoy_pct": 9.0,
        "net_debt_to_ebitda": 1.1,
        "fcf_margin_pct": 16.0,
        "debt_to_equity": 0.6,
        "current_ratio_stmt": 1.8,
        "statement_roe_pct": 19.0,
    }
    system, user = rules.build_read_messages(row, rules.VERDICT_GREEN)
    assert system == rules.READ_SYSTEM_PROMPT
    assert "never give investment advice" in system.lower()
    # verdict + its plain meaning are stated for the model to land on
    assert "green" in user
    assert rules.VERDICT_MEANING[rules.VERDICT_GREEN] in user
    # every present operating metric appears with its label
    for field in rules.INPUT_FIELDS_BY_TYPE["operating"]:
        assert rules.READ_METRIC_BRIEF[field]["label"] in user
    assert "24.0%" in user  # percent formatting
    # valuation + growth are both flagged context-only, never a health signal
    assert user.lower().count("context only") >= 2


def test_build_read_messages_omits_missing_metrics() -> None:
    row = {
        "company_type": "operating",
        "net_debt_to_ebitda": 1.1,
        "ebit_margin_pct": 24.0,
        "fcf_margin_pct": 16.0,
        # supporting metrics + valuation/growth all absent
    }
    _system, user = rules.build_read_messages(row, rules.VERDICT_GREEN)
    assert rules.READ_METRIC_BRIEF["debt_to_equity"]["label"] not in user
    assert rules.READ_METRIC_BRIEF["forward_pe"]["label"] not in user
    assert rules.READ_METRIC_BRIEF["net_debt_to_ebitda"]["label"] in user
    assert "None" not in user  # missing values never render as a number


def test_build_read_messages_financial_states_profitability_only_limit() -> None:
    row = {
        "company_type": "financial",
        "statement_roe_pct": 13.0,
        "net_margin_pct": 30.0,
        "roa_pct": 1.2,
    }
    system, user = rules.build_read_messages(row, rules.VERDICT_GREEN)
    assert "profitability only" in system.lower()  # the financial-sector honesty limit
    assert rules.READ_METRIC_BRIEF["roa_pct"]["label"] in user


def test_build_read_messages_pre_revenue_uses_survival_metrics() -> None:
    row = {
        "company_type": "pre_revenue",
        "currency": "GBP",
        "net_cash_to_market_cap": 0.4,
        "working_capital": 2.1e9,
        "cash_runway_months": 36.0,
        "burn_rate_monthly": 5.0e6,
    }
    _system, user = rules.build_read_messages(row, rules.VERDICT_GREEN)
    assert rules.READ_METRIC_BRIEF["cash_runway_months"]["label"] in user
    assert "36 months" in user  # months formatting
    assert "£2.1B" in user      # money amounts carry the card's own currency
    assert "£5.0M" in user
    assert "$" not in user      # never an assumed USD symbol


def test_build_read_messages_money_amount_names_the_currency() -> None:
    # known code -> the right symbol
    _s, jpy = rules.build_read_messages(
        {"company_type": "pre_revenue", "currency": "JPY", "working_capital": 2.1e9},
        rules.VERDICT_YELLOW,
    )
    assert "¥2.1B" in jpy  # ¥2.1B
    # unknown code -> the code itself, never a fabricated symbol
    _s2, chf = rules.build_read_messages(
        {"company_type": "pre_revenue", "currency": "CHF", "working_capital": 2.1e9},
        rules.VERDICT_YELLOW,
    )
    assert "CHF 2.1B" in chf
    assert "$" not in chf and "£" not in chf


def test_build_read_messages_unknown_type_falls_back_to_operating() -> None:
    _system, user = rules.build_read_messages(
        {"company_type": None, "ebit_margin_pct": 10.0}, rules.VERDICT_YELLOW
    )
    assert "Company type: operating" in user
