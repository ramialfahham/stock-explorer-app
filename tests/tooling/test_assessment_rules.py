"""Unit tests for the deterministic health-verdict rules + regeneration hash (Slice 5a).

The verdict is health-only and must be total (always green|yellow|red), null-tolerant, and
reproducible; the input hash must be stable under float noise but sensitive to real changes.
A catalogue-mirror guard keeps INPUT_FIELDS_BY_TYPE / DIRECTION_BY_METRIC in sync with the seed.
"""

from __future__ import annotations

import csv
import math
import re
from itertools import product
from pathlib import Path

import pytest

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
    # Core all good but a supporting metric is weak -> not green (yellow). Uses statement_roe_pct
    # here, not current_ratio_stmt: current_ratio_stmt now has one explicit exception (see the
    # joint-liquidity-evaluation tests below), so a fixture pairing weak current_ratio_stmt with
    # a strong fcf_margin_pct (as this test used to) would exercise that relief instead of the
    # general principle this test is about. The general principle still holds for every other
    # supporting axis.
    row = {
        "company_type": "operating", "net_debt_to_ebitda": 1.0, "ebit_margin_pct": 20.0,
        "fcf_margin_pct": 12.0, "statement_roe_pct": -5.0,  # weak returns
    }
    assert rules.compute_verdict(row) == rules.VERDICT_YELLOW


def test_growth_is_one_sided_shrinking_blocks_green() -> None:
    """A shrinking top line stops a card being called Healthy, on both card types that show
    growth. This is the whole point of step 2: growth was on the card and unread."""
    op = {
        "company_type": "operating", "net_debt_to_ebitda": 1.0, "ebit_margin_pct": 20.0,
        "fcf_margin_pct": 12.0, "revenue_growth_yoy_pct": -0.4,
    }
    assert rules.compute_verdict(op) == rules.VERDICT_YELLOW
    fin = {
        "company_type": "financial", "statement_roe_pct": 13.0, "net_margin_pct": 30.0,
        "roa_pct": 1.2, "revenue_growth_yoy_pct": -0.4,
    }
    assert rules.compute_verdict(fin) == rules.VERDICT_YELLOW


def test_growth_is_one_sided_shrinking_never_causes_red() -> None:
    """The asymmetry, half one. A solvent, profitable, cash-generating company having a bad
    year is not in distress -- growth may block green, never trigger red. Without this, one
    weak quarter would put a sturdy balance sheet in the same bucket as a company burning
    cash with negative margins."""
    row = {
        "company_type": "operating", "net_debt_to_ebitda": 0.5, "ebit_margin_pct": 25.0,
        "fcf_margin_pct": 18.0, "revenue_growth_yoy_pct": -40.0,
    }
    assert rules.compute_verdict(row) == rules.VERDICT_YELLOW


def test_growth_is_one_sided_growth_never_earns_green() -> None:
    """The asymmetry, half two, and the reason growth was excluded from the verdict for so
    long: a company can grow into losses. Spectacular growth must not rescue weak
    fundamentals -- this card is red on its core axes and stays red."""
    row = {
        "company_type": "operating", "net_debt_to_ebitda": 6.0, "ebit_margin_pct": -5.0,
        "fcf_margin_pct": -8.0, "revenue_growth_yoy_pct": 300.0,
    }
    assert rules.compute_verdict(row) == rules.VERDICT_RED
    # and it cannot lift a merely-yellow card either
    mid = {
        "company_type": "operating", "net_debt_to_ebitda": 2.0, "ebit_margin_pct": 5.0,
        "fcf_margin_pct": 2.0, "revenue_growth_yoy_pct": 300.0,
    }
    assert rules.compute_verdict(mid) == rules.VERDICT_YELLOW


def test_absent_growth_does_not_block_green() -> None:
    """Missing data is not a decline. Every other axis treats null as unknown rather than
    bad, and growth must not be the exception -- a company Yahoo has no growth figure for
    would otherwise be capped at yellow forever."""
    for value in (None, float("nan")):
        row = {
            "company_type": "operating", "net_debt_to_ebitda": 1.0, "ebit_margin_pct": 20.0,
            "fcf_margin_pct": 12.0, "revenue_growth_yoy_pct": value,
        }
        assert rules.compute_verdict(row) == rules.VERDICT_GREEN
    del row["revenue_growth_yoy_pct"]
    assert rules.compute_verdict(row) == rules.VERDICT_GREEN


def test_growth_threshold_is_zero_with_no_tolerance_band() -> None:
    """Owner-decided: any year-over-year decline blocks green. An earlier draft proposed a
    -5% tolerance on the argument that a single quarter is noisy; that was rejected. YoY
    compares the same quarter a year earlier, so the figure is not seasonal noise, though it
    is still one quarter and cannot separate a real decline from a divestment or FX move.
    That is what the one-sidedness is for. Pinned so the band cannot creep back."""
    assert rules.GROWTH_DECLINE_THRESHOLD_PCT == 0.0
    base = {
        "company_type": "operating", "net_debt_to_ebitda": 1.0, "ebit_margin_pct": 20.0,
        "fcf_margin_pct": 12.0,
    }
    assert rules.compute_verdict({**base, "revenue_growth_yoy_pct": 0.0}) == rules.VERDICT_GREEN
    assert rules.compute_verdict({**base, "revenue_growth_yoy_pct": -0.1}) == rules.VERDICT_YELLOW


