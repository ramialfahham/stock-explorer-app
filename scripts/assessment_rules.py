"""Deterministic per-type financial-health verdict + regeneration hash (Slice 5a).

Pure; the one file it reads is frontend/metrics.json, once. The verdict COLOR is decided here
by transparent rules, never by the LLM (5b writes only the prose read). The verdict measures **financial health /
resilience** from the card's own numbers, and it is **not** investment advice. Growth was
excluded from the verdict and now enters ONE-SIDED: a shrinking top line blocks green, while
growth never earns green and never causes red (see the policy comment below). Valuation used
to be excluded too; there is no valuation metric left to exclude, since every price-carrying
metric was dropped from the catalogue.

`INPUT_FIELDS_BY_TYPE` / `DIRECTION_BY_METRIC` mirror `dbt_analytics/seeds/metric_catalogue.csv`
(`applies_to` / `direction`), the same metric set 5b hashes and prompts over, so
"regenerate the read iff a prompt input changed" holds for the metric set. A
`tests/tooling` guard asserts this mirror stays in sync with the seed. The hash covers three
things beyond that set: the display currency, because the prompt names it and the read quotes
it; the rules' reasons for the verdict, which the prompt now gives; and whether an operating
card's margin is the annual figure, which changes its label; see `compute_input_hash`.
"""

from __future__ import annotations

import functools
import hashlib
import json
import math
import re
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any

# Verdict tokens (ASCII; the frontend maps token -> 🟢/🟡/🔴 in Slice 6).
VERDICT_GREEN = "green"
VERDICT_YELLOW = "yellow"
VERDICT_RED = "red"
VERDICTS = (VERDICT_GREEN, VERDICT_YELLOW, VERDICT_RED)

COMPANY_TYPES = ("operating", "financial", "pre_revenue")

# Bump this to force every stored 5b read to regenerate. Reads normally regenerate only when
# a card's own input hash moves, so a change to the PROMPT or to the verdict wording leaves
# existing prose untouched -- none of the numbers moved, so nothing tells the pipeline the
# text is stale. Bumping the version moves every card's hash and makes them all eligible.
#
# A card whose read failed a guard keeps no ai_read and is called again on every scheduled run,
# whatever its hash, because attach_reads regenerates an empty ai_read.
INPUT_HASH_VERSION = "5a.6"

# Per-type card metric sets, mirroring metric_catalogue.csv `applies_to`. These feed the
# input hash (and, in 5b, the prompt), so they are the FULL displayed set per type, not
# only the health axes the verdict reads.
INPUT_FIELDS_BY_TYPE: dict[str, tuple[str, ...]] = {
    "operating": (
        "ebit_margin_pct",
        "revenue_growth_yoy_pct",
        "net_debt_to_ebitda",
        "fcf_margin_pct",
        "debt_to_equity",
        "current_ratio_stmt",
        "statement_roe_pct",
    ),
    "financial": (
        "revenue_growth_yoy_pct",
        "statement_roe_pct",
        "net_margin_pct",
        "roa_pct",
    ),
    "pre_revenue": (
        "net_cash",
        "working_capital",
        "cash_runway_months",
        "burn_rate_monthly",
    ),
}

# Direction per metric, mirroring metric_catalogue.csv `direction`.
DIRECTION_BY_METRIC: dict[str, str] = {
    "ebit_margin_pct": "higher_better",
    "revenue_growth_yoy_pct": "higher_better",
    "net_debt_to_ebitda": "lower_better",
    "fcf_margin_pct": "higher_better",
    "debt_to_equity": "lower_better",
    "current_ratio_stmt": "higher_better",
    "statement_roe_pct": "higher_better",
    "net_margin_pct": "higher_better",
    "roa_pct": "higher_better",
    "net_cash": "higher_better",
    "working_capital": "higher_better",
    "cash_runway_months": "higher_better",
    "burn_rate_monthly": "lower_better",
}


def _is_missing(value: Any) -> bool:
    return value is None or (isinstance(value, float) and math.isnan(value))


def _band(value: Any, direction: str, weak_th: float, good_th: float) -> str:
    """Classify one metric into good | ok | weak | unknown.

    Convention: `good` is inclusive of its threshold; `weak` is strictly beyond
    `weak_th`. `weak_th`/`good_th` are expressed on the metric's own scale.
    """
    if _is_missing(value):
        return "unknown"
    v = float(value)
    if direction == "higher_better":
        if v >= good_th:
            return "good"
        if v < weak_th:
            return "weak"
        return "ok"
    # lower_better
    if v <= good_th:
        return "good"
    if v > weak_th:
        return "weak"
    return "ok"


def _axis(row: Mapping[str, Any], metric: str, weak_th: float, good_th: float) -> str:
    """Band a metric using its catalogue-mirrored direction."""
    return _band(row.get(metric), DIRECTION_BY_METRIC[metric], weak_th, good_th)


# --- Ratio sign-inversion guards ---------------------------------------------------------
# Three ratios can flip sign when their denominator goes negative, and banding the flipped value
# by raw magnitude reads a distressed or thin-equity company as "good" on that axis. All three
# cases are already named in metric_catalogue.csv's own applicability text: net_debt_to_ebitda
# "explodes when EBITDA ~ 0 (distressed/pre-profit)"; debt_to_equity "flips or explodes and stops
# being meaningful" when equity goes negative; statement_roe_pct "can read as a spuriously
# positive percentage" over negative equity. statement_roe_pct's guard is used from BOTH
# _evaluate_operating and _evaluate_financial, not operating only.
#
# All three guards check the RATIO'S OWN DENOMINATOR directly (info_ebitda,
# stmt_stockholders_equity), not the ratio's sign, because the ratio's sign fails for a different
# reason per metric. net_debt_to_ebitda's numerator can itself be negative (genuine net cash), so
# a negative EBITDA divided into a negative net debt gives an ambiguous positive ratio no
# different in sign from a genuinely low-leverage company. statement_roe_pct's numerator (net
# income) can also legitimately be negative (a real loss), so the SAME double-negative ambiguity
# applies there: whenever equity is negative, a genuine loss divides out to a spuriously positive
# percentage indistinguishable in sign from real profit over positive equity -- which is why the
# guard keys on equity's own sign alone and does not need to look at net income's sign at all.
# debt_to_equity's failure mode is different again: its numerator (total debt) is never negative
# in this data, but CAN be exactly zero, and zero divided by a negative number is zero, not
# negative, so a debt-free company with negative equity would silently evade a check on the
# ratio's own sign even though total debt itself never goes negative. All raw denominators are
# passed through the mart for exactly this reason; see their own column comments in
# int_stock__card_metrics.sql.
#
# The guards land on different bands because the axes play different roles, and the SAME axis
# can play a different role in a different verdict function. net_debt_to_ebitda is a CORE axis in
# _evaluate_operating (every core axis must be "good" for green), so it is fixed by treating it as
# "unknown" -- the same neutral treatment every other axis already gets for a missing value.
# debt_to_equity is a SUPPORTING axis, which never needs to be "good" to reach green -- only
# "weak" changes anything, since supporting axes can block green but never rescue it. Relabeling
# negative equity "unknown" there would have been a no-op on every card's actual color, which is
# not a fix. So it is banded "weak" instead, capping the card at yellow, the same ceiling every
# other weak supporting axis already has, never forcing red on its own. Negative equity is not
# always distress on its own (it can come from a healthy company's own buybacks, per the
# catalogue's own applicability note) -- "weak" is deliberately the mildest band that still
# changes anything, a caution rather than a verdict on the cause. statement_roe_pct gets the same
# "weak" treatment in _evaluate_operating (same supporting role as debt_to_equity), but "unknown"
# in _evaluate_financial, where it is effectively a CORE axis -- see the comment in
# _evaluate_financial for why that function's population makes "unknown" the honest choice rather
# than the harsher "weak" a first version of this guard used.


