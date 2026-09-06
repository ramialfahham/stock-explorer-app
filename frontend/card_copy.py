"""Plain-language metric lines for beginners (north_star).

Metric display definitions (label, format, direction, tier/order, and the plain-language
gloss / analogy / learn copy) come from `frontend/metrics.json`, generated from the
`metric_catalogue` seed by `scripts/export_metric_definitions_json.py`. The seed is the single
source of truth; do not hand-edit metrics.json or reintroduce hardcoded metric dicts here.
"""

import json
from datetime import date
from pathlib import Path

_METRICS_JSON = Path(__file__).resolve().parent / "metrics.json"


def _load_metrics() -> list[dict]:
    with _METRICS_JSON.open(encoding="utf-8") as f:
        return json.load(f)["metrics"]


_METRICS = _load_metrics()
_BY_ID = {m["metric_id"]: m for m in _METRICS}

ALL_METRICS = tuple(m["metric_id"] for m in _METRICS)
VISIBLE_METRICS = tuple(m["metric_id"] for m in _METRICS if m["importance_tier"] == 1)
DEEP_DIVE_METRICS = tuple(m["metric_id"] for m in _METRICS if m["importance_tier"] == 2)

METRIC_LABELS = {m["metric_id"]: m["label"] for m in _METRICS}
METRIC_GLOSS = {m["metric_id"]: m["gloss"] for m in _METRICS}
METRIC_ANALOGY = {m["metric_id"]: m["analogy"] for m in _METRICS}
METRIC_LEARN = {m["metric_id"]: m["learn"] for m in _METRICS}

_METRIC_FORMAT = {m["metric_id"]: m["format"] for m in _METRICS}
_METRIC_BASIS_COLUMN = {m["metric_id"]: (m["basis_column"] or None) for m in _METRICS}

# Sector/Lifecycle Router: which company types render each metric (from the catalogue).
DEFAULT_COMPANY_TYPE = "operating"
_METRIC_APPLIES_TO = {m["metric_id"]: tuple(m.get("applies_to") or ()) for m in _METRICS}

# Canonical analytical-lens order (matches the metric_catalogue `perspective` taxonomy). A card's
# metrics group by lens, then display_order within a lens — so each per-type card reads coherently
# from its own subset. This is identity-preserving for the operating card (its display_order already
# follows lens order) and gives disjoint per-type sets (bank, pre-revenue) a lens-grouped order too.
_LENS_ORDER = ("valuation", "profitability", "growth", "solvency", "liquidity", "cash", "returns")
_LENS_RANK = {lens: rank for rank, lens in enumerate(_LENS_ORDER)}
_PERSPECTIVE_BY_METRIC = {m["metric_id"]: m["perspective"] for m in _METRICS}


_LEAD_METRIC_BY_TYPE = {
    "operating": "ebit_margin_pct",
    "financial": "statement_roe_pct",
    "pre_revenue": "cash_runway_months",
}


def lead_metric_for_row(card: dict) -> tuple[str, str] | None:
    """The one metric a Discover list row leads with.

    Operating margin for operating companies, Return on equity for financial (banks), cash
    runway for pre-revenue: each is a CORE, verdict-deciding input to that company type's
    own verdict rule in scripts/assessment_rules.py, not just any input of any weight.
    `statement_roe_pct` was the first choice for both operating and financial, but for
    `_verdict_operating` it is only a supporting axis that "can break a tie but never rescue
    a red flag" (that function's own comment); the axes that actually decide red/green for
    an operating card are net_debt_to_ebitda, ebit_margin_pct, and fcf_margin_pct. A metric
    that only weakly relates to the actual verdict rule, on the majority company type, would
    misrepresent what decides that company's assessment. `ebit_margin_pct` is the one of
    those three axes with importance_tier 1 in the metric catalogue, already the headline
    profitability figure for an operating card. Returns None, not format_metric_value()'s
    em-dash placeholder, when the value is missing, so the row degrades to title/subtitle
    only rather than showing a blank or invented number.
    """
    company_type = card.get("company_type") or DEFAULT_COMPANY_TYPE
    metric_id = _LEAD_METRIC_BY_TYPE.get(company_type)
    if metric_id is None or card.get(metric_id) is None:
        return None
    label = metric_label(metric_id, card)
    value = format_metric_value(metric_id, card.get(metric_id), card.get("currency"))
    return label, value