def test_pre_revenue_verdict_still_ignores_burn_rate() -> None:
    """burn_rate_monthly is shown on the pre-revenue card and deliberately NOT read by the
    verdict -- an owner-decided exception to "everything shown feeds the verdict". Reading it
    as its own axis would double-count, because cash runway already IS cash divided by burn.
    It stays on the card because runway is a ratio and a ratio destroys magnitude: 18 months
    at $2M a month and 18 months at $50M a month are very different companies."""
    base = {
        "company_type": "pre_revenue", "cash_runway_months": 36.0, "net_cash": 4.0e8,
        "working_capital": 2.1e9,
    }
    assert rules.compute_verdict(base) == rules.VERDICT_GREEN
    assert rules.compute_verdict({**base, "burn_rate_monthly": 5.0e8}) == rules.VERDICT_GREEN
    assert "burn_rate_monthly" in rules.INPUT_FIELDS_BY_TYPE["pre_revenue"]  # still hashed + in the prose read


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
    green = {"company_type": "pre_revenue", "cash_runway_months": 36.0, "net_cash": 4.0e8, "working_capital": 2.1e9}
    red = {"company_type": "pre_revenue", "cash_runway_months": 8.0, "net_cash": 1.0e8, "working_capital": -5.0e7}
    yellow = {"company_type": "pre_revenue", "cash_runway_months": 18.0, "net_cash": 3.0e8, "working_capital": 1.0e6}
    assert rules.compute_verdict(green) == rules.VERDICT_GREEN
    assert rules.compute_verdict(red) == rules.VERDICT_RED
    assert rules.compute_verdict(yellow) == rules.VERDICT_YELLOW


def test_pre_revenue_null_runway_is_not_burning() -> None:
    # Null runway = not burning cash (positive); green still reachable via net-cash + WC.
    row = {"company_type": "pre_revenue", "cash_runway_months": None, "net_cash": 5.0e8, "working_capital": 1.0e8}
    assert rules.compute_verdict(row) == rules.VERDICT_GREEN
    # ...but a net-debt position still caps it red regardless of runway.
    row_red = {"company_type": "pre_revenue", "cash_runway_months": None, "net_cash": -1.0e8, "working_capital": 1.0e8}
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
    pr = lambda r: {"company_type": "pre_revenue", "cash_runway_months": r, "net_cash": 5.0e8, "working_capital": 1.0}
    assert rules.compute_verdict(pr(24.0)) == rules.VERDICT_GREEN
    assert rules.compute_verdict(pr(12.0)) == rules.VERDICT_YELLOW
    assert rules.compute_verdict(pr(11.9)) == rules.VERDICT_RED


# --- Ratio sign-inversion guards ----------------------------------------------------------
# Gemini feedback point 1 (docs/backlog/gemini_verdict_feedback.md): net_debt_to_ebitda and
# debt_to_equity can flip sign when a denominator goes negative, and banding the flipped value
# by raw magnitude used to read a distressed company as good on that axis.

def test_net_debt_to_ebitda_guard_moves_a_green_card_to_yellow() -> None:
    """Core axis: net debt looks tiny relative to a *negative* EBITDA (info_ebitda <= 0), which
    the old magnitude-only banding read as excellent leverage. The guard needs info_ebitda's own
    sign to catch this -- the ratio's sign alone can't, since a negative numerator would look
    identical."""
    row = {
        "company_type": "operating", "net_debt_to_ebitda": 0.2, "ebit_margin_pct": 20.0,
        "fcf_margin_pct": 12.0, "info_ebitda": -5.0,
    }
    assert rules.compute_verdict(row) == rules.VERDICT_YELLOW
    # Same numbers, profitable EBITDA instead: nothing wrong here, still green.
    healthy = {**row, "info_ebitda": 5.0}
    assert rules.compute_verdict(healthy) == rules.VERDICT_GREEN


def test_net_debt_to_ebitda_guard_ignores_a_missing_info_ebitda() -> None:
    """A MISSING info_ebitda must not trigger the guard -- only a denominator we can actually
    see is bad, the same "missing means unknown, never assumed" treatment every other axis
    gets. Without this, every card computed before info_ebitda existed would silently degrade."""
    row = {
        "company_type": "operating", "net_debt_to_ebitda": 0.2, "ebit_margin_pct": 20.0,
        "fcf_margin_pct": 12.0,
    }
    assert rules.compute_verdict(row) == rules.VERDICT_GREEN
    assert rules.compute_verdict({**row, "info_ebitda": None}) == rules.VERDICT_GREEN
    assert rules.compute_verdict({**row, "info_ebitda": float("nan")}) == rules.VERDICT_GREEN


def test_net_debt_to_ebitda_guard_does_not_touch_genuine_net_cash() -> None:
    """A real net-cash position (negative net_debt_to_ebitda, positive info_ebitda) is the
    case the guard must leave alone -- it is genuinely the best leverage reading, not a sign
    flip to catch."""
    row = {
        "company_type": "operating", "net_debt_to_ebitda": -0.5, "ebit_margin_pct": 20.0,
        "fcf_margin_pct": 12.0, "info_ebitda": 8.0,
    }
    assert rules.compute_verdict(row) == rules.VERDICT_GREEN