def _axis_unless_denominator_nonpositive(
    row: Mapping[str, Any],
    metric: str,
    denominator_field: str,
    bad_band: str,
    weak_th: float,
    good_th: float,
) -> str:
    """Like `_axis`, but `bad_band` when the ratio's own denominator is present and <= 0.

    Dividing by a non-positive denominator breaks the ratio's normal higher/lower-is-better
    meaning regardless of the numerator's sign -- net cash divided by negative EBITDA can look
    identical in sign to real debt divided by negative EBITDA, and a debt-free company divided by
    negative equity looks identical in sign to a company with no debt problem at all (0 either
    way). Checking the denominator directly, not the ratio, resolves both. A MISSING denominator
    does not trigger this: only a denominator we can actually see is bad, matching every other
    axis's missing-means-unknown treatment rather than assuming without evidence.
    """
    denominator = row.get(denominator_field)
    if not _is_missing(denominator) and float(denominator) <= 0:
        return bad_band
    return _axis(row, metric, weak_th, good_th)


# --- Per-type verdict policies (owner-signed §6 bands; conservative worst-axis-wins) ---
# The verdict is HEALTH/resilience: leverage, profitability, cash, liquidity, runway, and
# revenue growth, but growth counts in ONLY one direction. Valuation used to be excluded
# here too; there is no valuation metric left to exclude, since forward_pe,
# price_to_tangible_book and dividend_yield_pct were dropped from the catalogue for carrying
# the share price this twice-monthly pipeline cannot keep current.
#
# GROWTH IS ONE-SIDED, and that asymmetry is the entire design. A shrinking top line blocks
# green; growth never earns green and never causes red. Growth was excluded from the verdict
# originally for a real reason -- a company can grow into losses, so high growth is not health
# -- and the owner's rule that every metric shown must feed the verdict had to be satisfied
# without discarding that. One-sidedness does both. Do NOT "simplify" this into a symmetric
# good/weak axis: that would let momentum buy a health verdict, which is the thing the
# exclusion existed to prevent.
GROWTH_DECLINE_THRESHOLD_PCT = 0.0
# Any year-over-year decline, with no tolerance band. An earlier draft proposed -5% on the
# argument that a single quarter is noisy; the owner rejected it. Year-over-year compares the
# same quarter a year earlier, so the figure is not seasonal noise. It is still only one
# quarter: a decline can also come from a divestment, FX translation, contract timing or an
# unusually strong prior-year base, none of which this number distinguishes. That is why the
# axis is one-sided and can only withhold green, never cause red.
# Do not reintroduce a tolerance band.


def _is_shrinking(row: Mapping[str, Any]) -> bool:
    """True when revenue went backwards year over year. Null growth is NOT shrinking --
    absent data must never block a green verdict, the same way every other axis treats a
    missing value as unknown rather than bad."""
    value = row.get("revenue_growth_yoy_pct")
    if _is_missing(value):
        return False
    return float(value) < GROWTH_DECLINE_THRESHOLD_PCT


# --- Joint liquidity evaluation (current_ratio_stmt relief from FCF covering the shortfall) ----
# current_ratio_stmt and fcf_margin_pct were graded fully independently, so strong free cash flow could never rescue a
# merely-weak current ratio. Relief compares actual dollar amounts -- does free cash flow cover
# the working-capital shortfall? -- rather than fcf_margin_pct, because that margin is scaled by
# revenue, not by the size of the liquidity gap: a company with modest revenue but a large
# near-term liability wall could clear a "good" margin while its cash barely covers the shortfall.
CURRENT_RATIO_WEAK_TH = 1.0
CURRENT_RATIO_GOOD_TH = 1.5

# Owner-decided floor: below this, current liabilities are more than double current
# assets -- the level where a company is fully dependent on uninterrupted cash inflow with zero
# cushion, a real distress signal no amount of free cash flow should paper over. Relief only ever
# raises a "weak" current ratio to "ok", never to "good": free cash flow covering the shortfall
# earns relief from a borderline ratio, not a claim that the ratio itself is actually strong.
CURRENT_RATIO_LIQUIDITY_FLOOR = 0.5


def _current_ratio_axis_with_fcf_coverage_relief(row: Mapping[str, Any]) -> str:
    """Like `_axis(row, "current_ratio_stmt", ...)`, but "ok" instead of "weak" when free cash
    flow (stmt_free_cash_flow) covers the working-capital shortfall (-working_capital) and
    current_ratio_stmt is not below the liquidity floor.

    Only the "weak" case is touched -- a genuinely good or already-unknown current ratio is
    unaffected. Relief requires BOTH stmt_free_cash_flow and working_capital to actually be
    present and evidence a real shortfall (working_capital < 0) -- missing data earns no relief,
    the same "only apply an exception when we have positive evidence for it" stance the
    sign-inversion guards above take, not the reverse.
    """
    band = _axis(row, "current_ratio_stmt", weak_th=CURRENT_RATIO_WEAK_TH, good_th=CURRENT_RATIO_GOOD_TH)
    if band != "weak":
        return band
    # band == "weak" only reachable when current_ratio_stmt is present -- _band returns
    # "unknown" for a missing value before ever comparing it to a threshold.
    if float(row["current_ratio_stmt"]) < CURRENT_RATIO_LIQUIDITY_FLOOR:
        return "weak"
    fcf = row.get("stmt_free_cash_flow")
    shortfall = row.get("working_capital")
    if _is_missing(fcf) or _is_missing(shortfall) or float(shortfall) >= 0:
        return "weak"
    if float(fcf) >= -float(shortfall):
        return "ok"
    return "weak"


@dataclass(frozen=True)
class Axis:
    """One metric the verdict rules judged: `role` is "core" or "supporting", `band` is good, ok,
    weak or unknown, and `note` says in plain words when a guard or the current-ratio relief applied."""

    field: str
    role: str
    band: str
    note: str = ""


@dataclass(frozen=True)
class VerdictEvaluation:
    """The verdict with the rules' own reasons, from one computation, so the two cannot drift apart.

    `red_because` lists the core metrics that were weak; `held_back_by` lists what kept a card
    from green (core metrics that are not good, weak supporting metrics, and a falling top line,
    named "revenue_growth_yoy_pct"). Both are empty when they do not apply."""

    verdict: str
    axes: tuple[Axis, ...]
    shrinking: bool
    red_because: tuple[str, ...]
    held_back_by: tuple[str, ...]


EBITDA_NOTE = "EBITDA is zero or negative"
EQUITY_NOTE = "equity is zero or negative"
RELIEF_NOTE = "free cash flow covers the short-term shortfall"
NO_BURN_NOTE = "no cash burn is shown"


def _guard_note(row: Mapping[str, Any], denominator_field: str, text: str) -> str:
    denominator = row.get(denominator_field)
    return text if not _is_missing(denominator) and float(denominator) <= 0 else ""


def _evaluation(verdict: str, axes: tuple[Axis, ...], shrinking: bool, held_roa: bool = False) -> VerdictEvaluation:
    red = tuple(a.field for a in axes if a.role == "core" and a.band == "weak")
    held = tuple(
        a.field for a in axes
        if (a.role == "core" and a.band != "good") or (a.role == "supporting" and a.band == "weak")
    )
    if held_roa and "roa_pct" not in held:
        held += tuple(a.field for a in axes if a.field == "roa_pct")
    if shrinking:
        held += ("revenue_growth_yoy_pct",)
    return VerdictEvaluation(
        verdict=verdict,
        axes=axes,
        shrinking=shrinking,
        red_because=red if verdict == VERDICT_RED else (),
        held_back_by=held if verdict == VERDICT_YELLOW else (),
    )


def _relief_note(row: Mapping[str, Any], band: str) -> str:
    """RELIEF_NOTE when the relief turned a weak current ratio into ok."""
    raw = _axis(row, "current_ratio_stmt", weak_th=CURRENT_RATIO_WEAK_TH, good_th=CURRENT_RATIO_GOOD_TH)
    return RELIEF_NOTE if raw == "weak" and band == "ok" else ""