def metric_perspective_label(metric: str) -> str:
    """Group-header text for this metric's lens (catalogue `perspective`, title-cased) —
    the same lens metrics_for_card() already sorts by, just made visible on the card
    face and in the learn panel instead of only ordering silently."""
    return _PERSPECTIVE_BY_METRIC.get(metric, "").title()


def metrics_for_card(card: dict, tier: int | None = None) -> tuple[str, ...]:
    """Metric ids to render for this card, grouped by analytical lens then display order.

    A metric shows only when it applies to the card's ``company_type`` **and** has a value —
    so a lens that is blank for a type (e.g. bank solvency) or simply missing for a row is
    omitted, never rendered as an em-dash. A missing/None ``company_type`` defaults to
    ``operating`` (the classifier's own default and the current universe's majority).
    """
    company_type = card.get("company_type") or DEFAULT_COMPANY_TYPE
    selected: list[dict] = []
    for definition in _METRICS:
        metric_id = definition["metric_id"]
        if company_type not in _METRIC_APPLIES_TO.get(metric_id, ()):
            continue
        if tier is not None and definition["importance_tier"] != tier:
            continue
        if card.get(metric_id) is None:
            continue
        selected.append(definition)
    selected.sort(
        key=lambda d: (_LENS_RANK.get(d["perspective"], len(_LENS_ORDER)), d["display_order"] or 0)
    )
    return tuple(d["metric_id"] for d in selected)

# (metric, sector-median column, short direction) — derived from the catalogue.
_DIRECTION_SHORT = {"higher_better": "higher", "lower_better": "lower", "neutral": "neutral"}
# Every catalogued metric's direction, not just the 9 benchmarkable ones -- backs
# metric_direction()/metric_gloss()'s universal "Higher/Lower is better." cue.
_DIRECTION_BY_METRIC = {m["metric_id"]: _DIRECTION_SHORT.get(m["direction"], "neutral") for m in _METRICS}
BENCHMARK_METRICS = tuple(
    (m["metric_id"], f"sector_median_{m['metric_id']}", _DIRECTION_SHORT.get(m["direction"], "neutral"))
    for m in _METRICS
    if m["benchmarkable"]
)

PEER_THRESHOLD = 8

# Yahoo Finance GICS sector labels (info_sector on cards).
SECTOR_GLOSS = {
    "Communication Services": (
        "Media, telecom, and entertainment: how people connect and consume content"
    ),
    "Consumer Cyclical": (
        "Discretionary spending: retail, autos, travel, and other non-essential purchases"
    ),
    "Consumer Defensive": (
        "Everyday essentials: food, household goods, and staples people buy in any economy"
    ),
    "Energy": "Oil, gas, and energy producers, tied to commodity prices and global demand",
    "Financial Services": (
        "Banks, insurers, and asset managers: profit from lending, fees, and financial products"
    ),
    "Healthcare": "Pharmaceuticals, medical devices, and health services",
    "Industrials": "Manufacturing, transport, and business equipment, tied to economic cycles",
    "Basic Materials": (
        "Raw materials: mining, chemicals, and forestry inputs for other industries"
    ),
    "Real Estate": "Property owners and developers: revenue from rent and real estate values",
    "Technology": "Software, hardware, and IT services, often growth-focused and R&D heavy",
    "Utilities": "Power, water, and gas distributors: regulated, steady-demand businesses",
}

DEFAULT_SECTOR_GLOSS = (
    "Industry grouping used to compare this company with similar businesses in the app"
)

