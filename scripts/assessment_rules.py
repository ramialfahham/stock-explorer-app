"""Deterministic per-type financial-health verdict + regeneration hash (Slice 5a).

Pure, no I/O. The verdict COLOR is decided here by transparent rules, never by the
LLM (5b writes only the prose read). The verdict measures **financial health /
resilience** from the card's own numbers, and it is **not** investment advice. Growth was
excluded from the verdict and now enters ONE-SIDED: a shrinking top line blocks green, while
growth never earns green and never causes red (see the policy comment below). Valuation used
to be excluded too; there is no valuation metric left to exclude, since every price-carrying
metric was dropped from the catalogue.

`INPUT_FIELDS_BY_TYPE` / `DIRECTION_BY_METRIC` mirror `dbt_analytics/seeds/metric_catalogue.csv`
(`applies_to` / `direction`), the same metric set 5b hashes and prompts over, so
"regenerate the read iff a prompt input changed" holds by construction. A
`tests/tooling` guard asserts this mirror stays in sync with the seed. The hash covers one
thing beyond that set, the display currency, because the prompt names it and the read quotes
it; see `compute_input_hash`.
"""

from __future__ import annotations

import hashlib
import json
import math
from collections.abc import Mapping
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
# "Eligible", not "guaranteed". A card whose Haiku call fails is counted and skipped without
# ai_read being set, while the record still carries the new hash into the upsert, so the next
# run's regenerate test (hash differs OR ai_read empty) can skip it and leave prose written
# under an older prompt in place. Whether the old text survives or is nulled depends on how
# PostgREST treats a batch whose rows have different keys, which nothing here pins and which
# has not been verified. Worth checking before any run that regenerates the whole deck.
INPUT_HASH_VERSION = "5a.4"

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
# positive percentage" over negative equity. Filed as Gemini feedback point 1 and its sibling-bug
# note (docs/backlog/gemini_verdict_feedback.md). statement_roe_pct's guard is used from BOTH
# _verdict_operating and _verdict_financial, not operating only.
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
# _verdict_operating (every core axis must be "good" for green), so it is fixed by treating it as
# "unknown" -- the same neutral treatment every other axis already gets for a missing value.
# debt_to_equity is a SUPPORTING axis, which never needs to be "good" to reach green -- only
# "weak" changes anything, since supporting axes can block green but never rescue it. Relabeling
# negative equity "unknown" there would have been a no-op on every card's actual color, which is
# not a fix. So it is banded "weak" instead, capping the card at yellow, the same ceiling every
# other weak supporting axis already has, never forcing red on its own. Negative equity is not
# always distress on its own (it can come from a healthy company's own buybacks, per the
# catalogue's own applicability note) -- "weak" is deliberately the mildest band that still
# changes anything, a caution rather than a verdict on the cause. statement_roe_pct gets the same
# "weak" treatment in _verdict_operating (same supporting role as debt_to_equity), but "unknown"
# in _verdict_financial, where it is effectively a CORE axis -- see the comment above
# _verdict_financial for why that function's population makes "unknown" the honest choice rather
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
# Gemini feedback points 6/8 (docs/backlog/gemini_verdict_feedback.md): current_ratio_stmt and
# fcf_margin_pct were graded fully independently, so a company with excellent free cash flow but
# a merely-weak current ratio was capped at yellow regardless -- Apple's real card (current ratio
# 0.89, FCF margin 23.7%) is exactly this case.
#
# First version of this relief gated on fcf_margin_pct banding "good" (FCF / revenue). A review
# caught that this is a mismatched comparison: fcf_margin_pct is scaled by REVENUE, not by the
# SIZE of the liquidity gap, so it only happens to work for Apple because Apple's revenue and
# current-liability scale roughly track each other. A company with modest revenue but a large
# near-term debt-maturity wall sitting in current liabilities could clear a "good" FCF margin
# while its actual free cash flow covers only a small fraction of the real shortfall -- exactly
# the case this relief exists to NOT wave through.
#
# Corrected to a direct dollar comparison instead: does free cash flow actually cover the
# working-capital shortfall (current_liabilities - current_assets, i.e. -working_capital when
# working_capital is negative)? This still relieves Apple (whose free cash flow is a large
# multiple of its comparatively small shortfall) and correctly withholds relief from a company
# whose cash generation can't plug the hole, regardless of how the ratio compares to revenue.
CURRENT_RATIO_WEAK_TH = 1.0
CURRENT_RATIO_GOOD_TH = 1.5

