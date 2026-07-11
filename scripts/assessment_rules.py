"""Deterministic per-type financial-health verdict + regeneration hash (Slice 5a).

Pure, no I/O. The verdict COLOR is decided here by transparent rules — never by the
LLM (5b writes only the prose read). The verdict measures **financial health /
resilience** from the card's own numbers; it deliberately excludes valuation (P/E,
P/TBV) and growth, and it is **not** investment advice.

`INPUT_FIELDS_BY_TYPE` / `DIRECTION_BY_METRIC` mirror `dbt_analytics/seeds/metric_catalogue.csv`
(`applies_to` / `direction`) — the same field set 5b hashes and prompts over, so
"regenerate the read iff a prompt input changed" holds by construction. A
`tests/tooling` guard asserts this mirror stays in sync with the seed.
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

# Bump to force a global 5b regeneration when the prompt/rubric field set changes.
INPUT_HASH_VERSION = "5a.1"

# Per-type card metric sets — mirror metric_catalogue.csv `applies_to`. These feed the
# input hash (and, in 5b, the prompt), so they are the FULL displayed set per type, not
# only the health axes the verdict reads.
INPUT_FIELDS_BY_TYPE: dict[str, tuple[str, ...]] = {
    "operating": (
        "forward_pe",
        "ebit_margin_pct",
        "revenue_growth_yoy_pct",
        "net_debt_to_ebitda",
        "fcf_margin_pct",
        "debt_to_equity",
        "current_ratio_stmt",
        "statement_roe_pct",
    ),
    "financial": (
        "forward_pe",
        "revenue_growth_yoy_pct",
        "statement_roe_pct",
        "price_to_tangible_book",
        "net_margin_pct",
        "roa_pct",
        "dividend_yield_pct",
    ),
    "pre_revenue": (
        "net_cash_to_market_cap",
        "working_capital",
        "cash_runway_months",
        "burn_rate_monthly",
    ),
}

# Direction per metric — mirrors metric_catalogue.csv `direction`.
DIRECTION_BY_METRIC: dict[str, str] = {
    "forward_pe": "lower_better",
    "ebit_margin_pct": "higher_better",
    "revenue_growth_yoy_pct": "higher_better",
    "net_debt_to_ebitda": "lower_better",
    "fcf_margin_pct": "higher_better",
    "debt_to_equity": "lower_better",
    "current_ratio_stmt": "higher_better",
    "statement_roe_pct": "higher_better",
    "price_to_tangible_book": "lower_better",
    "net_margin_pct": "higher_better",
    "roa_pct": "higher_better",
    "dividend_yield_pct": "higher_better",
    "net_cash_to_market_cap": "higher_better",
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


# --- Per-type verdict policies (owner-signed §6 bands; conservative worst-axis-wins) ---
# The verdict is HEALTH/resilience only: leverage, profitability, cash, liquidity, runway.
# Valuation (forward_pe, price_to_tangible_book) and growth are excluded on purpose.


def _verdict_operating(row: Mapping[str, Any]) -> str:
    # Core axes are eligibility-required, so present for eligible operating cards.
    core = (
        _axis(row, "net_debt_to_ebitda", weak_th=3.0, good_th=1.5),
        _axis(row, "ebit_margin_pct", weak_th=0.0, good_th=10.0),
        _axis(row, "fcf_margin_pct", weak_th=0.0, good_th=5.0),
    )
    # Supporting axes may be null; they can break a tie but never rescue a red flag.
    supporting = (
        _axis(row, "debt_to_equity", weak_th=2.0, good_th=1.0),
        _axis(row, "current_ratio_stmt", weak_th=1.0, good_th=1.5),
        _axis(row, "statement_roe_pct", weak_th=0.0, good_th=10.0),
    )
    if any(b == "weak" for b in core):
        return VERDICT_RED
    if all(b == "good" for b in core) and not any(b == "weak" for b in supporting):
        return VERDICT_GREEN
    return VERDICT_YELLOW


def _verdict_financial(row: Mapping[str, Any]) -> str:
    # Banks: profitability/returns only — capital adequacy (CET1/Tier 1) is unsourceable
    # from yfinance, so this verdict is deliberately modest (documented in data_contract).
    roe = _axis(row, "statement_roe_pct", weak_th=0.0, good_th=8.0)
    margin = _axis(row, "net_margin_pct", weak_th=0.0, good_th=15.0)
    roa = _axis(row, "roa_pct", weak_th=0.0, good_th=0.8)
    if roe == "weak" or margin == "weak":
        return VERDICT_RED
    if roe == "good" and margin == "good" and roa in ("good", "unknown"):
        return VERDICT_GREEN
    return VERDICT_YELLOW


def _verdict_pre_revenue(row: Mapping[str, Any]) -> str:
    # Survival story. cash_runway_months is null when NOT burning cash (a positive) —
    # treat null runway as good; the net-cash and working-capital axes independently
    # catch a genuinely fragile pre-revenue company.
    runway_val = row.get("cash_runway_months")
    runway = "good" if _is_missing(runway_val) else _axis(
        row, "cash_runway_months", weak_th=12.0, good_th=24.0
    )
    net_cash = _axis(row, "net_cash_to_market_cap", weak_th=0.0, good_th=0.2)
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
    """sha256 hex over the canonicalized per-type input set + company_type + verdict + version.

    5b regenerates the prose read only when this hash changes. Numbers only — name/sector
    are context, not signals ("reason only from the given numbers").
    """
    ctype = normalize_company_type(row.get("company_type"))
    payload = {
        "version": version,
        "company_type": ctype,
        "verdict": verdict,
        "inputs": {field: _canonical_number(row.get(field)) for field in INPUT_FIELDS_BY_TYPE[ctype]},
    }
    blob = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()