MEDIAN_PRIMER = (
    "Median = the middle value among eligible companies in this sector and market."
)

BENCHMARK_COMPARE_UNAVAILABLE_LEARN = (
    "Fewer than 8 similar companies in this market: sector compare is hidden."
)


def _benchmark_eligible(card: dict) -> bool:
    peer_count = card.get("sector_peer_count")
    return peer_count is not None and peer_count >= PEER_THRESHOLD


def benchmark_compare_unavailable_learn(card: dict) -> str | None:
    peer_count = card.get("sector_peer_count")
    if peer_count is None or peer_count >= PEER_THRESHOLD:
        return None
    return BENCHMARK_COMPARE_UNAVAILABLE_LEARN


def benchmark_compare_available(card: dict) -> bool:
    return _benchmark_eligible(card)


def sector_headline(card: dict) -> str:
    """Sector label with peer count when available (north_star)."""
    sector = card.get("sector") or "Unknown sector"
    peer_count = card.get("sector_peer_count")
    if peer_count is not None:
        return f"{sector} ({peer_count} companies)"
    return sector


def metric_label(metric: str, card: dict | None = None) -> str:
    if metric == "ebit_margin_pct" and card and card.get("ebit_margin_basis") == "annual_latest":
        return "Operating margin (annual)"
    return METRIC_LABELS[metric]


def metric_direction(metric: str) -> str:
    """'higher' | 'lower' | 'neutral', straight from the catalogue's own `direction`
    field -- no metric-specific special-casing. See metric_gloss() for why every
    direction (not just the benchmarked ones) gets a cue."""
    return _DIRECTION_BY_METRIC.get(metric, "neutral")


def metric_gloss(metric: str, value: float | None, card: dict | None = None) -> str:
    """Card-face gloss; value-aware where the story depends on the number.

    Ends with a plain "Higher is better."/"Lower is better." for every metric with a
    known catalogue direction -- a ceteris-paribus statement about that metric's own
    axis (owner's call: this holds even for metrics whose free-text `interpretation`
    carries a caveat, e.g. revenue growth's "growth is not health -- a company can grow into
    losses" -- the caveat is about using the metric as a standalone judgment, not about
    which way its own axis points. The example used to be forward P/E's "always read next
    to growth", which stopped being checkable when that metric was dropped;
    this one is a live catalogue row on purpose, so a reader can verify it). Applies whether or not the metric currently has a range mark; a metric
    without one (not in the 9 benchmarked today) still gets the same plain cue.
    Suppressed for net_debt_to_ebitda's value-aware "Net cash" branch and
    debt_to_equity's "Negative equity" branch -- both already state the actual
    situation directly, and appending "Lower is better." on top would imply a more
    negative number is a better version of the same good news, when it's actually a
    different, broken state the ratio's normal direction no longer describes.

    Re-confirmed. The owner asked for the cue to be dropped as clutter, then
    reopened it: the honest tension is that "better" is only true ceteris paribus, and
    this app never teaches that concept. Kept anyway, and deliberately on EVERY metric
    rather than only the inverted ones -- a cue that appears on some metrics and not
    others makes its own absence ambiguous, which is worse than not having it. The bar
    itself carries no direction (right is only "bigger"), so for the two benchmarked inverted
    metrics (net_debt_to_ebitda, debt_to_equity) a beginner has no way to read the mark without
    this line -- and only 9 of the 13 catalogued metrics are benchmarkable at all, so for the other 4
    (pre-revenue's working_capital, net_cash, cash_runway_months, burn_rate_monthly) this cue
    is the ONLY direction signal anywhere on the card face. (Counts changed when the three
    price-carrying metrics were dropped, and again when the 5-metric benchmark expansion --
    owner-approved follow-up to MR #22 -- made every operating/financial metric benchmarkable;
    forward_pe used to be the second inverted one.) The
    clutter that prompted the question was addressed in presentation instead: the gloss
    is now a step larger and lighter than the range mark's own axis labels.
    """
    if metric == "net_debt_to_ebitda" and value is not None and value < 0:
        return "Net cash: cash on hand exceeds debt"
    if metric == "debt_to_equity" and value is not None and value < 0:
        return "Negative equity, so this ratio isn't a normal leverage read"
    if metric == "ebit_margin_pct" and card and card.get("ebit_margin_basis") == "annual_latest":
        base = "Operating profit as share of sales (latest annual)"
    else:
        base = METRIC_GLOSS[metric]
    direction = metric_direction(metric)
    if direction == "higher":
        return f"{base}. Higher is better."
    if direction == "lower":
        return f"{base}. Lower is better."
    return base