def _evaluate_operating(row: Mapping[str, Any]) -> VerdictEvaluation:
    # Core axes are eligibility-required, so present for eligible operating cards.
    # net_debt_to_ebitda goes through the sign-inversion guard: "unknown" (not "good") when
    # info_ebitda is present and <= 0, so a distressed company can't reach green just because
    # dividing by negative earnings flipped the ratio's sign favorably.
    core = (
        _axis_unless_denominator_nonpositive(
            row, "net_debt_to_ebitda", "info_ebitda", "unknown", weak_th=3.0, good_th=1.5
        ),
        _axis(row, "ebit_margin_pct", weak_th=0.0, good_th=10.0),
        _axis(row, "fcf_margin_pct", weak_th=0.0, good_th=5.0),
    )
    # Supporting axes may be null; they can break a tie but never rescue a red flag.
    # debt_to_equity and statement_roe_pct both go through the same sign-inversion guard: "weak"
    # (not "unknown", which would be a no-op on a supporting axis) when stmt_stockholders_equity
    # is present and <= 0, capping the card at yellow, the same ceiling any other weak supporting
    # axis already gets. A loss over negative equity divides out to a spuriously POSITIVE
    # statement_roe_pct, the exact case the catalogue's own applicability note warns about.
    # current_ratio_stmt goes through the joint-liquidity-evaluation relief: "ok" (not "weak")
    # when it would otherwise band weak, free cash flow covers the working-capital shortfall,
    # and it isn't below the liquidity floor -- see the comment above
    # _current_ratio_axis_with_fcf_coverage_relief.
    supporting = (
        _axis_unless_denominator_nonpositive(
            row, "debt_to_equity", "stmt_stockholders_equity", "weak", weak_th=2.0, good_th=1.0
        ),
        _current_ratio_axis_with_fcf_coverage_relief(row),
        _axis_unless_denominator_nonpositive(
            row, "statement_roe_pct", "stmt_stockholders_equity", "weak", weak_th=0.0, good_th=10.0
        ),
    )
    if any(b == "weak" for b in core):
        verdict = VERDICT_RED
    elif (
        all(b == "good" for b in core)
        and not any(b == "weak" for b in supporting)
        and not _is_shrinking(row)
    ):
        verdict = VERDICT_GREEN
    else:
        verdict = VERDICT_YELLOW
    axes = (
        Axis("net_debt_to_ebitda", "core", core[0], _guard_note(row, "info_ebitda", EBITDA_NOTE)),
        Axis("ebit_margin_pct", "core", core[1]),
        Axis("fcf_margin_pct", "core", core[2]),
        Axis("debt_to_equity", "supporting", supporting[0], _guard_note(row, "stmt_stockholders_equity", EQUITY_NOTE)),
        Axis("current_ratio_stmt", "supporting", supporting[1], _relief_note(row, supporting[1])),
        Axis("statement_roe_pct", "supporting", supporting[2], _guard_note(row, "stmt_stockholders_equity", EQUITY_NOTE)),
    )
    return _evaluation(verdict, axes, _is_shrinking(row))


def _evaluate_financial(row: Mapping[str, Any]) -> VerdictEvaluation:
    # Banks: profitability/returns only. Capital adequacy (CET1/Tier 1) is unsourceable
    # from yfinance, so this verdict is deliberately modest (documented in data_contract).
    # statement_roe_pct goes through the same sign-inversion guard as the operating verdict, but
    # bands "unknown" here (roe is core-like in this function: "unknown" still blocks green,
    # since only "good" counts, but does NOT force red the way "weak" would).
    #
    # An earlier version of this guard used "weak" here, forcing red outright, reasoned from US
    # bank capital regulation (the FDIC's Prompt Corrective Action framework requires regulatory
    # intervention well before a bank's capital depletion reaches zero). A review caught that
    # this overreached what the data actually supports: company_type == 'financial' is the whole
    # GICS "Financial Services" sector (insurers, asset managers, broker-dealers, payment
    # networks, exchanges, mortgage finance -- not only depository banks), spans markets under
    # entirely different regulatory regimes (this app covers US, UK, Japan, Australia, Germany,
    # France, Netherlands, Switzerland, Spain), and includes firms (e.g. payment networks) known
    # for the same benign buyback-driven negative equity operating companies can have. Nothing in
    # the data distinguishes a bank in real distress from a payment network mid-buyback, so
    # "unknown" -- the same neutral, no-severity-claim treatment every other axis gets for
    # information this app cannot actually determine -- is the honest choice, not "weak".
    roe = _axis_unless_denominator_nonpositive(
        row, "statement_roe_pct", "stmt_stockholders_equity", "unknown", weak_th=0.0, good_th=8.0
    )
    margin = _axis(row, "net_margin_pct", weak_th=0.0, good_th=15.0)
    roa = _axis(row, "roa_pct", weak_th=0.0, good_th=0.8)
    if roe == "weak" or margin == "weak":
        verdict = VERDICT_RED
    elif (
        roe == "good"
        and margin == "good"
        and roa in ("good", "unknown")
        and not _is_shrinking(row)
    ):
        verdict = VERDICT_GREEN
    else:
        verdict = VERDICT_YELLOW
    axes = (
        Axis("statement_roe_pct", "core", roe, _guard_note(row, "stmt_stockholders_equity", EQUITY_NOTE)),
        Axis("net_margin_pct", "core", margin),
        Axis("roa_pct", "supporting", roa),
    )
    return _evaluation(verdict, axes, _is_shrinking(row), held_roa=roa not in ("good", "unknown"))


def _evaluate_pre_revenue(row: Mapping[str, Any]) -> VerdictEvaluation:
    # Survival story. cash_runway_months is null when NOT burning cash (a positive),
    # treat null runway as good; the net-cash and working-capital axes independently
    # catch a genuinely fragile pre-revenue company.
    runway_val = row.get("cash_runway_months")
    runway = "good" if _is_missing(runway_val) else _axis(
        row, "cash_runway_months", weak_th=12.0, good_th=24.0
    )
    # net_cash is a MONEY AMOUNT, not the old ratio against market cap, so
    # there is no scale-free "good" level any more: 0.2 meant "net cash worth a fifth of the
    # company's market value", and no equivalent exists in currency terms across companies of
    # different sizes. Both thresholds collapse to zero, i.e. the axis now asks only "is there
    # more cash than debt". That makes green marginally easier to reach for a pre-revenue
    # card; the runway and working-capital axes still carry the rest of the judgement.
    # Flagged to the owner rather than absorbed silently.
    net_cash = _axis(row, "net_cash", weak_th=0.0, good_th=0.0)
    working_capital = _axis(row, "working_capital", weak_th=0.0, good_th=0.0)
    if runway == "weak" or net_cash == "weak" or working_capital == "weak":
        verdict = VERDICT_RED
    elif runway == "good" and net_cash == "good" and working_capital == "good":
        verdict = VERDICT_GREEN
    else:
        verdict = VERDICT_YELLOW
    axes = (
        Axis("cash_runway_months", "core", runway, NO_BURN_NOTE if _is_missing(runway_val) else ""),
        Axis("net_cash", "core", net_cash),
        Axis("working_capital", "core", working_capital),
    )
    return _evaluation(verdict, axes, False)


def normalize_company_type(company_type: Any) -> str:
    """Resolve to one of COMPANY_TYPES; null/unknown -> operating (mirrors the frontend)."""
    if company_type in COMPANY_TYPES:
        return str(company_type)
    return "operating"


_EVALUATE_FN = {
    "operating": _evaluate_operating,
    "financial": _evaluate_financial,
    "pre_revenue": _evaluate_pre_revenue,
}


def evaluate_verdict(row: Mapping[str, Any]) -> VerdictEvaluation:
    """The verdict and the rules' own reasons for it, from one computation."""
    return _EVALUATE_FN[normalize_company_type(row.get("company_type"))](row)


def compute_verdict(row: Mapping[str, Any]) -> str:
    """Deterministic health verdict for a card row. Total: always returns a VERDICTS member."""
    return evaluate_verdict(row).verdict


def _canonical_number(value: Any) -> float | None:
    """Round numerics to 6dp and coerce missing/NaN to None so float noise doesn't
    force a spurious 5b regeneration."""
    if _is_missing(value):
        return None
    try:
        return round(float(value), 6)
    except (TypeError, ValueError):
        return None


