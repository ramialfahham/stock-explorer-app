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
BENCHMARK_METRICS = tuple(
    (m["metric_id"], f"sector_median_{m['metric_id']}", _DIRECTION_SHORT.get(m["direction"], "neutral"))
    for m in _METRICS
    if m["benchmarkable"]
)

PEER_THRESHOLD = 8

# Yahoo Finance GICS sector labels (info_sector on cards).
SECTOR_GLOSS = {
    "Communication Services": (
        "Media, telecom, and entertainment — how people connect and consume content"
    ),
    "Consumer Cyclical": (
        "Discretionary spending — retail, autos, travel, and other non-essential purchases"
    ),
    "Consumer Defensive": (
        "Everyday essentials — food, household goods, and staples people buy in any economy"
    ),
    "Energy": "Oil, gas, and energy producers — tied to commodity prices and global demand",
    "Financial Services": (
        "Banks, insurers, and asset managers — profit from lending, fees, and financial products"
    ),
    "Healthcare": "Pharmaceuticals, medical devices, and health services",
    "Industrials": "Manufacturing, transport, and business equipment — tied to economic cycles",
    "Basic Materials": (
        "Raw materials — mining, chemicals, and forestry inputs for other industries"
    ),
    "Real Estate": "Property owners and developers — revenue from rent and real estate values",
    "Technology": "Software, hardware, and IT services — often growth-focused and R&D heavy",
    "Utilities": "Power, water, and gas distributors — regulated, steady-demand businesses",
}

DEFAULT_SECTOR_GLOSS = (
    "Industry grouping used to compare this company with similar businesses in the app"
)

MEDIAN_PRIMER = (
    "Median = the middle value among eligible companies in this sector and market."
)

BENCHMARK_COMPARE_UNAVAILABLE_LEARN = (
    "Fewer than 8 similar companies in this market — sector compare is hidden."
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


def metric_gloss(metric: str, value: float | None, card: dict | None = None) -> str:
    """Card-face gloss; value-aware where the story depends on the number."""
    if metric == "net_debt_to_ebitda" and value is not None and value < 0:
        return "Net cash — cash on hand exceeds debt"
    if metric == "ebit_margin_pct" and card and card.get("ebit_margin_basis") == "annual_latest":
        return "Operating profit as share of sales (latest annual)"
    return METRIC_GLOSS[metric]


def metric_analogy(metric: str, value: float | None, card: dict | None = None) -> str:
    if metric == "net_debt_to_ebitda" and value is not None and value < 0:
        return (
            "Cash on the balance sheet exceeds debt — a net cash position, "
            "not leverage to repay."
        )
    if metric == "ebit_margin_pct" and card and card.get("ebit_margin_basis") == "annual_latest":
        return (
            "For each dollar of annual sales, this is the slice kept as operating "
            "profit before interest and taxes — one fiscal year, not four quarters."
        )
    return METRIC_ANALOGY[metric]


def metric_learn_text(metric: str, value: float | None, card: dict | None = None) -> str:
    if metric == "net_debt_to_ebitda" and value is not None and value < 0:
        return (
            "Net debt is total debt minus cash. When cash exceeds debt, the ratio "
            "is negative — a net cash position. Yahoo's EBITDA is still in the "
            "denominator; read the sign as cash vs debt, not years to repay."
        )
    if metric == "ebit_margin_pct" and card and card.get("ebit_margin_basis") == "annual_latest":
        return (
            "Yahoo did not provide four quarters of operating profit for this ticker. "
            "This card uses the latest annual operating profit divided by annual "
            "total revenue — comparable in spirit to margin, but not trailing twelve months."
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

# Registry-driven markets use these currencies; fall back to the code for anything else.
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


_BENCHMARK_INDICATORS = {
    "above": "↑",
    "below": "↓",
    "at": "→",
}

_BENCHMARK_INDICATOR_LABELS = {
    "above": "Higher than sector median",
    "below": "Lower than sector median",
    "at": "At sector median",
}


def benchmark_indicator(card: dict, metric: str, median_key: str) -> str | None:
    position = benchmark_position(card, metric, median_key)
    if position is None:
        return None
    return _BENCHMARK_INDICATORS[position]


def benchmark_indicator_label(card: dict, metric: str, median_key: str) -> str | None:
    position = benchmark_position(card, metric, median_key)
    if position is None:
        return None
    return _BENCHMARK_INDICATOR_LABELS[position]


STALE_SNAPSHOT_DAYS = 7

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
VERDICT_BADGE_LABEL = {"green": "Sturdy", "yellow": "Mixed", "red": "Strained"}


def health_verdict_token(card: dict) -> str | None:
    """The card's health_verdict token if present and a known value, else None — a missing
    or unrecognized token means "no assessment", never a placeholder."""
    token = card.get("health_verdict")
    return token if token in VERDICT_EMOJI else None


def ai_read(card: dict) -> str | None:
    """The card's Claude-written prose read, or None when absent/blank."""
    text = str(card.get("ai_read") or "").strip()
    return text or None
