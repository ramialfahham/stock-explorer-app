"""Deterministic per-type financial-health verdict + regeneration hash (Slice 5a).

Pure, no I/O. The verdict COLOR is decided here by transparent rules — never by the
LLM (5b writes only the prose read). The verdict measures **financial health /
resilience** from the card's own numbers; it deliberately excludes growth, and it is
**not** investment advice. It used to exclude valuation too — as of 2026-08-26 there is no
valuation metric left to exclude, since every price-carrying metric was dropped from the
catalogue.

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
# 5a.2 (2026-08-26): READ_SYSTEM_PROMPT gained a no-dashes rule and a don't-sound-like-a-model
# rule, and the verdict wording changed from sturdy/strained to healthy/fragile. Existing reads
# were written under the old prompt and would otherwise survive untouched (reads regenerate on
# input-hash change, and none of the NUMBERS moved), leaving em dashes and "sturdy" phrasing on
# every card whose figures happen to be stable. The bump is what makes them regenerate.
# Precisely: it advances the stored hash for EVERY record, so every card is offered for
# regeneration on the next run. A card whose read actually regenerates gets new prose. A
# card whose Haiku call FAILS is not covered by that guarantee -- attach_reads() counts it
# and moves on without setting ai_read, while the record still carries the new hash into
# the upsert, so the next run's regenerate test (hash differs OR ai_read empty) may skip
# it. Whether the old prose survives or is nulled depends on how PostgREST treats a batch
# whose rows have different keys, which nothing here pins. The last run reported failed=0,
# so this is not known to have bitten -- do not claim it cannot.
INPUT_HASH_VERSION = "5a.2"

# Per-type card metric sets — mirror metric_catalogue.csv `applies_to`. These feed the
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

# Direction per metric — mirrors metric_catalogue.csv `direction`.
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


# --- Per-type verdict policies (owner-signed §6 bands; conservative worst-axis-wins) ---
# The verdict is HEALTH/resilience only: leverage, profitability, cash, liquidity, runway.
# Growth is excluded on purpose. Valuation used to be excluded here too; as of 2026-08-26
# there is no valuation metric left to exclude -- forward_pe, price_to_tangible_book and
# dividend_yield_pct were dropped from the catalogue because they carry the share price and
# this pipeline refreshes twice a month. Step 2 of that work will widen the verdict to read
# every remaining metric; until then it still reads only the health axes below.


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
    # net_cash is a MONEY AMOUNT since 2026-08-26, not the old ratio against market cap, so
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
- Interpret, don't list. Pull out the one or two things that most shape the financial picture and say what they mean; don't recite every number back.
- Growth is context only - never treat high growth as a reason to buy. The verdict measures financial health and resilience only. (Valuation metrics were removed from this app on 2026-08-26, so there is no P/E or price-to-book figure to be given to you at all.)
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
# the growth line is tagged "context only" so the read never
# turns them into a buy cue. (Owner-signed §6, alongside READ_SYSTEM_PROMPT.)
READ_METRIC_BRIEF: dict[str, dict[str, str]] = {
    "ebit_margin_pct": {
        "label": "Operating margin",
        "fmt": "pct",
        "gloss": "share of each sales dollar kept as operating profit (higher = more profitable); can look extreme when revenue is very small",
    },
    "revenue_growth_yoy_pct": {
        "label": "Revenue growth vs a year ago",
        "fmt": "pct",
        "gloss": "how fast sales are growing - context only, not a health signal; a huge percentage can just mean a very small prior-year base, not real momentum",
    },
    "net_debt_to_ebitda": {
        "label": "Net debt / EBITDA",
        "fmt": "ratio",
        "gloss": "roughly how many years of earnings would clear net debt (lower = less borrowing); can explode to a huge or distorted number when earnings are near zero",
    },
    "fcf_margin_pct": {
        "label": "Free cash flow margin",
        "fmt": "pct",
        "gloss": "real cash kept from each sales dollar (higher = stronger); negative = burning cash; can look extreme when revenue is very small",
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
        "gloss": "final profit kept from each revenue dollar after all costs (higher = more profitable); for a financial company \"revenue\" means net interest plus fees, not sales",
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
# (never a fake symbol). The app spans US/UK/JP/AU/DE markets, so "$" is not a safe default.
_CURRENCY_SYMBOLS = {"USD": "$", "GBP": "£", "JPY": "¥", "EUR": "€", "AUD": "A$"}


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
    currency = row.get("currency")  # names the money amounts in the card's own currency
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
    user = (
        f"Company type: {ctype}\n"
        f"Health verdict: {meaning}\n\n"
        f"Numbers for this company:\n{facts}\n\n"
        "Write the 2-3 sentence read."
    )
    return READ_SYSTEM_PROMPT, user