def compute_input_hash(
    row: Mapping[str, Any], verdict: str, *, version: str = INPUT_HASH_VERSION
) -> str:
    """sha256 hex over the canonicalized per-type input set + company_type + verdict +
    display currency + the rules' reasons for the verdict (each judged metric's band and guard
    note, and whether revenue is falling) + whether an operating card's margin is the annual
    figure + version.

    5b regenerates the prose read only when this hash changes. Numbers only, plus the
    currency: name/sector are context, not signals ("reason only from the given numbers"),
    but the currency is named in the prompt and the read quotes it, so a card whose currency
    is corrected upstream must regenerate rather than keep prose naming the old one. Hashed
    through `_display_currency` so a GBp/GBP change, which the card face never shows, does
    not churn every FTSE read for nothing.
    """
    ctype = normalize_company_type(row.get("company_type"))
    evaluation = evaluate_verdict(row)
    annual_margin = ctype == "operating" and row.get("ebit_margin_basis") == "annual_latest"
    payload = {
        "version": version,
        "reasons": [[a.field, a.band, a.note] for a in evaluation.axes] + [evaluation.shrinking],
        "annual_margin": annual_margin,
        "company_type": ctype,
        "verdict": verdict,
        "currency": _display_currency(row.get("currency")) or None,
        "inputs": {field: _canonical_number(row.get(field)) for field in INPUT_FIELDS_BY_TYPE[ctype]},
    }
    blob = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()


# --- Slice 5b: the Claude-written prose "read" -------------------------------
# The verdict COLOR is decided above by rules; the LLM writes ONLY the prose read.
# Everything here is pure (no I/O, no anthropic import) so it unit-tests offline;
# scripts/generate_assessments.py makes the actual Claude Haiku call.

# Owner-signed voice (§6). Educational, never advice; true-beginner language;
# reason only from the given numbers; one fact and its meaning per sentence, never the verdict
# itself (the card's badge shows it), never a buy/sell.
READ_SYSTEM_PROMPT = """You write a short, plain-language "read" of a company's financial health for a complete beginner using a stock-learning app. You are given the company type, a set of already-computed numbers, and a health verdict (green, yellow, or red) that fixed rules decided - not you. In 2-3 sentences, explain what those numbers say about the company's financial health. The card shows each sentence as its own bullet and shows the verdict in a badge right above your text, so every sentence states one fact from the numbers and what it means in plain words, and none of them states or restates the verdict.

Rules:
- Respond by calling the write_card_read tool with three fields: "read" (the prose),
  "referenced_metrics" (one entry per metric from the numbers list below that the read explicitly
  cites, each with "label" and "value_as_shown" copied EXACTLY as given below, character for
  character, not reformatted, rounded, or recomputed), and "verdict_meaning" (which of
  healthy/mixed/fragile your overall reading of the numbers lands on; it is never shown to the
  reader and must match the health verdict given below). Never invent a label or value that is
  not in the numbers list.
- Educational only. Never give investment advice. Do not say or imply whether to buy, sell, hold, or avoid the share, whether it is cheap, expensive, or "worth it", and never predict the price. You explain what the numbers describe; you never recommend an action.
- Never use the words buy, buys, buying, sell, sells, selling or price anywhere, even about what the company does or charges: say "revenue" instead ("sales" is fine for an operating company), or name what it makes. A check rejects the whole read if any of them appears.
- Write for someone who knows no finance vocabulary. If you use a term, gloss it in plain words or an everyday comparison. Leave no jargon unexplained.
- Reason only from the numbers given. Do not invent or assume anything about the company's products, industry, news, management, or history, and bring in no outside facts. If a number is missing, don't mention it - never guess.
- Money amounts already carry their own currency symbol or code - use it exactly as given; never assume, add, or convert to a different currency (these companies report in different currencies).
- A margin is a percentage, not money. Explaining one as the amount kept out of every unit of revenue is good teaching and is encouraged, but it must use the currency given on the "Currency this company trades in" line below and no other, whichever currency that turns out to be. Where that currency has no everyday small unit, say it per 100 units of that same currency instead. If there is no such line, describe the margin as a percentage or a share and do not phrase it per unit of money at all. Never mix two currencies in one explanation. A margin is per unit of revenue, never per item sold: you are not told how many units the company delivers and must never imply profit per item.
- Returns and growth are NOT amounts per unit of revenue, so never phrase them that way. Return on equity is profit measured against the owners' money, and return on assets is profit measured against everything the company owns. Revenue growth compares the latest reported quarter with the same quarter a year earlier, so it is one quarter's change, never a full year's: do not write "this year" or "over the year" about it.
- Write short sentences. Each sentence has one topic, is in the active voice, and has at most 25 words. Each sentence states one of the numbers below in digits, exactly as it appears (for example 24.0%), and says what it means in plain words, using the wording of that number's Meaning line. Use one word for one thing: call a number by the name it has in the list, every time. Pick the 2 or 3 numbers that most shape the picture.
- Explain a number with the Meaning and Limit lines given for it under the numbers list, and say any finance term in plain words. Use a Limit line only when it applies to this company. Never say why the company has a number, how it got there, what it plans, or what the company can or cannot do. Write in words, never the symbols ≈, → or ÷.
- Write every number in digits, never as a fraction or a phrase in words ("one third", "a quarter of", "a fifth", "half", "one in five"). A time period such as "the latest quarter" is not a number. Never write a currency symbol or code without an amount next to it.
- The Why lines under the numbers say how the rules reached the verdict. Explain what is strong or weak only with those lines, and give no other reason for the verdict. Falling revenue can stop a company being called healthy but never makes it red. Rising revenue does not make a company healthy, and is never a reason to buy.
- Do not state the verdict or say it again in other words, and do not close with a summary of the whole picture ("these numbers together...", "on these figures it is..."): the badge above your text does that. Put what is strong first, if anything is. If the verdict is red, the last sentence names the figure that is actually poor (a loss, negative free cash flow, heavy net debt, short runway, negative net cash meaning more borrowed than held in cash, negative working capital); falling revenue alone never makes a company red, so never name it as the cause of red. If the verdict is yellow, the last sentence names the weakest figure, or says which figure is only modest, or that a measure could not be worked out, when nothing shown is clearly weak; never invent a weakness the numbers do not show. If the verdict is green, add no caveat sentence. A financial company's read still states the limit given in the lens below, as one of its 2-3 sentences. Never call a green company fragile or a red one healthy. Never phrase anything as a good or bad buy.
- No dashes as punctuation. Never use an em dash or en dash. Use a comma, a full stop, or brackets instead. Hyphens inside ordinary compound words are fine.
- Write like a person explaining this to someone they know, not like a model. Avoid the usual tells: no "not just X, but Y", no "it's worth noting" or "it's important to remember", no rhetorical questions, no three-item lists used for rhythm, no sentence that hedges and then pivots for the sake of sounding balanced. Vary your sentence lengths. Say the thing and stop. Plain is not the same as chatty, so stay calm and factual. This rule is about STYLE only: it never overrides the rules above or the company-type lens below. Where one of those requires a limit to be stated - above all the financial-company limit that these numbers cannot judge balance-sheet safety or capital strength - state it plainly and in full. A required caveat is never a tell to be trimmed.
- Calm, clear, honest. No hype, no emoji, no exclamation marks.

Company-type lens:
- operating: profitability (does it earn on sales?), leverage (how much it has borrowed), cash generation.
- financial: profitability and returns (margin, return on equity, return on assets). State the honest limit: this shows profitability only - it can't judge this financial company's balance-sheet safety or capital strength, which these numbers don't show. Its revenue is net interest plus fees, never sales, even where a Meaning line says sales.
- pre_revenue: a survival story - not profitable yet, so focus on cash, how fast it is spending (burn), and how long the cash lasts (runway). Health = staying power, not profit."""


# Plain-English meaning of each verdict token, given to the model as context for its hidden
# verdict_meaning field, never to be written in the read. Mirrors the frontend token -> emoji
# mapping added in Slice 6.
VERDICT_MEANING: dict[str, str] = {
    VERDICT_GREEN: "green - financially healthy on these figures",
    VERDICT_YELLOW: "yellow - a mixed financial picture on these figures",
    VERDICT_RED: "red - financially fragile on these figures",
}

# The single word each verdict's meaning boils down to, for the write_card_read tool's
# verdict_meaning field (below) -- what the model classifies its OWN overall reading as (hidden
# from the reader), checked against the verdict already decided by (deterministic, non-LLM)
# rules above.
VERDICT_MEANING_WORD: dict[str, str] = {
    VERDICT_GREEN: "healthy",
    VERDICT_YELLOW: "mixed",
    VERDICT_RED: "fragile",
}


