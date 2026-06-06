"""Plain-language metric lines for beginners (north_star)."""

from datetime import date

METRIC_HELP = {
    "forward_pe": "Forward P/E compares today's share price to expected earnings over the next year.",
    "ebit_margin_pct": "EBIT margin shows how much profit the company keeps from sales before interest and taxes.",
    "revenue_growth_yoy_pct": "Revenue growth YoY shows how fast sales grew compared with a year ago.",
    "net_debt_to_ebitda": "Net debt / EBITDA shows how many years of operating profit would repay net debt.",
    "fcf_margin_pct": "FCF margin shows free cash left from each dollar of revenue after running the business.",
}

METRIC_LEARN = {
    "forward_pe": (
        "P/E (price-to-earnings) divides the share price by earnings per share. "
        "Forward P/E uses analyst estimates for next year's earnings, not last year's results. "
        "A higher number often means investors expect faster growth — or are paying a premium today."
    ),
    "ebit_margin_pct": (
        "EBIT is profit from core operations before interest and taxes. "
        "EBIT margin expresses that profit as a share of revenue — it shows how efficiently a company "
        "turns sales into operating profit."
    ),
    "revenue_growth_yoy_pct": (
        "Year-over-year (YoY) growth compares revenue today with the same period one year ago. "
        "It helps you see whether a company is expanding, flat, or shrinking. "
        "One quarter can be noisy — look for a pattern over time when you dig deeper."
    ),
    "net_debt_to_ebitda": (
        "Net debt is total debt minus cash on hand. EBITDA is a rough measure of operating cash "
        "generation before interest, taxes, and non-cash charges. "
        "Dividing net debt by EBITDA estimates how many years of operating profit would repay the debt."
    ),
    "fcf_margin_pct": (
        "Free cash flow (FCF) is cash left after running and investing in the business. "
        "FCF margin shows that cash as a percentage of revenue. "
        "It hints at whether a company can fund dividends, buybacks, or growth without borrowing more."
    ),
}

METRIC_LABELS = {
    "forward_pe": "Forward P/E",
    "ebit_margin_pct": "EBIT margin",
    "revenue_growth_yoy_pct": "Revenue growth (YoY)",
    "net_debt_to_ebitda": "Net debt / EBITDA",
    "fcf_margin_pct": "FCF margin",
}

# north_star: top three on the card; leverage and FCF in deep dive.
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
    return f"Fundamentals as of {formatted}"


def format_metric_value(metric: str, value: float | None) -> str:
    if value is None:
        return "—"
    if metric in ("ebit_margin_pct", "revenue_growth_yoy_pct", "fcf_margin_pct"):
        return f"{value:.1f}%"
    if metric == "forward_pe":
        return f"{value:.1f}"
    return f"{value:.2f}"


def benchmark_line(card: dict, metric: str, median_key: str, direction: str) -> str | None:
    peer_count = card.get("sector_peer_count")
    if peer_count is None or peer_count < PEER_THRESHOLD:
        return None
    value = card.get(metric)
    median = card.get(median_key)
    if value is None or median is None:
        return None
    median_fmt = format_metric_value(metric, median)
    if direction == "higher":
        word = "above" if value >= median else "below"
    else:
        word = "below" if value <= median else "above"
    sector = card.get("sector") or "sector"
    return f"{word.capitalize()} the {sector} median ({median_fmt}, {peer_count} peers in this app)"