# Owner-decided floor (2026-09-01): below this, current liabilities are more than double current
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


def _verdict_operating(row: Mapping[str, Any]) -> str:
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
        return VERDICT_RED
    if (
        all(b == "good" for b in core)
        and not any(b == "weak" for b in supporting)
        and not _is_shrinking(row)
    ):
        return VERDICT_GREEN
    return VERDICT_YELLOW


def _verdict_financial(row: Mapping[str, Any]) -> str:
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
        return VERDICT_RED
    if (
        roe == "good"
        and margin == "good"
        and roa in ("good", "unknown")
        and not _is_shrinking(row)
    ):
        return VERDICT_GREEN
    return VERDICT_YELLOW


def _verdict_pre_revenue(row: Mapping[str, Any]) -> str:
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
    # Flagged to the owner rather than absorbed silently -- see .claude/task/contract.md.
    net_cash = _axis(row, "net_cash", weak_th=0.0, good_th=0.0)
    working_capital = _axis(row, "working_capital", weak_th=0.0, good_th=0.0)
    if runway == "weak" or net_cash == "weak" or working_capital == "weak":
        return VERDICT_RED
    if runway == "good" and net_cash == "good" and working_capital == "good":
        return VERDICT_GREEN
    return VERDICT_YELLOW


_VERDICT_FN = {
    "operating": _verdict_operating,
    "financial": _verdict_financial,
    "pre_revenue": _verdict_pre_revenue,
}


def normalize_company_type(company_type: Any) -> str:
    """Resolve to one of COMPANY_TYPES; null/unknown -> operating (mirrors the frontend)."""
    if company_type in COMPANY_TYPES:
        return str(company_type)
    return "operating"


def compute_verdict(row: Mapping[str, Any]) -> str:
    """Deterministic health verdict for a card row. Total: always returns a VERDICTS member."""
    ctype = normalize_company_type(row.get("company_type"))
    return _VERDICT_FN[ctype](row)


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
    display currency + version.

    5b regenerates the prose read only when this hash changes. Numbers only, plus the
    currency: name/sector are context, not signals ("reason only from the given numbers"),
    but the currency is named in the prompt and the read quotes it, so a card whose currency
    is corrected upstream must regenerate rather than keep prose naming the old one. Hashed
    through `_display_currency` so a GBp/GBP change, which the card face never shows, does
    not churn every FTSE read for nothing.
    """
    ctype = normalize_company_type(row.get("company_type"))
    payload = {
        "version": version,
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
# reason only from the given numbers; end on the verdict's meaning as financial
# health/fragility "on these figures", never as a buy/sell.
READ_SYSTEM_PROMPT = """You write a short, plain-language "read" of a company's financial health for a complete beginner using a stock-learning app. You are given the company type, a set of already-computed numbers, and a health verdict (green, yellow, or red) that fixed rules decided - not you. In 2-3 sentences, explain what those numbers say about the company's financial health, ending on what the verdict means in plain words.