# Forces structured output instead of free text: the model must name which facts it used, in the
# exact form it was given them, so scripts/generate_assessments.py can check the read against
# the card's own numbers before storing it -- a numeric hallucination guard, not an LLM judge.
# verdict_meaning is the model's own overall classification, as a separate enum-constrained
# field the reader never sees, checked in code against the verdict already decided (never the
# model's call). Nothing reads the prose against the verdict; the prompt alone keeps the read
# from stating or contradicting it.
# Pure data, no I/O; the actual API call lives in scripts/generate_assessments.py.
READ_TOOL_NAME = "write_card_read"
READ_TOOL_SCHEMA: dict[str, Any] = {
    "name": READ_TOOL_NAME,
    "description": "Write the plain-language financial health read for this card.",
    "input_schema": {
        "type": "object",
        "properties": {
            "read": {
                "type": "string",
                "description": "The 2-3 sentence plain-language read, one fact and its meaning per sentence, never stating the verdict, following every rule in the system prompt.",
            },
            "referenced_metrics": {
                "type": "array",
                "description": (
                    "One entry per metric from the numbers list that the read explicitly cites. "
                    "Copy label and value_as_shown EXACTLY as given in the numbers list -- do "
                    "not reformat, round, or recompute either one. Empty if the read cites no "
                    "specific number."
                ),
                "items": {
                    "type": "object",
                    "properties": {
                        "label": {
                            "type": "string",
                            "description": "The metric's label exactly as it appears in the numbers list, e.g. 'Operating margin (TTM)'.",
                        },
                        "value_as_shown": {
                            "type": "string",
                            "description": "That metric's value exactly as it appears in the numbers list, e.g. '24.0%'.",
                        },
                    },
                    "required": ["label", "value_as_shown"],
                },
            },
            "verdict_meaning": {
                "type": "string",
                "enum": ["healthy", "mixed", "fragile"],
                "description": (
                    "Your own overall reading of the numbers: healthy, mixed, or fragile. "
                    "Never shown to the reader. Must match the Health verdict given above, and "
                    "the read itself must not state it."
                ),
            },
        },
        "required": ["read", "referenced_metrics", "verdict_meaning"],
    },
}


# Per-metric brief for the facts block: label + a value format. The meaning text beside each
# number is the catalogue gloss plus its direction cue, built by read_metric_meaning; it is not
# written here. Keys MUST
# cover every field in INPUT_FIELDS_BY_TYPE, every label is the
# catalogue's label for that metric, and every fmt renders the value exactly as
# frontend/card_copy.py renders it on the card face; tests/tooling pins all three against
# dbt_analytics/seeds/metric_catalogue.csv, so the read can only cite what the reader sees
# beside it. (Owner-signed §6, alongside READ_SYSTEM_PROMPT.)
READ_METRIC_BRIEF: dict[str, dict[str, str]] = {
    "ebit_margin_pct": {
        "label": "Operating margin (TTM)",
        "fmt": "pct",
    },
    "revenue_growth_yoy_pct": {
        "label": "Rev growth YoY (quarter)",
        "fmt": "pct",
    },
    "net_debt_to_ebitda": {
        "label": "Net debt / EBITDA",
        "fmt": "ratio",
    },
    "fcf_margin_pct": {
        "label": "FCF margin (annual)",
        "fmt": "pct",
    },
    "debt_to_equity": {
        "label": "Debt / equity",
        "fmt": "ratio",
    },
    "current_ratio_stmt": {
        "label": "Current ratio",
        "fmt": "ratio",
    },
    "statement_roe_pct": {
        "label": "Return on equity",
        "fmt": "pct",
    },
    "net_margin_pct": {
        "label": "Net margin",
        "fmt": "pct",
    },
    "roa_pct": {
        "label": "Return on assets",
        "fmt": "pct",
    },
    "net_cash": {
        "label": "Net cash",
        "fmt": "currency",
    },
    "working_capital": {
        "label": "Working capital",
        "fmt": "currency",
    },
    "cash_runway_months": {
        "label": "Cash runway",
        "fmt": "ratio_1",
    },
    "burn_rate_monthly": {
        "label": "Cash burn (monthly)",
        "fmt": "currency",
    },
}


# Currency symbols for the money-amount metrics; mirrors frontend/card_copy.py so the
# read names the SAME currency the card face shows. Unknown code -> the code itself
# (never a fake symbol). The app spans markets in ten currencies, so "$" is not a safe
# default. The owner's rule is to use whatever form that currency takes in real
# practice. CHF has no entry and renders as "CHF", which IS the practical form, so it stays.
# CAD gets "C$", following AUD; SEK, DKK and NOK stay bare ISO codes, because "kr" names
# three different currencies and this app shows markets side by side.
_CURRENCY_SYMBOLS = {"USD": "$", "GBP": "£", "JPY": "¥", "EUR": "€", "AUD": "A$", "CAD": "C$"}


def _display_currency(currency: str | None) -> str:
    """The currency the CARD FACE shows, as the read should name it: '£ (GBP)', 'CHF', ''.

    The mart's `currency` is a DISPLAY code, not the statement currency (`stmt_currency`
    exists in fct_fundamentals_snapshot but is not carried into the mart), so this is
    deliberately phrased as what the reader sees rather than as what the company files.
    Upper-casing is what makes 'GBp' safe: yfinance reports LSE tickers in pence, and every
    other consumer (_compact_amount, frontend/card_copy.py) already collapses it to GBP so
    the card face shows a pound sign. Passing the raw code to the model would name a unit
    that appears nowhere on the card.
    """
    # Guarded here, not only in build_read_messages: compute_input_hash calls this too, and
    # a NaN currency would raise on .strip().
    if _is_missing(currency):
        return ""
    code = str(currency).strip().upper()
    if not code:
        return ""
    symbol = _CURRENCY_SYMBOLS.get(code)
    return f"{symbol} ({code})" if symbol else code


def _compact_amount(value: float, currency: str | None) -> str:
    """Compact, sign-aware money amount WITH the card's currency:
    2_100_000_000 / 'GBP' -> '£2.1B'; -5.0e7 / 'JPY' -> '-¥50.0M'; unknown code kept
    literal ('CHF 2.1B'); no code -> bare magnitude."""
    code = (currency or "").upper()
    symbol = _CURRENCY_SYMBOLS.get(code) or (f"{code} " if code else "")
    v = float(value)
    sign = "-" if v < 0 else ""
    magnitude = abs(v)
    for suffix, size in (("B", 1e9), ("M", 1e6), ("K", 1e3)):
        if magnitude >= size:
            return f"{sign}{symbol}{magnitude / size:.1f}{suffix}"
    return f"{sign}{symbol}{magnitude:.0f}"


def _format_metric_value(value: Any, fmt: str, currency: str | None = None) -> str:
    v = float(value)
    if fmt == "pct":
        return f"{v:.1f}%"
    if fmt == "ratio_1":
        return f"{v:.1f}"
    if fmt == "currency":
        return _compact_amount(v, currency)
    return f"{v:.2f}"  # ratio


def read_metric_label(field: str, row: Mapping[str, Any]) -> str:
    """The label the card face shows for this metric on THIS row. One metric's label depends
    on the row: operating margin says "(annual)" when the mart fell back to the latest annual
    statement (ebit_margin_basis == "annual_latest"), mirroring frontend/card_copy.py's
    metric_label; a test pins the two equal for both bases."""
    if field == "ebit_margin_pct" and row.get("ebit_margin_basis") == "annual_latest":
        return "Operating margin (annual)"
    return READ_METRIC_BRIEF[field]["label"]


@functools.lru_cache(maxsize=1)
def _catalogue_text() -> dict[str, dict[str, str]]:
    """metric_id -> catalogue text, from frontend/metrics.json (generated from the seed, kept
    equal to it by tests/tooling/test_metric_catalogue.py). The one place this module reads a file."""
    path = Path(__file__).resolve().parents[1] / "frontend" / "metrics.json"
    metrics = json.loads(path.read_text(encoding="utf-8"))["metrics"]
    return {m["metric_id"]: m for m in metrics}