def test_debt_to_equity_guard_caps_a_negative_equity_card_at_yellow() -> None:
    """Supporting axis: total debt is never negative in this data, so a negative ratio always
    means negative shareholders' equity. The old magnitude-only banding treated any negative
    value as "good" (lower-is-better, and negative is always below the good threshold), so this
    used to help a distressed company toward green. "weak" gives it the same ceiling every
    other weak supporting axis already has: it caps the card at yellow, it does not force red."""
    row = {
        "company_type": "operating", "net_debt_to_ebitda": 1.0, "ebit_margin_pct": 20.0,
        "fcf_margin_pct": 12.0, "debt_to_equity": -3.0, "stmt_stockholders_equity": -500.0,
        "current_ratio_stmt": 1.8, "statement_roe_pct": 22.0,
    }
    assert rules.compute_verdict(row) == rules.VERDICT_YELLOW
    # A red core axis still wins outright; the guard must not soften that.
    weak_core = {**row, "ebit_margin_pct": -5.0}
    assert rules.compute_verdict(weak_core) == rules.VERDICT_RED


def test_debt_to_equity_guard_checks_equity_directly_not_the_ratios_sign() -> None:
    """The ratio's own sign is not a reliable tell: total debt is never negative in this data,
    but it CAN be exactly zero, and zero divided by negative equity is zero, not negative. A
    debt-free company with negative equity (debt_to_equity == 0.0) would silently evade a check
    on the ratio's own sign and still band "good". Checking stmt_stockholders_equity's own sign
    directly catches this case too."""
    row = {
        "company_type": "operating", "net_debt_to_ebitda": 1.0, "ebit_margin_pct": 20.0,
        "fcf_margin_pct": 12.0, "debt_to_equity": 0.0, "stmt_stockholders_equity": -500.0,
        "current_ratio_stmt": 1.8, "statement_roe_pct": 22.0,
    }
    assert rules.compute_verdict(row) == rules.VERDICT_YELLOW


def test_debt_to_equity_guard_does_not_touch_genuinely_low_leverage() -> None:
    """A real low-leverage company (positive debt_to_equity, positive equity) is unaffected --
    the guard only fires when it can see equity itself is non-positive."""
    row = {
        "company_type": "operating", "net_debt_to_ebitda": 1.0, "ebit_margin_pct": 20.0,
        "fcf_margin_pct": 12.0, "debt_to_equity": 0.6, "stmt_stockholders_equity": 800.0,
        "current_ratio_stmt": 1.8, "statement_roe_pct": 22.0,
    }
    assert rules.compute_verdict(row) == rules.VERDICT_GREEN


def test_debt_to_equity_guard_ignores_a_missing_equity_value() -> None:
    # A MISSING stmt_stockholders_equity does not trigger the guard -- only equity we can
    # actually see is bad, matching every other axis's missing-means-unknown treatment. The
    # ratio itself may still be present (e.g. from a period the pipeline didn't carry equity for).
    row = {
        "company_type": "operating", "net_debt_to_ebitda": 1.0, "ebit_margin_pct": 20.0,
        "fcf_margin_pct": 12.0, "debt_to_equity": 0.6, "current_ratio_stmt": 1.8,
        "statement_roe_pct": 22.0,
    }
    assert rules.compute_verdict(row) == rules.VERDICT_GREEN
    assert rules.compute_verdict({**row, "stmt_stockholders_equity": None}) == rules.VERDICT_GREEN


# --- statement_roe_pct sign-inversion guard (both verdict functions) ----------------------
# Same bug class as debt_to_equity: statement_roe_pct = stmt_net_income_common /
# stmt_stockholders_equity, so a loss over negative equity divides out to a spuriously POSITIVE
# percentage. Operating treats it as a supporting axis (weak caps at yellow, same as
# debt_to_equity). Financial treats it as core-like, but bands "unknown", not "weak" -- it
# blocks green (roe must band "good" to reach green) without forcing red, because
# company_type == 'financial' spans a heterogeneous, multi-jurisdiction population (insurers,
# asset managers, payment networks, exchanges, not only depository banks, across markets with
# very different bank regulators) the data cannot distinguish "genuine distress" from "a payment
# network mid-buyback" within -- see the comment above _verdict_financial for the full account,
# including why an earlier version of this guard forcing red was corrected in review.