Rules:
- Educational only. Never give investment advice. Do not say or imply whether to buy, sell, hold, or avoid the share, whether it is cheap, expensive, or "worth it", and never predict the price. You explain what the numbers describe; you never recommend an action.
- Write for someone who knows no finance vocabulary. If you use a term, gloss it in plain words or an everyday comparison. Leave no jargon unexplained.
- Reason only from the numbers given. Do not invent or assume anything about the company's products, industry, news, management, or history, and bring in no outside facts. If a number is missing, don't mention it - never guess.
- Money amounts already carry their own currency symbol or code - use it exactly as given; never assume, add, or convert to a different currency (these companies report in different currencies).
- A margin is a percentage, not money. Explaining one as the amount kept out of every unit of revenue is good teaching and is encouraged, but it must use the currency given on the "Currency this company trades in" line below and no other, whichever currency that turns out to be. Where that currency has no everyday small unit, say it per 100 units of that same currency instead. If there is no such line, describe the margin as a percentage or a share and do not phrase it per unit of money at all. Never mix two currencies in one explanation. A margin is per unit of revenue, never per item sold: you are not told how many units the company sells and must never imply profit per item.
- Returns and growth are NOT amounts per unit of revenue, so never phrase them that way. Return on equity is profit measured against the owners' money, and return on assets is profit measured against everything the company owns. Revenue growth compares the latest reported quarter with the same quarter a year earlier, so it is one quarter's change, never a full year's: do not write "this year" or "over the year" about it.
- Interpret, don't list. Pull out the one or two things that most shape the financial picture and say what they mean; don't recite every number back.
- Falling revenue counts against a company here and can stop it being called healthy. Rising revenue does not make a company healthy, and is never a reason to buy. When growth is positive, never give it as the reason the verdict is not green, because the rules only ever count a fall. Describing a nearly flat top line accurately is fine; blaming the verdict on it is not.
- End on the verdict's meaning, phrased as health or fragility on these figures - e.g. "financially healthy on these figures", "a mixed financial picture on these numbers", "financially fragile on these figures". Never phrase it as a good or bad buy.
- No dashes as punctuation. Never use an em dash or en dash. Use a comma, a full stop, or brackets instead. Hyphens inside ordinary compound words are fine.
- Write like a person explaining this to someone they know, not like a model. Avoid the usual tells: no "not just X, but Y", no "it's worth noting" or "it's important to remember", no rhetorical questions, no three-item lists used for rhythm, no sentence that hedges and then pivots for the sake of sounding balanced. Vary your sentence lengths. Say the thing and stop. Plain is not the same as chatty, so stay calm and factual. This rule is about STYLE only: it never overrides the rules above or the company-type lens below. Where one of those requires a limit to be stated - above all the financial-company limit that these numbers cannot judge balance-sheet safety or capital strength - state it plainly and in full. A required caveat is never a tell to be trimmed.
- Calm, clear, honest. No hype, no emoji, no exclamation marks.

