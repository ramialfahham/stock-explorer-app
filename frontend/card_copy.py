"""Plain-language metric lines for beginners (north_star)."""

METRIC_HELP = {
    "forward_pe": "Forward P/E compares today's share price to expected earnings over the next year.",
    "ebit_margin_pct": "EBIT margin shows how much profit the company keeps from sales before interest and taxes.",
    "revenue_growth_yoy_pct": "Revenue growth YoY shows how fast sales grew compared with a year ago.",
    "net_debt_to_ebitda": "Net debt / EBITDA shows how many years of operating profit would repay net debt.",
    "fcf_margin_pct": "FCF margin shows free cash left from each dollar of revenue after running the business.",
}

METRIC_LABELS = {
    "forward_pe": "Forward P/E",
    "ebit_margin_pct": "EBIT margin",
    "revenue_growth_yoy_pct": "Revenue growth (YoY)",
    "net_debt_to_ebitda": "Net debt / EBITDA",
    "fcf_margin_pct": "FCF margin",
}

BENCHMARK_METRICS = (
    ("forward_pe", "sector_median_forward_pe", "lower"),
    ("ebit_margin_pct", "sector_median_ebit_margin_pct", "higher"),
    ("revenue_growth_yoy_pct", "sector_median_revenue_growth_yoy_pct", "higher"),
    ("net_debt_to_ebitda", "sector_median_net_debt_to_ebitda", "lower"),
    ("fcf_margin_pct", "sector_median_fcf_margin_pct", "higher"),
)

PEER_THRESHOLD = 8


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
    if direction == "higher":
        word = "above" if value >= median else "below"
    else:
        word = "below" if value <= median else "above"
    sector = card.get("sector") or "sector"
    return f"{word} {sector} median ({peer_count} companies)"