def test_statement_roe_guard_function_is_isolated_from_debt_to_equitys_shared_denominator() -> None:
    """Direct test of the guard mechanism itself, calling _axis_unless_denominator_nonpositive
    with each verdict function's actual parameters. debt_to_equity's own guard (a prior, merged
    fix) keys off the SAME stmt_stockholders_equity field unconditionally, so a
    compute_verdict-level row with negative equity trips BOTH guards at once -- a
    compute_verdict-level test alone cannot prove this guard's own effect, confirmed by mutation
    testing in review (reverting only this guard left the operating verdict-level test below
    passing identically, since debt_to_equity's guard alone already explains its outcome)."""
    negative_equity = {"statement_roe_pct": 20.0, "stmt_stockholders_equity": -1000.0}
    healthy_equity = {"statement_roe_pct": 20.0, "stmt_stockholders_equity": 1000.0}
    missing_equity = {"statement_roe_pct": 20.0}
    # Operating's parameters: bad_band "weak".
    assert rules._axis_unless_denominator_nonpositive(
        negative_equity, "statement_roe_pct", "stmt_stockholders_equity", "weak",
        weak_th=0.0, good_th=10.0,
    ) == "weak"
    assert rules._axis_unless_denominator_nonpositive(
        healthy_equity, "statement_roe_pct", "stmt_stockholders_equity", "weak",
        weak_th=0.0, good_th=10.0,
    ) == "good"
    assert rules._axis_unless_denominator_nonpositive(
        missing_equity, "statement_roe_pct", "stmt_stockholders_equity", "weak",
        weak_th=0.0, good_th=10.0,
    ) == "good"
    # Financial's parameters: bad_band "unknown".
    assert rules._axis_unless_denominator_nonpositive(
        negative_equity, "statement_roe_pct", "stmt_stockholders_equity", "unknown",
        weak_th=0.0, good_th=8.0,
    ) == "unknown"
    assert rules._axis_unless_denominator_nonpositive(
        healthy_equity, "statement_roe_pct", "stmt_stockholders_equity", "unknown",
        weak_th=0.0, good_th=8.0,
    ) == "good"


def test_operating_statement_roe_guard_caps_a_negative_equity_card_at_yellow() -> None:
    """Integration-level sanity check: the whole card computes sensibly with negative equity.
    Both debt_to_equity's and statement_roe_pct's guards trip on the same field here (realistic --
    a company's negative equity affects every ratio computed from it), so this does not in
    isolation prove statement_roe_pct's own call site is wired -- see
    test_operating_statement_roe_call_site_is_actually_wired below for that."""
    row = {
        "company_type": "operating", "net_debt_to_ebitda": 1.0, "ebit_margin_pct": 20.0,
        "fcf_margin_pct": 12.0, "debt_to_equity": 0.6, "current_ratio_stmt": 1.8,
        "statement_roe_pct": 20.0, "stmt_stockholders_equity": -1000.0,
    }
    assert rules.compute_verdict(row) == rules.VERDICT_YELLOW
    # A red core axis still wins outright; the guard must not soften that.
    weak_core = {**row, "ebit_margin_pct": -5.0}
    assert rules.compute_verdict(weak_core) == rules.VERDICT_RED


def test_operating_statement_roe_call_site_is_actually_wired(monkeypatch) -> None:
    """Proves _verdict_operating's statement_roe_pct call site is genuinely routed through the
    guard, not just that the shared guard function behaves correctly on its own (the gap the
    direct function test above does not close, and the verdict-level test above cannot close
    either, since debt_to_equity's own guard on the SAME stmt_stockholders_equity field fires
    unconditionally whenever that field is negative, regardless of debt_to_equity's own value or
    even its presence -- there is no row where the shared denominator is negative that trips only
    one of the two guards, confirmed by mutation testing in review).

    Neutralizes debt_to_equity's guard specifically (falls back to plain magnitude banding for
    that one call) while leaving statement_roe_pct's call to the real guard, then drives the row
    through compute_verdict -- if statement_roe_pct's call site were ever silently reverted to
    plain _axis(...), this row would read GREEN instead of YELLOW, since every other axis bands
    good/ok once debt_to_equity's guard is neutralized.
    """
    real_guard = rules._axis_unless_denominator_nonpositive

    def neutralize_debt_to_equity(row, metric, denominator_field, bad_band, weak_th, good_th):
        if metric == "debt_to_equity":
            return rules._axis(row, metric, weak_th, good_th)
        return real_guard(row, metric, denominator_field, bad_band, weak_th, good_th)

    monkeypatch.setattr(rules, "_axis_unless_denominator_nonpositive", neutralize_debt_to_equity)

    row = {
        "company_type": "operating", "net_debt_to_ebitda": 1.0, "ebit_margin_pct": 20.0,
        "fcf_margin_pct": 12.0, "debt_to_equity": 0.6, "current_ratio_stmt": 1.8,
        "statement_roe_pct": 20.0, "stmt_stockholders_equity": -1000.0,
    }
    assert rules.compute_verdict(row) == rules.VERDICT_YELLOW


def test_operating_statement_roe_guard_does_not_touch_genuinely_healthy_equity() -> None:
    row = {
        "company_type": "operating", "net_debt_to_ebitda": 1.0, "ebit_margin_pct": 20.0,
        "fcf_margin_pct": 12.0, "debt_to_equity": 0.6, "current_ratio_stmt": 1.8,
        "statement_roe_pct": 20.0, "stmt_stockholders_equity": 1000.0,
    }
    assert rules.compute_verdict(row) == rules.VERDICT_GREEN


def test_operating_statement_roe_guard_ignores_a_missing_equity_value() -> None:
    row = {
        "company_type": "operating", "net_debt_to_ebitda": 1.0, "ebit_margin_pct": 20.0,
        "fcf_margin_pct": 12.0, "debt_to_equity": 0.6, "current_ratio_stmt": 1.8,
        "statement_roe_pct": 20.0,
    }
    assert rules.compute_verdict(row) == rules.VERDICT_GREEN
    assert rules.compute_verdict({**row, "stmt_stockholders_equity": None}) == rules.VERDICT_GREEN