def metric_analogy(metric: str, value: float | None, card: dict | None = None) -> str:
    if metric == "net_debt_to_ebitda" and value is not None and value < 0:
        return (
            "Cash on the balance sheet exceeds debt: a net cash position, "
            "not leverage to repay."
        )
    if metric == "debt_to_equity" and value is not None and value < 0:
        return (
            "Owners' equity has gone negative here, so the usual mortgage-versus-"
            "equity comparison breaks down."
        )
    if metric == "ebit_margin_pct" and card and card.get("ebit_margin_basis") == "annual_latest":
        return (
            "Out of everything the company sold that year, this is the slice kept as "
            "operating profit before interest and taxes: one fiscal year, not four quarters."
        )
    return METRIC_ANALOGY[metric]


def metric_learn_text(metric: str, value: float | None, card: dict | None = None) -> str:
    if metric == "net_debt_to_ebitda" and value is not None and value < 0:
        return (
            "Net debt is total debt minus cash. When cash exceeds debt, the ratio "
            "is negative: a net cash position. Yahoo's EBITDA is still in the "
            "denominator; read the sign as cash vs debt, not years to repay."
        )
    if metric == "debt_to_equity" and value is not None and value < 0:
        return (
            "Debt-to-equity divides total debt by shareholders' equity. When heavy "
            "losses or buybacks push equity below zero, the ratio's sign flips: a "
            "very negative number here does not mean low debt, it means the owners' "
            "stake itself has gone negative."
        )
    if metric == "ebit_margin_pct" and card and card.get("ebit_margin_basis") == "annual_latest":
        return (
            "Yahoo did not provide four quarters of operating profit for this ticker. "
            "This card uses the latest annual operating profit divided by annual "
            "total revenue, comparable in spirit to margin, but not trailing twelve months."
        )
    return METRIC_LEARN[metric]


def saved_row_subtitle(card: dict) -> str:
    """Second line for Saved list rows: ticker and sector only."""
    ticker = card.get("ticker") or "—"
    sector = card.get("sector") or "Unknown sector"
    return f"{ticker} · {sector}"


def sector_gloss_line(sector: str | None) -> str:
    if not sector:
        return DEFAULT_SECTOR_GLOSS
    return SECTOR_GLOSS.get(sector, DEFAULT_SECTOR_GLOSS)


def format_snapshot_date(raw: date | str | None) -> str | None:
    if raw is None:
        return None
    if isinstance(raw, str):
        try:
            parsed = date.fromisoformat(raw[:10])
        except ValueError:
            return None
    elif isinstance(raw, date):
        parsed = raw
    else:
        return None
    return parsed.strftime("%B %d, %Y")


def freshness_line(card: dict) -> str | None:
    formatted = format_snapshot_date(card.get("snapshot_date"))
    if not formatted:
        return None
    line = f"As of {formatted}"
    raw = card.get("snapshot_date")
    parsed = None
    if isinstance(raw, str):
        try:
            parsed = date.fromisoformat(raw[:10])
        except ValueError:
            parsed = None
    elif isinstance(raw, date):
        parsed = raw
    if parsed is not None:
        age = (date.today() - parsed).days
        if age > STALE_SNAPSHOT_DAYS:
            line += f" · data may be up to {age} days old"
    return line


