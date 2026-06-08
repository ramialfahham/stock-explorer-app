{% docs card_eligibility %}

A ticker is **card-eligible** when all five discovery metrics are non-null:

1. `forward_pe` — Yahoo `forwardPE`
2. `ebit_margin_pct` — TTM sum of four quarterly Operating Income / Total Revenue × 100
3. `revenue_growth_yoy_pct` — `revenueGrowth × 100`
4. `net_debt_to_ebitda` — `netDebt / ebitda` (both required; no statement fallback)
5. `fcf_margin_pct` — latest annual `Free Cash Flow / Total Revenue × 100`

Missing any metric excludes the ticker from the Streamlit discovery queue. See `docs/data_contract.md`.

{% enddocs %}

{% docs card_metrics %}

Five metrics power the stock swipe card (valuation → quality → momentum → solvency → cash).
All are computed in `int_stock__card_metrics` from the latest fundamentals snapshot and
constituent dimension. No fallbacks (e.g. ROIC) when a primary Yahoo field is null.

{% enddocs %}

{% docs sector_benchmarks %}

Sector medians are computed per `(market_code, sector)` over **card-eligible** tickers only.
If `sector_peer_count` is below 8, median columns are null and the UI omits benchmark lines.
Benchmark availability does not change eligibility.

{% enddocs %}

{% docs mart_stock_cards %}

Consumption mart for Supabase export and Streamlit. One row per ticker per fundamentals
snapshot, with card metrics, eligibility flag, and optional sector benchmark columns.

{% enddocs %}
