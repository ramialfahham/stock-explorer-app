"""Plain-language metric lines for beginners (north_star).

Metric label/format/gloss/analogy/learn copy comes from `frontend/metrics.json`, generated
from the `metric_catalogue` seed by `scripts/export_metric_definitions_json.py`. Do not
hand-edit metrics.json or reintroduce hardcoded metric dicts here.
"""

import json
import re
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

# Analytical-lens order (matches metric_catalogue's `perspective` taxonomy); cards group metrics
# by lens then display_order, so this order directly shapes every per-type card's layout.
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

    Operating margin for operating companies, return on equity for financial firms, cash
    runway for pre-revenue: each is a core, verdict-deciding input to that company type's
    own verdict rule in scripts/assessment_rules.py. Returns None, not format_metric_value()'s
    em-dash placeholder, when the value is missing, so the row falls back to title/subtitle only.
    """
    company_type = card.get("company_type") or DEFAULT_COMPANY_TYPE
    metric_id = _LEAD_METRIC_BY_TYPE.get(company_type)
    if metric_id is None or card.get(metric_id) is None:
        return None
    label = metric_label(metric_id, card)
    value = format_metric_value(metric_id, card.get(metric_id), card.get("currency"))
    return label, value


def metric_perspective_label(metric: str) -> str:
    """Group-header text for this metric's lens (catalogue `perspective`, title-cased) -- the
    same lens metrics_for_card() sorts by, now shown on the card face and learn panel."""
    return _PERSPECTIVE_BY_METRIC.get(metric, "").title()


def metrics_for_card(card: dict, tier: int | None = None) -> tuple[str, ...]:
    """Metric ids to render for this card, grouped by analytical lens then display order.

    Shows a metric only when it applies to the card's ``company_type`` and has a value, so a
    blank lens or missing value is omitted rather than rendered as an em-dash. A missing
    ``company_type`` defaults to ``operating``.
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

# (metric, sector-median column, short direction) -- derived from the catalogue.
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


def metric_gloss(
    metric: str,
    value: float | None,
    card: dict | None = None,
    *,
    benchmarked: bool = False,
) -> str:
    """Card-face gloss; value-aware where the story depends on the number.

    `benchmarked=True` inserts ", vs sector" before the direction cue. Ends with a plain
    "Higher/Lower is better." for every metric with a known catalogue direction, benchmarked
    or not, since the range bar itself carries no direction and this is the only direction
    signal on the card face for the metrics with no range mark. Suppressed for
    net_debt_to_ebitda's "Net cash" branch and debt_to_equity's "Negative equity" branch,
    which already state the actual situation directly; appending the cue there would imply a
    more negative number is a better version of the same good news, not the different broken
    state it actually is.
    """
    if metric == "net_debt_to_ebitda" and value is not None and value < 0:
        return "Net cash: cash on hand exceeds debt"
    if metric == "debt_to_equity" and value is not None and value < 0:
        return "Negative equity, so this ratio isn't a normal leverage read"
    if metric == "ebit_margin_pct" and card and card.get("ebit_margin_basis") == "annual_latest":
        base = "Operating profit as share of sales (latest annual)"
    else:
        base = METRIC_GLOSS[metric]
    if benchmarked:
        base = f"{base}, vs sector"
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

# Mirrors scripts/assessment_rules.py's currency map so the AI read matches the card face; a
# test pins them identical. CHF has no entry here and falls back to the bare ISO code by design.
_CURRENCY_SYMBOLS = {"USD": "$", "GBP": "£", "JPY": "¥", "EUR": "€", "AUD": "A$"}


def currency_symbol(currency: str | None) -> str:
    """The symbol the face prints money with; the ISO code when no symbol is known."""
    code = (currency or "").upper()
    return _CURRENCY_SYMBOLS.get(code) or code


def _format_currency_compact(value: float, currency: str | None) -> str:
    """A money amount as a compact, sign-aware string with the card's currency symbol.

    e.g. 2_100_000_000/GBP -> "£2.1B"; -58_300_000/USD -> "-$58.3M". Used for level metrics
    (working capital, monthly cash burn) that are amounts, not ratios.
    """
    symbol = currency_symbol(currency)
    if symbol[-1:].isalpha():
        symbol += " "
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


