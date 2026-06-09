"""Plain-language metric lines for beginners (north_star)."""

from datetime import date

METRIC_HELP = {
    "forward_pe": "Forward P/E compares today's share price to expected earnings over the next year.",
    "ebit_margin_pct": "Operating margin (TTM) shows operating profit as a share of sales over the last four quarters.",
    "revenue_growth_yoy_pct": "Revenue growth YoY (quarter) shows how fast sales grew vs the same quarter last year.",
    "net_debt_to_ebitda": "Net debt / EBITDA uses Yahoo balance-sheet debt/cash and EBITDA — periods may differ.",
    "fcf_margin_pct": "FCF margin shows free cash left from each dollar of revenue after running the business.",
}

METRIC_GLOSS = {
    "forward_pe": "Price vs expected next-year earnings",
    "ebit_margin_pct": "Operating profit as share of sales (TTM)",
    "revenue_growth_yoy_pct": "Sales growth vs same quarter last year",
    "net_debt_to_ebitda": "Net debt vs Yahoo EBITDA",
    "fcf_margin_pct": "Free cash left from each sales dollar (latest annual statements)",
}

METRIC_ANALOGY = {
    "forward_pe": (
        "Think payback time: how many years of expected earnings are priced into one share today."
    ),
    "ebit_margin_pct": (
        "For every dollar of sales, this is the slice kept as operating profit before interest and taxes."
    ),
    "revenue_growth_yoy_pct": (
        "Compared with a year ago — is the business growing, flat, or shrinking?"
    ),
    "net_debt_to_ebitda": (
        "If operating profit stayed steady, about how many years to repay net debt from cash generation?"
    ),
    "fcf_margin_pct": (
        "After running the business, how much cash is left from each sales dollar — not the same as accounting profit."
    ),
}

METRIC_LEARN = {
    "forward_pe": (
        "P/E (price-to-earnings) divides the share price by earnings per share. "
        "Forward P/E uses analyst estimates for next year's earnings, not last year's results. "
        "A higher number often means investors expect faster growth — or are paying a premium today."
    ),
    "ebit_margin_pct": (
        "This card sums Operating Income and Total Revenue from the last four quarterly "
        "financial statements, then divides — a trailing twelve-month (TTM) operating margin. "
        "It is not Yahoo's single-quarter operatingMargins snapshot."
    ),
    "revenue_growth_yoy_pct": (
        "Year-over-year (YoY) growth compares revenue in the latest reported quarter with the "
        "same quarter one year ago (Yahoo revenueGrowth). One quarter can be noisy — look for a "
        "pattern over time when you dig deeper."
    ),
    "net_debt_to_ebitda": (
        "Net debt is total debt minus cash on hand (Yahoo). EBITDA is Yahoo's reported EBITDA figure — "
        "often trailing, not necessarily matched to the same instant as the balance sheet. "
        "Use this as a rough leverage signal, not a precise accounting ratio."
    ),
    "fcf_margin_pct": (
        "Free cash flow (FCF) is cash left after running and investing in the business. "
        "This card computes FCF margin from the latest annual cash flow and income statements — "
        "not Yahoo's trailing Key Statistics ratio. Run the metric audit script to compare."
    ),
}

METRIC_LABELS = {
    "forward_pe": "Forward P/E",
    "ebit_margin_pct": "Operating margin (TTM)",
    "revenue_growth_yoy_pct": "Rev growth YoY (quarter)",
    "net_debt_to_ebitda": "Net debt / EBITDA",
    "fcf_margin_pct": "FCF margin (annual)",
}

ALL_METRICS = (
    "forward_pe",
    "ebit_margin_pct",
    "revenue_growth_yoy_pct",
    "net_debt_to_ebitda",
    "fcf_margin_pct",
)

VISIBLE_METRICS = (
    "forward_pe",
    "ebit_margin_pct",
    "revenue_growth_yoy_pct",
)
DEEP_DIVE_METRICS = (
    "net_debt_to_ebitda",
    "fcf_margin_pct",
)

BENCHMARK_METRICS = (
    ("forward_pe", "sector_median_forward_pe", "lower"),
    ("ebit_margin_pct", "sector_median_ebit_margin_pct", "higher"),
    ("revenue_growth_yoy_pct", "sector_median_revenue_growth_yoy_pct", "higher"),
    ("net_debt_to_ebitda", "sector_median_net_debt_to_ebitda", "lower"),
    ("fcf_margin_pct", "sector_median_fcf_margin_pct", "higher"),
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
    "Median = the middle value among eligible companies in this sector and market. "
    "↑ higher than median · ↓ lower than median · → at median."
)

BENCHMARK_UNAVAILABLE = "Comparison unavailable (small sector)"


def _benchmark_eligible(card: dict) -> bool:
    peer_count = card.get("sector_peer_count")
    return peer_count is not None and peer_count >= PEER_THRESHOLD


def benchmark_unavailable_line(card: dict) -> str | None:
    peer_count = card.get("sector_peer_count")
    if peer_count is None:
        return None
    if peer_count < PEER_THRESHOLD:
        return BENCHMARK_UNAVAILABLE
    return None


def benchmark_compare_available(card: dict) -> bool:
    return _benchmark_eligible(card)


def sector_headline(card: dict) -> str:
    """Sector label with peer count when available (north_star)."""
    sector = card.get("sector") or "Unknown sector"
    peer_count = card.get("sector_peer_count")
    if peer_count is not None:
        return f"{sector} ({peer_count} companies)"
    return sector


def metric_gloss(metric: str, value: float | None) -> str:
    """Card-face gloss; value-aware where the story depends on the number."""
    if metric == "net_debt_to_ebitda" and value is not None and value < 0:
        return "Net cash — cash on hand exceeds debt"
    return METRIC_GLOSS[metric]


def metric_analogy(metric: str, value: float | None) -> str:
    if metric == "net_debt_to_ebitda" and value is not None and value < 0:
        return (
            "Cash on the balance sheet exceeds debt — a net cash position, "
            "not leverage to repay."
        )
    return METRIC_ANALOGY[metric]


def metric_learn_text(metric: str, value: float | None) -> str:
    if metric == "net_debt_to_ebitda" and value is not None and value < 0:
        return (
            "Net debt is total debt minus cash. When cash exceeds debt, the ratio "
            "is negative — a net cash position. Yahoo's EBITDA is still in the "
            "denominator; read the sign as cash vs debt, not years to repay."
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


def format_metric_value(metric: str, value: float | None) -> str:
    if value is None:
        return "—"
    if metric in ("ebit_margin_pct", "revenue_growth_yoy_pct", "fcf_margin_pct"):
        return f"{value:.1f}%"
    if metric == "forward_pe":
        return f"{value:.1f}"
    return f"{value:.2f}"


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


BUSINESS_SUMMARY_PREVIEW_CHARS = 120

STALE_SNAPSHOT_DAYS = 7


def business_summary_preview(card: dict) -> str | None:
    raw = card.get("business_summary")
    if raw is None:
        return None
    text = str(raw).strip()
    if not text:
        return None
    if len(text) <= BUSINESS_SUMMARY_PREVIEW_CHARS:
        return text
    return text[:BUSINESS_SUMMARY_PREVIEW_CHARS].rstrip() + "…"


def business_summary_full(card: dict) -> str | None:
    raw = card.get("business_summary")
    if raw is None:
        return None
    text = str(raw).strip()
    return text or None