Company-type lens:
- operating: profitability (does it earn on sales?), leverage (how much it has borrowed), cash generation.
- financial: profitability and returns (margin, return on equity, return on assets). State the honest limit: this shows profitability only - it can't judge this financial company's balance-sheet safety or capital strength, which these numbers don't show.
- pre_revenue: a survival story - not profitable yet, so focus on cash, how fast it is spending (burn), and how long the cash lasts (runway). Health = staying power, not profit."""


# Plain-English meaning of each verdict token, given to the model so the read can
# land on it. Mirrors the frontend token -> emoji mapping added in Slice 6.
VERDICT_MEANING: dict[str, str] = {
    VERDICT_GREEN: "green - financially healthy on these figures",
    VERDICT_YELLOW: "yellow - a mixed financial picture on these figures",
    VERDICT_RED: "red - financially fragile on these figures",
}


# Per-metric beginner brief for the facts block: label + one plain gloss + a value
# format. Keys MUST cover every field in INPUT_FIELDS_BY_TYPE (a tests/tooling guard
# asserts it). Wording is drawn from dbt_analytics/seeds/metric_catalogue.csv;
# the growth line states which way growth counts, so the read never turns it into a buy
# cue. (Owner-signed §6, alongside READ_SYSTEM_PROMPT.)
READ_METRIC_BRIEF: dict[str, dict[str, str]] = {
    "ebit_margin_pct": {
        "label": "Operating margin",
        "fmt": "pct",
        "gloss": "share of sales kept as operating profit (higher = more profitable); can look extreme when revenue is very small",
    },
    "revenue_growth_yoy_pct": {
        "label": "Revenue growth vs a year ago",
        "fmt": "pct",
        "gloss": "how fast the top line is growing; for a financial company that is net interest plus fees, not sales. A fall counts against the verdict, a rise does not count for it. A very big percentage either way can just mean an unusual prior year rather than real change",
    },
    "net_debt_to_ebitda": {
        "label": "Net debt / EBITDA",
        "fmt": "ratio",
        "gloss": "roughly how many years of earnings would clear net debt (lower = less borrowing); can explode to a huge or distorted number when earnings are near zero",
    },
    "fcf_margin_pct": {
        "label": "Free cash flow margin",
        "fmt": "pct",
        "gloss": "share of sales kept as real cash (higher = stronger); negative = burning cash; can look extreme when revenue is very small",
    },
    "debt_to_equity": {
        "label": "Debt / equity",
        "fmt": "ratio",
        "gloss": "borrowed money versus the owners' stake (lower = more cushion; distorted or meaningless if equity is thin or negative)",
    },
    "current_ratio_stmt": {
        "label": "Current ratio",
        "fmt": "ratio",
        "gloss": "short-term assets versus short-term bills (above 1 = covers near-term bills); a very high ratio isn't automatically good either - it can mean cash sitting idle",
    },
    "statement_roe_pct": {
        "label": "Return on equity",
        "fmt": "pct",
        "gloss": "profit earned on the owners' money (higher = more efficient; can look spuriously positive if equity is negative)",
    },
    "net_margin_pct": {
        "label": "Net margin",
        "fmt": "pct",
        "gloss": "share of revenue kept as final profit after all costs (higher = more profitable); for a financial company \"revenue\" means net interest plus fees, not sales",
    },
    "roa_pct": {
        "label": "Return on assets",
        "fmt": "pct",
        "gloss": "profit earned on everything the company owns (higher = more efficient)",
    },
    "net_cash": {
        "label": "Net cash",
        "fmt": "currency",
        "gloss": "cash and equivalents minus borrowings, a money amount (positive = more cash than borrowings). Not every obligation, and the cash figure excludes short-term investments; a big number is only a long cushion if the burn is slow",
    },
    "working_capital": {
        "label": "Working capital",
        "fmt": "currency",
        "gloss": "short-term assets minus short-term bills, a money amount (positive = a near-term cushion, negative = a squeeze)",
    },
    "cash_runway_months": {
        "label": "Cash runway",
        "fmt": "months",
        "gloss": "how long the cash lasts at the current spend (higher = more time before needing to raise money)",
    },
    "burn_rate_monthly": {
        "label": "Cash burn per month",
        "fmt": "currency",
        "gloss": "how fast cash is going out each month, a money amount (lower = the cash lasts longer)",
    },
}


# Currency symbols for the money-amount metrics; mirrors frontend/card_copy.py so the
# read names the SAME currency the card face shows. Unknown code -> the code itself
# (never a fake symbol). The app spans nine markets across six currencies, so "$" is not a safe
# default. The owner's rule (2026-08-28) is to use whatever form that currency takes in real
# practice. CHF has no entry and renders as "CHF", which IS the practical form, so it stays.
# When those markets land: CAD gets "C$", following AUD; SEK, DKK and NOK stay bare ISO codes,
# because "kr" names three different currencies and this app shows markets side by side.
_CURRENCY_SYMBOLS = {"USD": "$", "GBP": "£", "JPY": "¥", "EUR": "€", "AUD": "A$"}


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
    if fmt == "months":
        return f"{v:.0f} months"
    if fmt == "currency":
        return _compact_amount(v, currency)
    return f"{v:.2f}"  # ratio


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
    lines: list[str] = []
    for field in INPUT_FIELDS_BY_TYPE[ctype]:
        value = row.get(field)
        if _is_missing(value):
            continue
        brief = READ_METRIC_BRIEF[field]
        rendered = _format_metric_value(value, brief["fmt"], currency)
        lines.append(f"- {brief['label']}: {rendered} - {brief['gloss']}")
    facts = "\n".join(lines) if lines else "- (no metric values available)"
    meaning = VERDICT_MEANING.get(verdict, verdict)
    display_currency = _display_currency(currency)
    currency_line = f"Currency this company trades in: {display_currency}\n" if display_currency else ""
    user = (
        f"Company type: {ctype}\n"
        f"{currency_line}"
        f"Health verdict: {meaning}\n\n"
        f"Numbers for this company:\n{facts}\n\n"
        "Write the 2-3 sentence read."
    )
    return READ_SYSTEM_PROMPT, user