def test_financial_statement_roe_guard_blocks_green_but_does_not_force_red() -> None:
    """Unlike a genuinely weak margin (which forces red on its own), a negative-equity roe bands
    "unknown": it blocks green (roe must band "good" to reach green) but does not force red,
    since the data can't tell a bank in real distress apart from a payment network mid-buyback."""
    row = {
        "company_type": "financial", "statement_roe_pct": 13.0, "net_margin_pct": 30.0,
        "roa_pct": 1.2, "stmt_stockholders_equity": -500.0,
    }
    assert rules.compute_verdict(row) == rules.VERDICT_YELLOW
    # A genuinely weak margin still forces red on its own, unaffected by this guard.
    weak_margin = {**row, "net_margin_pct": -5.0}
    assert rules.compute_verdict(weak_margin) == rules.VERDICT_RED


def test_financial_statement_roe_guard_does_not_touch_genuinely_healthy_equity() -> None:
    row = {
        "company_type": "financial", "statement_roe_pct": 13.0, "net_margin_pct": 30.0,
        "roa_pct": 1.2, "stmt_stockholders_equity": 500.0,
    }
    assert rules.compute_verdict(row) == rules.VERDICT_GREEN


def test_financial_statement_roe_guard_ignores_a_missing_equity_value() -> None:
    row = {
        "company_type": "financial", "statement_roe_pct": 13.0, "net_margin_pct": 30.0,
        "roa_pct": 1.2,
    }
    assert rules.compute_verdict(row) == rules.VERDICT_GREEN
    assert rules.compute_verdict({**row, "stmt_stockholders_equity": None}) == rules.VERDICT_GREEN


# --- Joint liquidity evaluation (current_ratio_stmt relief from FCF covering the shortfall) ---
# Gemini feedback points 6/8: current_ratio_stmt and fcf_margin_pct used to be graded fully
# independently, so a company with excellent free cash flow but a merely-weak current ratio was
# capped at yellow regardless -- Apple's real card (current ratio 0.89, FCF margin 23.7%).
#
# A review round caught that gating relief on fcf_margin_pct (FCF / revenue) is a mismatched
# comparison: it doesn't track the SIZE of the liquidity gap, which isn't proportional to revenue
# (e.g. a near-term debt-maturity wall). Corrected to a direct dollar comparison: does free cash
# flow (stmt_free_cash_flow) actually cover the working-capital shortfall (-working_capital)?
# fcf_margin_pct remains a CORE axis in its own right (unrelated to this relief), so it still
# needs to band "good" for a row to reach green -- these tests set it accordingly and vary
# stmt_free_cash_flow/working_capital independently to isolate the relief mechanism itself.

def _liquidity_row(**overrides) -> dict:
    row = {
        "company_type": "operating", "net_debt_to_ebitda": 1.0, "ebit_margin_pct": 20.0,
        "fcf_margin_pct": 23.7, "statement_roe_pct": 22.0, "debt_to_equity": 0.6,
    }
    row.update(overrides)
    return row


def test_current_ratio_weak_gets_relief_when_fcf_covers_the_shortfall() -> None:
    """Apple's real figures: current ratio 0.89 (weak, below the 1.0 threshold), but free cash
    flow comfortably exceeds the working-capital shortfall. This used to cap the card at yellow
    purely on the ratio; it should now reach green."""
    row = _liquidity_row(
        current_ratio_stmt=0.89, working_capital=-100.0, stmt_free_cash_flow=200.0,
    )
    assert rules.compute_verdict(row) == rules.VERDICT_GREEN


def test_current_ratio_relief_denied_when_fcf_margin_good_but_shortfall_too_large() -> None:
    """The exact case the fcf_margin_pct-only version missed: a decent FCF margin (6%, bands
    "good") that is nowhere near large enough in dollar terms to cover a real shortfall, e.g.
    from a near-term debt-maturity wall sitting in current liabilities. Revenue-scaled margin
    alone would have wrongly granted relief here; the dollar comparison correctly withholds it."""
    row = _liquidity_row(
        fcf_margin_pct=6.0, current_ratio_stmt=0.525,
        working_capital=-950.0, stmt_free_cash_flow=60.0,
    )
    assert rules.compute_verdict(row) == rules.VERDICT_YELLOW


def test_current_ratio_relief_has_a_floor_regardless_of_fcf_coverage() -> None:
    """The relief is not unconditional. Below CURRENT_RATIO_LIQUIDITY_FLOOR, current liabilities
    are more than double current assets -- a real distress signal no amount of free cash flow
    should paper over, since the company is fully dependent on uninterrupted cash inflow with
    zero cushion. FCF here would clear the coverage check easily; the floor still blocks it."""
    row = _liquidity_row(
        current_ratio_stmt=0.4, working_capital=-50.0, stmt_free_cash_flow=500.0,
    )
    assert rules.compute_verdict(row) == rules.VERDICT_YELLOW


def test_current_ratio_relief_floor_boundary() -> None:
    row = lambda cr: _liquidity_row(
        current_ratio_stmt=cr, working_capital=-100.0, stmt_free_cash_flow=200.0,
    )
    assert rules.compute_verdict(row(0.5)) == rules.VERDICT_GREEN  # exactly at the floor: relief
    assert rules.compute_verdict(row(0.49)) == rules.VERDICT_YELLOW  # just below: no relief