# Standard box-plot outlier-fence multiplier (Tukey, 1977), not tuned to any one card; clamps
# the displayed range in benchmark_range() so one extreme peer can't dominate every other peer's marker position.
_TUKEY_FENCE_MULTIPLIER = 1.5


def benchmark_range(card: dict, metric: str, median_key: str) -> dict | None:
    """Position this card's value within its sector's outlier-aware display range, median
    labeled.

    Clamps to a Tukey fence (Q1 - 1.5*IQR .. Q3 + 1.5*IQR) when sector quartiles are present,
    so one extreme peer can't dominate every other peer's marker position; falls back to the
    raw [sector_min, sector_max] range when quartiles are null. Returns None when unavailable
    (peer count < 8) or degenerate (range collapses to zero width). `min`/`max` in the result
    are the displayed bound, fence-clamped when a fence narrows the range, not necessarily the
    raw peer extreme. `low_off_scale`/`high_off_scale` flag only this card's marker position,
    never its raw value.
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


# Worst-case gap between two healthy 1st/15th-cron runs, plus one day of slack (17 days after
# a 31-day month); a lower threshold would flag the normal tail of a healthy cycle as stale.
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
    """Card-face preview from Yahoo text -- original wording, word-limited."""
    full = business_summary_full(card)
    if not full:
        return None
    preview, _ = truncate_words(full, max_words)
    return preview or None


# Splits only where a terminator is followed by whitespace and a capital letter, so "3.0%"
# (no following space) and "U.S. markets" (lowercase after) are not mistaken for sentence ends.
_SENTENCE_SPLIT = re.compile(r"(?<=[.!?])\s+(?=[A-Z])")


def ai_read_sentences(text: str) -> tuple[str, ...]:
    """Split the AI-written read (or the deterministic fallback, same shape) into one bullet
    per sentence for the card face -- always shown in full, nothing folded."""
    normalized = " ".join(text.split())
    if not normalized:
        return ()
    return tuple(s for s in (p.strip() for p in _SENTENCE_SPLIT.split(normalized)) if s)


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


VERDICT_EMOJI = {"green": "🟢", "yellow": "🟡", "red": "🔴"}
# Health framing, not Strong/Weak, which would read as a verdict on the SHARE rather than the
# company's finances. Must stay in step with VERDICT_MEANING in scripts/assessment_rules.py, or a card's prose contradicts its own badge.
VERDICT_BADGE_LABEL = {"green": "Healthy", "yellow": "Mixed", "red": "Fragile"}

# Fallback health-block text for when ai_read is absent; keep it a general summary, never the
# verdict engine's internal thresholds. No apostrophes/em-dashes: _esc() breaks a literal-substring test match on them.
VERDICT_FALLBACK_READ = {
    "green": "Strong across all financial-health metrics, with zero red flags.",
    "yellow": "No severe financial vulnerabilities, but not every metric clears the bar for strong.",
    "red": "Exhibits at least one severe financial vulnerability that impairs overall stability.",
}

# Always shown on "financial" cards regardless of ai_read (the model is only prompted, not
# required, to state this). States only what's missing, not what's shown, since the shown-metric set is data-driven; same no-apostrophe/em-dash rule as VERDICT_FALLBACK_READ above.
FINANCIAL_CAPITAL_ADEQUACY_CAVEAT = (
    "These numbers do not show whether this company holds enough capital to stay safe."
)


def health_verdict_token(card: dict) -> str | None:
    """The card's health_verdict token if present and a known value, else None -- a missing
    or unrecognized token means "no assessment", never a placeholder."""
    token = card.get("health_verdict")
    return token if token in VERDICT_EMOJI else None


def ai_read(card: dict) -> str | None:
    """The card's Claude-written prose read, or None when absent/blank."""
    text = str(card.get("ai_read") or "").strip()
    return text or None