_VALUE_FORMATTERS = {
    "percent_1": lambda value: f"{value:.1f}%",
    "ratio_1": lambda value: f"{value:.1f}",
    "ratio_2": lambda value: f"{value:.2f}",
}

# Mirrors scripts/assessment_rules.py so the read names the currency the card face shows. Not
# every registry-driven market is here: CHF has no entry and falls back to the bare code, which
# the owner settled on 2026-08-28 as correct, the rule being to use each currency's real-world
# form. Keep this map identical to the one in scripts/assessment_rules.py; a test pins it.
_CURRENCY_SYMBOLS = {"USD": "$", "GBP": "£", "JPY": "¥", "EUR": "€", "AUD": "A$"}


def _format_currency_compact(value: float, currency: str | None) -> str:
    """A money amount as a compact, sign-aware string with the card's currency symbol.

    e.g. 2_100_000_000/GBP -> "£2.1B"; -58_300_000/USD -> "-$58.3M". Used for level metrics
    (working capital, monthly cash burn) that are amounts, not ratios.
    """
    code = (currency or "").upper()
    symbol = _CURRENCY_SYMBOLS.get(code) or (f"{code} " if code else "")
    sign = "-" if value < 0 else ""
    magnitude = abs(value)
    if magnitude >= 1_000_000_000:
        body = f"{magnitude / 1_000_000_000:.1f}B"
    elif magnitude >= 1_000_000:
        body = f"{magnitude / 1_000_000:.1f}M"
    elif magnitude >= 1_000:
        body = f"{magnitude / 1_000:.1f}K"
    else:
        body = f"{magnitude:.0f}"
    return f"{sign}{symbol}{body}"


def format_metric_value(metric: str, value: float | None, currency: str | None = None) -> str:
    if value is None:
        return "—"
    fmt = _METRIC_FORMAT.get(metric, "ratio_2")
    if fmt == "currency_compact":
        return _format_currency_compact(value, currency)
    return _VALUE_FORMATTERS[fmt](value)


def benchmark_position(
    card: dict,
    metric: str,
    median_key: str,
) -> str | None:
    """Return above, below, or at vs sector median (neutral positional compare)."""
    if not _benchmark_eligible(card):
        return None
    value = card.get(metric)
    median = card.get(median_key)
    if value is None or median is None:
        return None
    if value > median:
        return "above"
    if value < median:
        return "below"
    return "at"


# Standard box-plot outlier-fence multiplier (Tukey, 1977) -- not a value picked to fit any
# one card. Used by benchmark_range() to clamp the displayed range so one extreme peer no
# longer dominates every other peer's marker position in the same sector (Gemini feedback
# point 5, docs/backlog/gemini_verdict_feedback.md).
_TUKEY_FENCE_MULTIPLIER = 1.5


