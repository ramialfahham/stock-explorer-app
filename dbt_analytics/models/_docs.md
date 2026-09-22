{% docs card_eligibility %}

A ticker is **card-eligible** when its `company_type`'s required metrics are all non-null. The
required set is per company type (the Sector/Lifecycle Router):

- **operating** -- all four discovery metrics:
  1. `ebit_margin_pct` -- TTM sum of four quarterly Operating Income / Total Revenue × 100
  2. `revenue_growth_yoy_pct` -- `revenueGrowth × 100`
  3. `net_debt_to_ebitda` -- `netDebt / ebitda` (both required; no statement fallback)
  4. `fcf_margin_pct` -- latest annual `Free Cash Flow / Total Revenue × 100`
- **financial**: the pair `statement_roe_pct` + `net_margin_pct` (the operating metrics are
  dropped by classification, not because they cannot be fetched; see `docs/data_contract.md`).
- **pre_revenue** -- `net_cash` (cash minus total debt; the operating metrics break for revenue ≤ 0).

`forward_pe` left the operating and financial sets, and pre_revenue moved off
`net_cash_to_market_cap`, when all three price-carrying metrics were dropped from the
catalogue. A card must not be gated on a metric it does not display. Both changes WIDEN
eligibility: no forward P/E is required, and a pre-revenue company no longer needs a market cap.

Missing any required metric excludes the ticker from the Streamlit discover pool.
See `docs/data_contract.md` for the canonical per-type definition.

{% enddocs %}

{% docs card_metrics %}

Metrics power the stock swipe card, grouped by analytical lens (valuation → profitability →
growth → solvency → liquidity → cash → returns) and varying by company type. All are computed
in `int_stock__card_metrics` from the latest fundamentals snapshot and constituent dimension.
No fallbacks (e.g. ROIC) when a primary Yahoo field is null.

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