def test_current_ratio_relief_coverage_boundary() -> None:
    # FCF exactly equal to the shortfall clears it (>=); a cent short does not.
    row = lambda fcf: _liquidity_row(
        current_ratio_stmt=0.89, working_capital=-100.0, stmt_free_cash_flow=fcf,
    )
    assert rules.compute_verdict(row(100.0)) == rules.VERDICT_GREEN
    assert rules.compute_verdict(row(99.99)) == rules.VERDICT_YELLOW


def test_current_ratio_relief_ignores_missing_fcf_or_working_capital() -> None:
    # Missing data earns no relief -- the same "only apply an exception when we have positive
    # evidence for it" stance as the sign-inversion guards, not the reverse.
    row = _liquidity_row(current_ratio_stmt=0.89, working_capital=-100.0)  # no stmt_free_cash_flow
    assert rules.compute_verdict(row) == rules.VERDICT_YELLOW
    row2 = _liquidity_row(current_ratio_stmt=0.89, stmt_free_cash_flow=200.0)  # no working_capital
    assert rules.compute_verdict(row2) == rules.VERDICT_YELLOW


def test_current_ratio_relief_ignores_a_non_negative_working_capital() -> None:
    # Defensive: current_ratio_stmt banding "weak" implies working_capital should be negative
    # (both derive from the same current assets/liabilities), but the relief function must not
    # misbehave on inconsistent input -- a working_capital that isn't actually negative is not
    # evidence of a shortfall to cover, so no relief.
    row = _liquidity_row(current_ratio_stmt=0.89, working_capital=0.0, stmt_free_cash_flow=200.0)
    assert rules.compute_verdict(row) == rules.VERDICT_YELLOW


def test_current_ratio_relief_does_not_rescue_other_weak_axes() -> None:
    """Relief is narrowly scoped to current_ratio_stmt -- it does not have a broader "everything
    is fine" side effect on the rest of the card."""
    row = _liquidity_row(
        current_ratio_stmt=0.89, working_capital=-100.0, stmt_free_cash_flow=200.0,
        statement_roe_pct=-5.0,  # weak
    )
    assert rules.compute_verdict(row) == rules.VERDICT_YELLOW