def benchmark_range(card: dict, metric: str, median_key: str) -> dict | None:
    """Position this card's value within its sector's outlier-aware display range, median
    labeled.

    The display range clamps to a Tukey fence (Q1 - 1.5*IQR .. Q3 + 1.5*IQR) whenever the
    sector's quartiles are present, so one extreme peer no longer dominates every other peer's
    marker position in the same sector -- the exact case documented in
    docs/ui/card_metric_cell.md's "Known data-quality interaction" note (Deep Yellow/DYL,
    -129,810.5% FCF margin, ASX Energy). Falls back to the raw [sector_min, sector_max] range
    when quartiles are null (a sector exported before this shipped, or any transitional state),
    so nothing regresses to "no mark". For a sector with no real outlier, the fence is wider
    than the true min/max, so the clamp is a no-op and the displayed range is unchanged.

    Returns None when unavailable (peer count < 8, same threshold benchmark_position already
    applies) or degenerate (the display range collapses to zero width -- every eligible peer
    reports the same value). `min`/`max` in the returned dict are the DISPLAYED bound -- what
    actually renders at the 0%/100% track edges -- which is the fence-clamped value when a
    fence narrows the range, not necessarily the single most extreme peer's raw value.

    `low_off_scale` / `high_off_scale` report whether this card's OWN value fell outside the
    displayed range on that side; its raw value is never affected, only its marker position.
    position_pct / median_pct are clamped to [0, 100] defensively.
    """
    if not _benchmark_eligible(card):
        return None
    value = card.get(metric)
    median = card.get(median_key)
    minimum = card.get(f"sector_min_{metric}")
    maximum = card.get(f"sector_max_{metric}")
    if value is None or median is None or minimum is None or maximum is None:
        return None
    q1 = card.get(f"sector_q1_{metric}")
    q3 = card.get(f"sector_q3_{metric}")
    display_min, display_max = minimum, maximum
    if q1 is not None and q3 is not None:
        iqr = q3 - q1
        fence_low = q1 - _TUKEY_FENCE_MULTIPLIER * iqr
        fence_high = q3 + _TUKEY_FENCE_MULTIPLIER * iqr
        display_min = max(minimum, fence_low)
        display_max = min(maximum, fence_high)
    span = display_max - display_min
    if span <= 0:
        return None
    position_pct = max(0.0, min(100.0, (value - display_min) / span * 100))
    median_pct = max(0.0, min(100.0, (median - display_min) / span * 100))
    return {
        "min": display_min,
        "median": median,
        "max": display_max,
        "value": value,
        "position_pct": position_pct,
        "median_pct": median_pct,
        "low_off_scale": value < display_min,
        "high_off_scale": value > display_max,
    }


_BENCHMARK_INDICATOR_LABELS = {
    "above": "Higher than sector median",
    "below": "Lower than sector median",
    "at": "At sector median",
}


def benchmark_indicator_label(card: dict, metric: str, median_key: str) -> str | None:
    position = benchmark_position(card, metric, median_key)
    if position is None:
        return None
    return _BENCHMARK_INDICATOR_LABELS[position]


# Worst-case gap between two HEALTHY scheduled runs under the 1st/15th cron, plus one day
# of slack: 15th -> 1st is 14 days after a non-leap February, 17 days after any 31-day
# month. A threshold at or below that worst case would flag the normal tail of a healthy
# cycle as stale, same failure mode this constant is supposed to catch. Was 7, matched to
# the prior weekly cadence the same way — recalibrate this again if the cron changes.
STALE_SNAPSHOT_DAYS = 18

# Yahoo longBusinessSummary preview length on the card face (tap to expand).
BUSINESS_SUMMARY_PREVIEW_WORDS = 20


def business_summary_full(card: dict) -> str | None:
    raw = card.get("business_summary") or card.get("longBusinessSummary")
    if raw is None:
        return None
    text = str(raw).strip()
    return text or None


def truncate_words(text: str, max_words: int) -> tuple[str, bool]:
    """Return normalized text truncated to max_words; bool is True when shortened."""
    normalized = " ".join(text.split())
    if not normalized:
        return "", False
    words = normalized.split()
    if len(words) <= max_words:
        return normalized, False
    preview = " ".join(words[:max_words]).rstrip(".,;:")
    return f"{preview}…", True


def business_summary_preview(
    card: dict,
    *,
    max_words: int = BUSINESS_SUMMARY_PREVIEW_WORDS,
) -> str | None:
    """Card-face preview from Yahoo text — original wording, word-limited."""
    full = business_summary_full(card)
    if not full:
        return None
    preview, _ = truncate_words(full, max_words)
    return preview or None


def business_summary_is_truncated(
    card: dict,
    *,
    max_words: int = BUSINESS_SUMMARY_PREVIEW_WORDS,
) -> bool:
    full = business_summary_full(card)
    if not full:
        return False
    _, truncated = truncate_words(full, max_words)
    return truncated