def read_metric_meaning(field: str, row: Mapping[str, Any]) -> str:
    """The definition the read is given for this metric on THIS row: the catalogue gloss plus its
    direction cue, mirroring frontend/card_copy.py's metric_gloss(benchmarked=False) with its
    three row-specific forms (a test pins the two equal). One deliberate difference: a negative
    debt ratio with non-positive EBITDA is not called net cash, because negative EBITDA also
    makes the ratio negative. `interpretation` is not used: it carries rationale, and a
    definition states what the thing is (ISO/IEC 11179-4)."""
    value = row.get(field)
    present = not _is_missing(value)
    if field == "net_debt_to_ebitda" and present and float(value) < 0:
        ebitda = row.get("info_ebitda")
        if _is_missing(ebitda) or float(ebitda) > 0:
            return "Net cash: cash on hand exceeds debt"
    if field == "debt_to_equity" and present and float(value) < 0:
        return "Negative equity, so this ratio isn't a normal leverage read"
    if field == "ebit_margin_pct" and row.get("ebit_margin_basis") == "annual_latest":
        base = "Operating profit as share of sales (latest annual)"
    else:
        base = _catalogue_text()[field]["gloss"]
    direction = DIRECTION_BY_METRIC.get(field)
    if direction == "higher_better":
        return f"{base}. Higher is better."
    if direction == "lower_better":
        return f"{base}. Lower is better."
    return base


def _present_metric_renderings(
    row: Mapping[str, Any], ctype: str, currency: str | None
) -> dict[str, str]:
    """label -> rendered display string, for every PRESENT per-type metric, keyed by the SAME
    label text the model is shown (never the internal field name, which the model never sees).

    Shared by build_read_messages (the facts block the model reads) and
    validate_read_metrics (the hallucination guard) so the two can never disagree about what
    "as shown" means for a given label -- one renderer, two callers.
    """
    out: dict[str, str] = {}
    for field in INPUT_FIELDS_BY_TYPE[ctype]:
        value = row.get(field)
        if _is_missing(value):
            continue
        brief = READ_METRIC_BRIEF[field]
        out[read_metric_label(field, row)] = _format_metric_value(value, brief["fmt"], currency)
    return out


_BAND_WORDS = {"good": "good", "ok": "ok", "weak": "weak", "unknown": "not judged"}


def verdict_why_lines(row: Mapping[str, Any]) -> list[str]:
    """How the rules reached the verdict, in plain lines for the read: one line per judged metric
    (label as in the numbers list, band word, and the note when one applied: a guard, the
    current-ratio relief, or no cash burn shown), the falling top
    line when it is, and one closing line. No thresholds. Built from `evaluate_verdict`, the same
    computation that decides the color."""
    evaluation = evaluate_verdict(row)
    lines: list[str] = []
    for axis in evaluation.axes:
        if _is_missing(row.get(axis.field)) and not axis.note:
            continue
        note = f" ({axis.note})" if axis.note else ""
        lines.append(f"- {read_metric_label(axis.field, row)}: {_BAND_WORDS[axis.band]}{note}")
    if evaluation.shrinking:
        lines.append(f"- {read_metric_label('revenue_growth_yoy_pct', row)}: falling")
    bands = {a.field: a.band for a in evaluation.axes}

    def name(field: str) -> str:
        band = 'falling' if field == "revenue_growth_yoy_pct" else _BAND_WORDS[bands[field]]
        return f"{read_metric_label(field, row)} ({band})"

    if evaluation.verdict == VERDICT_RED:
        lines.append("Placed at the bottom because of: " + ", ".join(name(f) for f in evaluation.red_because) + ".")
    elif evaluation.verdict == VERDICT_YELLOW:
        lines.append("Held back from the top by: " + ", ".join(name(f) for f in evaluation.held_back_by) + ".")
    else:
        lines.append(
            "Every core figure is good, so nothing held it back."
            if normalize_company_type(row.get("company_type")) == "pre_revenue"
            else "Every core figure is good, no supporting figure is weak and no falling revenue is shown, so nothing held it back."
        )
    return lines


def build_read_messages(row: Mapping[str, Any], verdict: str) -> tuple[str, str]:
    """Pure: build the (system, user) messages for the Claude Haiku prose read.

    The user message states the company type, the verdict + its plain meaning, and
    one line per PRESENT per-type metric (the same INPUT_FIELDS_BY_TYPE set the hash
    covers). Missing metrics are omitted - never guessed. No I/O, no anthropic import.
    """
    ctype = normalize_company_type(row.get("company_type"))
    # This line is the ONLY route by which the currency reaches the model on operating and
    # financial cards: every field on those types is pct or ratio, so _format_metric_value
    # never renders a currency for them. Delete it and the model has none, and invents one.
    currency = row.get("currency")
    if _is_missing(currency):
        currency = None
    renderings = _present_metric_renderings(row, ctype, currency)
    labels_to_fields = {read_metric_label(f, row): f for f in INPUT_FIELDS_BY_TYPE[ctype]}
    lines = []
    for label, rendered in renderings.items():
        field = labels_to_fields[label]
        entry = f"- {label}: {rendered}\n  Meaning: {read_metric_meaning(field, row)}"
        limit = _catalogue_text()[field]["applicability"].strip()
        if limit:
            entry += f"\n  Limit: {limit}"
        lines.append(entry)
    facts = "\n".join(lines) if lines else "- (no metric values available)"
    why = "\n".join(verdict_why_lines(row))
    meaning = VERDICT_MEANING.get(verdict, verdict)
    display_currency = _display_currency(currency)
    currency_line = f"Currency this company trades in: {display_currency}\n" if display_currency else ""
    user = (
        f"Company type: {ctype}\n"
        f"{currency_line}"
        f"Health verdict: {meaning} (for your verdict_meaning field only; never write it in the read)\n\n"
        f"Numbers for this company:\n{facts}\n\n"
        "Why lines (how the rules reached the verdict; explain only with these; never state the verdict itself):\n"
        f"{why}\n\n"
        "Write the 2-3 sentence read."
    )
    return READ_SYSTEM_PROMPT, user


def validate_read_metrics(row: Mapping[str, Any], referenced_metrics: list[Any]) -> bool:
    """True iff every {"label", "value_as_shown"} pair in referenced_metrics matches this row's
    OWN rendering of that label, exactly as build_read_messages showed it to the model.

    An empty list is valid -- a read may legitimately discuss the verdict without citing a
    specific number. An unknown label, a missing key, or a mismatched value fails closed
    (returns False): the model either cited something it wasn't given, or misquoted a number it
    was. Either way the read is not trustworthy as written. No tolerance/rounding logic here --
    both sides use the identical renderer, so a genuine citation matches character for character.
    """
    ctype = normalize_company_type(row.get("company_type"))
    currency = row.get("currency")
    if _is_missing(currency):
        currency = None
    renderings = _present_metric_renderings(row, ctype, currency)
    for entry in referenced_metrics:
        if not isinstance(entry, Mapping):
            return False
        label = entry.get("label")
        claimed = entry.get("value_as_shown")
        if label not in renderings or claimed != renderings[label]:
            return False
    return True


# --- Slice 5b: deterministic style/rule guard (subset of READ_SYSTEM_PROMPT, no LLM judge) ----
# Complements validate_read_metrics (the numeric hallucination guard) with a SEPARATE guard over
# STYLE: a deliberately partial subset of READ_SYSTEM_PROMPT's own rules that a plain string/regex
# check can enforce without semantic judgment. Rules needing real language understanding -- the
# currency-phrasing paragraph (needs per-card context about which currency is expected), "don't
# blame the verdict on positive growth" (needs causal-attribution understanding, not just keyword
# proximity), "2-3 sentences" (stated in the intro, not a bulleted Rule, and sentence-splitting
# next to "24.0%"-style decimals is its own hazard), and three-item-list-used-for-rhythm detection
# (the "for rhythm" part is a judgment about INTENT, not structure) -- are NOT checked here and
# stay covered only by the prompt itself, exactly as before this guard existed. A miss on one of
# those is not a regression: it is the same status quo every rule below did not previously change.
#
# Every check below is a presence/absence check over the read's own text, nothing else -- no
# access to the row, the verdict, or any other card context, so a violation can never depend on
# information the read itself does not contain.

_EM_DASH = "—"
_EN_DASH = "–"