def test_current_ratio_relief_ignores_a_missing_current_ratio() -> None:
    # A MISSING current_ratio_stmt bands "unknown", not "weak" -- the relief function must not
    # touch it (and must not crash trying to read a value that isn't there).
    row = _liquidity_row(
        current_ratio_stmt=None, working_capital=-100.0, stmt_free_cash_flow=200.0,
    )
    assert rules.compute_verdict(row) == rules.VERDICT_GREEN


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
              "net_cash", "working_capital", "statement_roe_pct", "net_margin_pct", "roa_pct"]
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
    return {"company_type": "operating", "ebit_margin_pct": 20.0,
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
    # Must mutate a field that is actually IN the operating input set, or the hash never reads
    # it and this asserts h == h. forward_pe was used here before it was dropped, and removing it from
    # INPUT_FIELDS_BY_TYPE silently emptied this test, which is the only coverage
    # _canonical_number's NaN -> None guard has.
    assert "debt_to_equity" in rules.INPUT_FIELDS_BY_TYPE["operating"]
    with_none = {**row, "debt_to_equity": None}
    with_nan = {**row, "debt_to_equity": float("nan")}
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
    # The growth line must tell the model which way growth counts, since the verdict reads it
    # one-sidedly. Pinning the direction rather than a catchphrase: a falling top line counts
    # against the verdict, a rising one does not count for it.
    # Assert against the BUILT message, not the constant. Reading the constant would prove
    # only that it contains the words, so deleting the gloss from build_read_messages' f-string
    # would leave the whole suite green and the model would never be told which way growth
    # counts. Nothing else in this file covers gloss text reaching the prompt.
    assert "counts against the verdict" in user.lower()
    assert "does not count for it" in user.lower()
    assert "forward_pe" not in rules.INPUT_FIELDS_BY_TYPE["operating"]


def test_build_read_messages_omits_missing_metrics() -> None:
    row = {
        "company_type": "operating",
        "net_debt_to_ebitda": 1.1,
        "ebit_margin_pct": 24.0,
        "fcf_margin_pct": 16.0,
        # supporting metrics + growth all absent
    }
    _system, user = rules.build_read_messages(row, rules.VERDICT_GREEN)
    assert rules.READ_METRIC_BRIEF["debt_to_equity"]["label"] not in user
    assert rules.READ_METRIC_BRIEF["current_ratio_stmt"]["label"] not in user
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
        "net_cash": 4.0e8,
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


# --- Currency naming in the prose read -----------------------------------------------------
# The prompt names the card's currency so the read can explain a margin as an amount kept
# per unit of revenue without inventing one. Operating and financial cards carry no
# `currency`-fmt metric, so the dedicated prompt line is their only route to it.

# A deny-list, with the limits that implies. Currency is NOT declared per market anywhere:
# docs/market_registry.yml has no currency field, and the value comes from yfinance
# `info_currency` per ticker, so nothing in the repo can enumerate what may turn up. These
# eight cover the currencies the nine active markets return today: USD, GBp, JPY, EUR, AUD and
# CHF, the last arriving with Switzerland, which is what "franc" is here for. Six more markets
# are queued, three of which bring currencies this list does not hold: SEK, DKK and NOK.
# (CAD needs nothing: "dollar" already covers it, the same way "franc" covers CHF.)
# EXTEND IT when a market is added, when a dormant one is activated by flipping ingest_active,
# or when yfinance starts returning a currency these words miss. There is no mechanical trigger
# for any of those, which is the weakness of a deny-list and the reason to prefer catching this
# in review.
_CURRENCY_WORDS = (
    "dollar", "cent", "pound", "pence", "penny", "euro", "yen", "franc",
)

# Every catalogue column that `scripts/export_metric_definitions_json.py` copies into
# frontend/metrics.json. Four of them (gloss, analogy, learn, label) are bound to the card
# face by frontend/card_copy.py; the rest ship to the client unbound. Guarding all of them
# keeps a currency word out of anything a future binding could surface.
_VISIBLE_COPY_FIELDS = (
    "label", "gloss", "analogy", "learn", "interpretation", "applicability",
    "description", "calculation",
)


def _names_a_currency(text: str) -> bool:
    """Whole-word match plus symbols. Substring matching would fire on "percent" in a check
    whose whole subject is percentages."""
    lowered = text.lower()
    if any(re.search(rf"\b{word}s?\b", lowered) for word in _CURRENCY_WORDS):
        return True
    return any(symbol.strip() in text for symbol in rules._CURRENCY_SYMBOLS.values())


def test_names_a_currency_helper_is_not_fooled_by_percent() -> None:
    assert not _names_a_currency("share of sales kept as operating profit")
    assert not _names_a_currency("a percentage, not a percent of recent incentives")
    assert _names_a_currency("for every dollar of sales")
    assert _names_a_currency("keeps 24 cents per sale")
    assert _names_a_currency("every £ of sales")


def test_metric_glosses_name_no_currency() -> None:
    """A gloss naming a currency hands the model one for a number that has none, and it
    then applies it to companies reporting in five other currencies."""
    for metric, brief in rules.READ_METRIC_BRIEF.items():
        if brief["fmt"] == "currency":
            continue  # money amounts SHOULD carry their currency
        assert not _names_a_currency(brief["gloss"]), f"{metric} gloss names a currency"


@pytest.mark.parametrize(
    ("company_type", "row"),
    [
        ("operating", {"ebit_margin_pct": 24.0, "fcf_margin_pct": 16.0}),
        ("financial", {"statement_roe_pct": 12.0, "net_margin_pct": 20.0}),
        ("pre_revenue", {"net_cash": 5.0e8, "working_capital": 2.0e8}),
    ],
)
def test_build_read_messages_names_the_currency_for_every_card_type(company_type, row) -> None:
    _system, user = rules.build_read_messages(
        {"company_type": company_type, "currency": "AUD", **row}, rules.VERDICT_GREEN
    )
    assert "AUD" in user, f"{company_type} card never tells the model its currency"


def test_build_read_messages_normalises_gbp_pence_to_the_symbol_the_card_shows() -> None:
    """yfinance reports LSE tickers as `GBp`, i.e. pence. Every other consumer upper-cases
    before formatting, so the card face shows a pound sign; passing the raw code would name
    the model a unit that appears nowhere on the card."""
    _system, user = rules.build_read_messages(
        {"company_type": "operating", "currency": "GBp", "ebit_margin_pct": 24.0},
        rules.VERDICT_GREEN,
    )
    assert "£" in user
    assert "GBP" in user
    assert "GBp" not in user


def test_display_currency_falls_back_to_the_bare_code_never_a_fake_symbol() -> None:
    assert rules._display_currency("CHF") == "CHF"
    assert rules._display_currency("JPY") == "¥ (JPY)"
    assert rules._display_currency(None) == ""
    assert rules._display_currency("  ") == ""


def test_build_read_messages_omits_the_currency_line_when_absent() -> None:
    # Absent currency must not render an empty or "None"/"nan" label, the same "if a number
    # is missing, don't mention it" rule the facts block already follows.
    for absent in (None, float("nan"), ""):
        _system, user = rules.build_read_messages(
            {"company_type": "operating", "currency": absent, "ebit_margin_pct": 24.0},
            rules.VERDICT_GREEN,
        )
        assert "Currency this company trades in:" not in user
        # whole words: "nan" is a substring of "financially", "None" of "None-the-less"
        assert not re.search(r"\b(None|nan|NaN)\b", user)


def test_currency_is_hashed_so_a_corrected_currency_regenerates_the_read() -> None:
    """The prompt names the currency and the read quotes it, so it must move the hash.
    Otherwise a card whose currency is corrected upstream keeps prose naming the old one."""
    base = {"company_type": "operating", "ebit_margin_pct": 24.0, "currency": "USD"}
    usd = rules.compute_input_hash(base, rules.VERDICT_GREEN)
    eur = rules.compute_input_hash({**base, "currency": "EUR"}, rules.VERDICT_GREEN)
    assert usd != eur


def test_gbp_case_change_alone_does_not_churn_every_ftse_read() -> None:
    # GBp and GBP render identically on the card, so they must hash identically: a harmless
    # upstream case change should not force ~90 needless Haiku calls.
    base = {"company_type": "operating", "ebit_margin_pct": 24.0}
    assert rules.compute_input_hash({**base, "currency": "GBp"}, rules.VERDICT_GREEN) == (
        rules.compute_input_hash({**base, "currency": "GBP"}, rules.VERDICT_GREEN)
    )


# --- The one-sided growth axis, as the prose must state it ---------------------------------

def test_system_prompt_scopes_the_per_unit_idiom_to_margins_only() -> None:
    system = rules.READ_SYSTEM_PROMPT.lower()
    assert "a margin is a percentage, not money" in system
    assert 'the currency given on the "currency this company trades in" line below' in system
    # returns and growth have different denominators, so the idiom must not reach them
    assert "returns and growth are not amounts per unit of revenue" in system


def test_system_prompt_tells_the_model_what_to_do_with_no_currency() -> None:
    # Fails open otherwise: the rule points at a currency "named above" that isn't there,
    # which is the guess that produced the defect in the first place.
    system = rules.READ_SYSTEM_PROMPT.lower()
    assert "if there is no such line" in system
    assert "do not phrase it per unit of money at all" in system


def test_system_prompt_bars_blaming_the_verdict_on_positive_growth() -> None:
    """The verdict downgrades only on an actual decline (GROWTH_DECLINE_THRESHOLD_PCT is
    0.0), so prose blaming the badge on positive growth supplies a reason the badge does not
    contain, and re-establishes the two-sided axis the design forbids. It must NOT go further
    and deny that a flat top line is a weakness at all: +0.2% is a real-terms decline."""
    system = rules.READ_SYSTEM_PROMPT.lower()
    assert "never give it as the reason the verdict is not green" in system
    assert "describing a nearly flat top line accurately is fine" in system
    assert "never a weakness" not in system


def test_system_prompt_pins_the_growth_period_to_one_quarter() -> None:
    """`revenue_growth_yoy_pct` is the latest reported quarter against the same quarter a
    year earlier, not a full year (seed `description` and `learn` both say so). This rule is
    the only place the prompt states the period, so a wrong one here reaches every read."""
    system = rules.READ_SYSTEM_PROMPT.lower()
    assert "latest reported quarter" in system
    assert "one quarter's change, never a full year's" in system


def test_system_prompt_bars_profit_per_item() -> None:
    # A margin is per unit of REVENUE. "per unit sold" is profit per item, a different
    # number the model has no volume data to compute, so it could only fabricate it.
    system = rules.READ_SYSTEM_PROMPT.lower()
    assert "per unit of revenue, never per item sold" in system


def test_bank_only_metric_copy_never_says_sales() -> None:
    """`net_margin_pct` and `roa_pct` render ONLY on financial cards, where revenue is net
    interest plus fees rather than sales. Catalogue copy for them must not say "sale"."""
    financial_only = [
        row for row in _catalogue_rows()
        if row["applies_to"].strip() == "financial"
    ]
    assert financial_only, "expected at least one financial-only metric"
    for row in financial_only:
        for field in _VISIBLE_COPY_FIELDS:
            assert not re.search(r"\bsales?\b", row[field], re.I), (
                f"{row['metric_id']}.{field} says 'sale' on a bank-only metric: {row[field]!r}"
            )


def test_system_prompt_names_no_specific_currency() -> None:
    """The prompt is shared by every card in every market. A worked example naming a
    real currency ("24 cents in every dollar") is the same pressure that produced the defect:
    it seeds one market's currency into every other market's read."""
    assert not _names_a_currency(rules.READ_SYSTEM_PROMPT)


def test_catalogue_user_visible_copy_names_no_currency() -> None:
    """The seed is the source of truth for the card FACE via frontend/metrics.json. Without
    this, the next seed edit can put "each dollar of sales" back in front of a Japanese
    reader with CI green: nothing else checks these fields."""
    for row in _catalogue_rows():
        for field in _VISIBLE_COPY_FIELDS:
            value = row.get(field) or ""
            assert not _names_a_currency(value), (
                f"{row['metric_id']}.{field} names a currency on the card face: {value!r}"
            )


def test_prompt_pointer_names_a_line_the_message_actually_contains() -> None:
    """The system prompt points the model at a named line. If the user message ever stops
    emitting that exact label, the pointer dangles and the currency rule loses its anchor."""
    _system, user = rules.build_read_messages(
        {"company_type": "operating", "currency": "AUD", "ebit_margin_pct": 24.0},
        rules.VERDICT_GREEN,
    )
    label = "Currency this company trades in"
    assert label in user
    assert label.lower() in rules.READ_SYSTEM_PROMPT.lower()


def test_currency_symbol_maps_are_mirrors() -> None:
    """The two `_CURRENCY_SYMBOLS` copies must stay identical, and nothing pinned them.

    `scripts/assessment_rules.py` names the currency in the read prompt; `frontend/card_copy.py`
    renders it on the card face. Both files' comments say one mirrors the other, which is what
    stops the read describing a unit the card never shows. Editing one alone is worse than
    editing neither: add a franc symbol to `card_copy` only and the face shows it while every
    stored read still says CHF, with no `input_hash` movement to regenerate them, so the two
    disagree permanently. The handover's instructions for the queued CAD/SEK/DKK/NOK renderings
    depend on this holding.
    """
    from card_copy import _CURRENCY_SYMBOLS as face

    assert rules._CURRENCY_SYMBOLS == face, (
        "scripts/assessment_rules.py and frontend/card_copy.py disagree on currency symbols: "
        f"{rules._CURRENCY_SYMBOLS} vs {face}"
    )