# Health verdict (Slice 6c) — token -> emoji/label.
VERDICT_EMOJI = {"green": "🟢", "yellow": "🟡", "red": "🔴"}
# Owner-chosen (§6), replacing Sturdy/Mixed/Strained: "sturdy" is not a word
# people use. Health framing, deliberately not Strong/Weak, which read closer to a verdict on
# the SHARE than on the company's finances — this app never implies buy or sell. These MUST
# stay in step with VERDICT_MEANING in scripts/assessment_rules.py, which tells the model how
# to end its paragraph; if they drift, a card's prose contradicts its own badge.
VERDICT_BADGE_LABEL = {"green": "Healthy", "yellow": "Mixed", "red": "Fragile"}

# Deterministic fallback for the health block's narrative when ai_read is absent (5a wrote the
# verdict; 5b's read is pending, a per-card API failure, or a hallucination-guard reject -- see
# scripts/generate_assessments.py's validate_read_metrics). A bare badge with nothing else read
# as broken to a reader, not "not yet written" (owner feedback, 2026-09-01) -- this fills that
# gap under its own honest heading ("What the verdict means" in frontend/card_ui.py, never
# BLOCK_LABEL_ASSESSMENT's "AI-written", which this text is not). Owner-authored wording (§6): a
# general one-line summary, not a description of the verdict engine's internal logic -- the
# engine's decisive-vs-supporting metric split and its per-metric thresholds have no
# representation anywhere in the UI, so text that leaned on either would assert something a
# reader has no way to check. No mechanical sync test against VERDICT_MEANING is possible or
# intended (deliberately different in kind, not just phrasing); tests/frontend/test_card_ui.py
# only checks this covers the same three verdict tokens. Keep these strings free of apostrophes
# and em/en-dashes -- _esc() HTML-entity-escapes them, which is fine for rendering but breaks a
# literal-substring test match.
VERDICT_FALLBACK_READ = {
    "green": "Strong across all financial-health metrics, with zero red flags.",
    "yellow": "No severe financial vulnerabilities, but not every metric clears the bar for strong.",
    "red": "Exhibits at least one severe financial vulnerability that impairs overall stability.",
}

# Shown on every "financial" company-type card (the whole GICS "Financial Services" sector --
# banks, insurers, payment networks, asset managers, exchanges, ratings agencies -- not banks
# specifically, see docs/data_contract.md's company_type classification), regardless of whether
# ai_read is present -- the LLM is only prompted, never required, to state this limit in its own
# prose (scripts/assessment_rules.py's READ_SYSTEM_PROMPT, "financial" company-type lens), so
# relying on the model to say it every time would silently reintroduce the gap this exists to
# close. Deliberately says "this company", not "this bank" -- mirrors READ_SYSTEM_PROMPT's own
# already-reviewed "financial company" framing rather than the bank-specific framing an earlier
# draft used, which was wrong for the non-bank share of this sector (equity-analyst-reviewer
# finding). Deliberately states only what's MISSING, not an enumeration of what's shown --
# an earlier draft said "profitability only" / "profitability and returns only" and was wrong
# both times as soon as checked against metric_catalogue.csv's actual applies_to=financial set
# (also includes a growth metric), because that set is data-driven and can change independently
# of this string. Stating only the one invariant fact (capital adequacy is never assessed here)
# can't go stale the same way. Owner-authored wording (§6), approved verbatim. Same constraint
# as VERDICT_FALLBACK_READ above: no apostrophe, no em/en dash (_esc() escaping breaks a
# literal-substring test match on those) -- "do not", not "don't".
FINANCIAL_CAPITAL_ADEQUACY_CAVEAT = (
    "These numbers do not show whether this company holds enough capital to stay safe."
)


def health_verdict_token(card: dict) -> str | None:
    """The card's health_verdict token if present and a known value, else None — a missing
    or unrecognized token means "no assessment", never a placeholder."""
    token = card.get("health_verdict")
    return token if token in VERDICT_EMOJI else None


def ai_read(card: dict) -> str | None:
    """The card's Claude-written prose read, or None when absent/blank."""
    text = str(card.get("ai_read") or "").strip()
    return text or None