# Emoji ranges only -- NOT "any non-ASCII character", which would misfire on this app's own
# currency symbols (GBP/JPY/EUR signs) and a degree sign. The four ranges below cover the large
# majority of emoji actually in use (faces, hands, hearts, animals, food, activity, travel,
# objects, the misc-symbols/dingbats/star block, and flag letters) without reaching into Latin-1
# Supplement or the Currency Symbols block, both far outside these ranges. Not exhaustive of every
# emoji-capable code point in Unicode -- a miss there has the same "covered only by the prompt
# itself" status as the excluded semantic rules above, not a false claim of completeness.
_EMOJI_RE = re.compile(
    "["
    "\U0001F300-\U0001FAFF"  # pictographs, emoticons, transport/map, supplemental symbols, extended-A
    "\U00002600-\U000027BF"  # misc symbols + dingbats
    "\U00002B00-\U00002BFF"  # misc symbols and arrows (e.g. star)
    "\U0001F1E6-\U0001F1FF"  # regional indicator letters (flag emoji)
    "\U0000FE0F"  # variation selector-16 (emoji presentation)
    "]"
)

# A "same sentence" gap that does NOT treat a decimal point as a sentence boundary -- cto-
# reviewer's round-2 finding: a plain `[^.!?]` character class (or `re.split(r"[.!?]+", ...)`)
# breaks on the "." inside every percentage this app renders (f"{v:.1f}%", always one decimal),
# so a real violation with a figure sitting between its two halves (e.g. "not just a 24.0%
# margin story, but a debt story too") was silently missed -- the read/write mirror of the exact
# hazard already named elsewhere in this file for why "2-3 sentences" isn't checked at all.
# Matches any non-terminator character, OR a "." specifically sandwiched between two digits (a
# decimal point, not a sentence end).
_SENTENCE_GAP = r"(?:[^.!?]|(?<=\d)\.(?=\d))"

# Word-boundary matches so "buyback", "seller", "sales" never trip these -- none of those are
# the banned action. "buy"/"sell"/"price" have no legitimate non-advice use in this app's own
# vocabulary: the prompt bars these words from a read, so a read has no need to discuss the company buying or
# selling something else, and no card
# metric carries a share price any more (every price-carrying metric was dropped from the
# catalogue -- see the module docstring). A bare "price" match also catches "target price"/
# "share price", not only one worked phrasing. These stay bare-word matches, unlike the group
# below.
_ADVICE_ACTION_RE = re.compile(
    r"\b(?:buy|buys|buying|sell|sells|selling|price)\b",
    re.IGNORECASE,
)

# "cheap", "expensive", "worth it", "hold", and "avoid" are deliberately NOT bare-word matches:
# each has an ordinary, non-advice use this app's own vocabulary invites -- "expensive to
# service" (a debt/financing cost), "cheap financing", "strong reserves help it hold steady", "a
# large cash cushion helps it avoid a shortfall" all describe the company's own finances, not a
# recommendation, and none is a rule violation (cto-reviewer's round-1 finding: a bare
# "expensive" match rejected a legitimate leverage-cost explanation -- fixed by anchoring it the
# same way hold/avoid already were, rather than leaving it as the one unanchored exception).
# Anchoring to "share(s)"/"stock(s)" within the same clause keeps every one of these aimed at the
# literal banned claim about the SHARE ("the share is cheap", "avoid the share", "hold the
# stock") instead of the ordinary English word. This trades recall for precision: a violation
# phrased without "share"/"stock" nearby (e.g. "best to hold for now") is not caught here and
# stays covered only by the prompt itself, same as the excluded semantic rules above.
#
# "share"/"shares" excludes two further, real collisions (cto-reviewer's round-2 finding,
# confirmed against actual prompt-encouraged vocabulary): "share OF X" is a portion, not the
# security -- the catalogue's margin gloss says "Operating profit as share of sales", and
# the existing _CLEAN_READ fixture already uses "a solid share of every sale" -- so "share"
# immediately followed by "of" is excluded. "MARKET share" is a similar, unrelated business
# term (a portion of a market) -- excluded via a lookbehind. Neither exclusion touches "stock":
# no card metric describes inventory/stock-levels, so no equivalent collision is known to exist
# there, and adding an unproven exclusion would be guessing at a problem, not fixing one.
#
# The two exclusions are nested INSIDE the share/shares branch specifically (cto-reviewer's
# round-3 finding): an earlier version put `(?<!market )`/`(?!\s+of\b)` OUTSIDE the whole
# `(?:share|shares|stock|stocks)` alternation, so they silently applied to "stock"/"stocks" too
# -- directly contradicting this comment's own claim and regressing round 1's correct behavior
# ("hold/avoid the stock of X" went from caught to silently missed). Zero test coverage of
# "stock" as the anchor noun let this survive two review rounds; both branches now have their
# own dedicated tests.
_ADVICE_VALUE_SHARE_RE = re.compile(
    rf"\b(?:cheap|expensive|worth it|hold|holding|avoid|avoiding)\b{_SENTENCE_GAP}{{0,25}}"
    r"\b(?:(?<!market )(?:share|shares)\b(?!\s+of\b)|(?:stock|stocks)\b)",
    re.IGNORECASE,
)

# Straight or curly apostrophe -- Haiku may emit either; a straight-quote-only literal would
# silently miss the curly form.
_APOSTROPHE = "['’]"
_WORTH_NOTING_RE = re.compile(rf"\bit{_APOSTROPHE}s worth noting\b", re.IGNORECASE)
_IMPORTANT_REMEMBER_RE = re.compile(rf"\bit{_APOSTROPHE}s important to remember\b", re.IGNORECASE)
# "but" must appear in the SAME sentence as "not just" (_SENTENCE_GAP* stops at a real sentence
# boundary, not just anywhere later in the read, but tolerates a decimal figure in between --
# cto-reviewer's round-1 finding: the original two-part check, search the whole rest of the
# string for "but" with no bound, misfired on a read using "not just X" in one sentence and an
# ordinary, unrelated contrastive "but" in a later one, e.g. a yellow-verdict card contrasting a
# weak axis against a strong one). Word-boundary on "but" so "about"/"contributes" never count.
_NOT_JUST_BUT_RE = re.compile(rf"\bnot just\b{_SENTENCE_GAP}*\bbut\b", re.IGNORECASE)

# Scoped to the SAME sentence as a growth word (growth/grew/grown/growing), in either order --
# cto-reviewer's round-1 finding: the original bare phrase match fired on "this year"/"over the
# year" describing anything (e.g. free cash flow), not just growth, contradicting the prompt's
# own narrower rule ("do not write 'this year'... about it", where "it" = growth specifically).
# Checked per-sentence (see find_read_style_violations) rather than a single proximity-bounded
# regex, since the growth word can legitimately come before OR after the period phrase ("this
# year, revenue grew" vs "revenue grew this year").
_GROWTH_WORD_RE = re.compile(r"\b(?:growth|grew|grown|growing)\b", re.IGNORECASE)
_GROWTH_PERIOD_RE = re.compile(r"\b(?:this year|over the year)\b", re.IGNORECASE)

# Splits on a real sentence terminator only -- NOT the "." inside a decimal figure -- cto-
# reviewer's round-2 finding: the original `re.split(r"[.!?]+", read)` also split on the "."
# inside every percentage this app renders (f"{v:.1f}%", always one decimal), so a sentence with
# a figure sitting between its growth word and period phrase (e.g. "Revenue grew 24.0% this
# year") was silently cut into two fragments, neither containing both patterns, and the real
# violation was missed. `!`/`?` never appear inside a number, so they still split
# unconditionally.
#
# A period is a decimal point only when digits sit on BOTH sides ("1.50"); it is a real sentence
# end whenever EITHER side is not a digit -- an OR of the two negations, not an AND (cto-
# reviewer's round-3 finding: an earlier version wrote `(?<!\d)\.(?!\d)`, requiring BOTH sides
# digit-free, which wrongly treats a whole-number-then-period as non-terminal, e.g. "...ratio of
# 1.50. This year..." or "...$400. This year..." -- both real shapes this app's own metric/money
# formatters produce -- silently merged two unrelated sentences into one fragment, causing a
# FALSE positive on the growth-period check). `(?<!\d)\.|\.(?!\d)` is that OR, expressed as
# alternation since a single lookaround assertion can't express it directly.
_SENTENCE_BOUNDARY_RE = re.compile(r"(?<!\d)\.|\.(?!\d)|[!?]+")

def find_read_style_violations(read: str) -> list[str]:
    """Deterministic, code-checkable SUBSET of READ_SYSTEM_PROMPT's own rules -- a style/rule
    guard over the read TEXT ALONE, not a hallucination guard (that is validate_read_metrics)
    and not the verdict-meaning guard (that is verdict_meaning_violation, below -- it needs the
    verdict color and the model's own structured self-report, not just this text, so it can't
    live here). Returns one human-readable description per violated rule found; an empty list
    means none of the checks below fired (NOT a claim that the read is fully prompt-compliant --
    only that this specific, deliberately partial subset passed).

    Checks every rule independently and collects every violation found, rather than stopping at
    the first, so the caller can report all of them at once.
    """
    violations: list[str] = []

    if _EM_DASH in read or _EN_DASH in read:
        found = [name for ch, name in ((_EM_DASH, "em dash"), (_EN_DASH, "en dash")) if ch in read]
        violations.append(f"{' and '.join(found)} used as punctuation (rule: no em dash or en dash)")

    if "!" in read:
        violations.append("exclamation mark used (rule: no exclamation marks)")

    if _EMOJI_RE.search(read):
        violations.append("emoji character used (rule: no emoji)")

    m = _ADVICE_ACTION_RE.search(read)
    if m:
        violations.append(
            f'investment-advice language used: "{m.group(0)}" '
            "(rule: never say buy/sell, or predict the price)"
        )

    m = _ADVICE_VALUE_SHARE_RE.search(read)
    if m:
        violations.append(
            f'investment-advice phrase used: "{m.group(0)}" '
            "(rule: never say the share is cheap/expensive/worth it, or to hold or avoid it)"
        )

    if _NOT_JUST_BUT_RE.search(read):
        violations.append('"not just X, but Y" construction used (rule: avoid the usual AI tells)')

    if _WORTH_NOTING_RE.search(read):
        violations.append("\"it's worth noting\" used (rule: avoid the usual AI tells)")

    if _IMPORTANT_REMEMBER_RE.search(read):
        violations.append("\"it's important to remember\" used (rule: avoid the usual AI tells)")

    for sentence in _SENTENCE_BOUNDARY_RE.split(read):
        if _GROWTH_PERIOD_RE.search(sentence) and _GROWTH_WORD_RE.search(sentence):
            violations.append(
                '"this year" or "over the year" used about growth '
                "(rule: revenue growth is one quarter's change, never a full year's)"
            )
            break

    return violations


# --- Figure, length and wording check (the rules of READ_SYSTEM_PROMPT that code can verify) ----
# Like find_read_style_violations it rejects the whole read; unlike it, it needs the card's own
# rendered figures, so it takes the row. Every sentence of a read must state one of the card's
# figures as shown, so a read with a closing verdict sentence that cites no figure, or any
# sentence that talks about the company instead of a number, is rejected whole.

READ_MAX_WORDS = 25

# A sentence with no figure is allowed only when it states a limit the prompt requires: the
# financial-company limit, or a measure that could not be worked out.
_LIMIT_SENTENCE_RE = re.compile(r"balance-sheet|capital strength|could not be worked out", re.IGNORECASE)

_NUMBER_WORDS = "one|two|three|four|five|six|seven|eight|nine|ten"
_FRACTION_WORDS_RE = re.compile(
    r"\b(?:thirds|fifths|tenths|halves)\b"
    r"|\b(?:a|one)[\s-]+(?:third|fifth|tenth|half)\b(?!\s*-?\s*(?:party|quarter|year|time))"
    r"|(?<!first[ -])(?<!second[ -])(?<!last[ -])(?<!latter[ -])\bhalf\s+(?:of|the)\b"
    r"|\b(?:a|one)[\s-]+quarter\s+of\b|\bthree[\s-]+quarters\b"
    rf"|\b(?:{_NUMBER_WORDS})\s+(?:in|out\s+of)\s+(?:two|three|four|five|six|seven|eight|nine|ten)\b",
    re.IGNORECASE,
)

_CAUSE_MARKER_RE = re.compile(
    r"\b(?:to fund|to finance|in order to|because|thanks to|driven by|ability to|so it can|allowing it)\b",
    re.IGNORECASE,
)

# A symbol or code is fine with an amount right after it ("$2.1B", "CHF 2.1B") or right before it
# ("100 SEK", "100 \u20ac"): the margin rule asks for "per 100 units" of a bare-code currency.
_CURRENCY_NO_AMOUNT_RE = re.compile(
    r"(?<!\d)(?<!\d\s)(?:(?:[AC]\$|(?<![AC])\$|[\u00a3\u00a5\u20ac])(?!\s*\d)"
    r"|\b(?:USD|GBP|EUR|JPY|AUD|CAD|CHF|SEK|DKK|NOK)\b(?!\s*\d))"
)


def _read_sentences(read: str) -> list[str]:
    parts = re.split(r"\n+", read.strip())
    sentences = [p for part in parts for p in _SENTENCE_BOUNDARY_RE.split(part)]
    return [s.strip() for s in sentences if s.strip()]


def _figure_pattern(rendered: str) -> re.Pattern[str]:
    # Digit boundaries so "5.6%" never matches inside "15.6%" or "5.65%"; a leading minus is
    # ignored because a read may say "a loss of 12.0%" for "-12.0%".
    return re.compile(r"(?<![\d.])" + re.escape(rendered.lstrip("-")) + r"(?!\d)")


def find_read_figure_violations(row: Mapping[str, Any], read: str) -> list[str]:
    """Deterministic checks of the read against THIS card's figures and the prompt's wording
    rules. One description per violated rule; an empty list means none fired, not that the read
    is fully prompt-compliant (active voice, one word per meaning and one topic per sentence
    stay in the prompt only)."""
    ctype = normalize_company_type(row.get("company_type"))
    currency = row.get("currency")
    if _is_missing(currency):
        currency = None
    patterns = [_figure_pattern(r) for r in _present_metric_renderings(row, ctype, currency).values()]
    violations: list[str] = []

    no_figure = [
        s for s in _read_sentences(read)
        if not any(p.search(s) for p in patterns) and not _LIMIT_SENTENCE_RE.search(s)
    ] if patterns else []
    if no_figure:
        violations.append(
            f'sentence with none of the card\'s figures: "{no_figure[0]}" '
            "(rule: every sentence states one of the numbers, exactly as shown)"
        )

    too_long = [s for s in _read_sentences(read) if len(s.split()) > READ_MAX_WORDS]
    if too_long:
        violations.append(
            f"sentence of {len(too_long[0].split())} words (rule: at most {READ_MAX_WORDS} words)"
        )

    m = _FRACTION_WORDS_RE.search(read)
    if m:
        violations.append(f'number written in words: "{m.group(0)}" (rule: write every number in digits)')

    m = _CAUSE_MARKER_RE.search(read)
    if m:
        violations.append(
            f'purpose or cause wording: "{m.group(0)}" '
            "(rule: never say why the company has a number or what it can do)"
        )

    m = _CURRENCY_NO_AMOUNT_RE.search(read)
    if m:
        violations.append(f'currency "{m.group(0)}" without an amount (rule: no currency symbol or code alone)')

    return violations


def verdict_meaning_violation(verdict: str, read: str, reported_meaning: str) -> str | None:
    """Confirms the model's hidden classification matches the verdict the rules already decided.

    The model reports its own overall reading as a separate enum-constrained tool field
    (verdict_meaning, forced by READ_TOOL_SCHEMA to "healthy"/"mixed"/"fragile"), which the
    reader never sees. It must equal the verdict this row's rules ALREADY decided -- never the
    model's own call -- which catches a self-report that disagrees with the verdict. `read`
    is not inspected: that the text neither states nor contradicts the verdict is instructed by
    the prompt only.

    A read that fails is dropped and the card shows the fixed one-line verdict meaning instead.
    Returns a description of the violation, or None if the read has none.
    """
    expected = VERDICT_MEANING_WORD.get(verdict)
    if reported_meaning != expected:
        return (
            f'reported verdict_meaning "{reported_meaning}" does not match the verdict '
            f'"{verdict}" (expected "{expected}")'
        )
    return None
