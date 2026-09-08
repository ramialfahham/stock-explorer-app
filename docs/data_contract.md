# Data contract — Stock Swipe App

Grains, freshness, completeness, and export shape. Ingestion lands **raw fields only**;
dbt computes metrics and eligibility. See [`layering.md`](layering.md) for layer rules.

---

## Partition key

All market-scoped data uses **`market_code`** from [`market_registry.yml`](market_registry.yml).
Never hardcode market identifiers in business logic.

---

## Constituent seeds

| Property | Value |
|----------|--------|
| Path | `storage/seeds/{market_code}/constituents.csv` |
| Grain | One row per `(market_code, ticker)` |
| Columns | `market_code`, `ticker`, `company_name`, `refreshed_at`, `source` |
| Refresh | `scripts/refresh_constituents.py` per [`constituent_sources.yml`](constituent_sources.yml) |

**Hybrid model:** committed seeds are source of truth for ingestion; refresh updates seeds
from Wikipedia or manual import.

---

## Raw parquet (ingestion output)

Base path: `storage/raw/{market_code}/` (dbt var `raw_path`, default `../storage/raw`).

### Current (Phase B baseline)

| File | Grain | Notes |
|------|-------|-------|
| `yf_constituents.parquet` | One row per ticker | Joined from seeds at ingest time |
| `yf_daily_prices.parquet` | One row per `(ticker, trade_date)` | OHLCV; not shown on discovery card |

### Planned (fundamentals)

| File | Grain | Notes |
|------|-------|-------|
| `yf_fundamentals.parquet` | One row per `(ticker, snapshot_date)` | Raw `ticker.info` + statement fields from yfinance only |

**Rule:** Python ingestion writes provider fields as-is. No derived ratios in ingestion.

---

## yfinance raw field mapping

Ingestion calls `yf.Ticker(yf_symbol)` per constituent. Land **raw columns** below into
`yf_fundamentals.parquet`. dbt computes card metrics and eligibility — never in Python.

Metrics are ordered by **analytical relevance** (valuation → profitability → growth → solvency → cash).

### From `ticker.info`

| Raw column (parquet) | yfinance key | Card metric (dbt) |
|----------------------|--------------|-------------------|
| `info_forward_pe` | `forwardPE` | `forward_pe` |
| `info_operating_margins` | `operatingMargins` | Audit only — not used for card metric |
| `info_revenue_growth` | `revenueGrowth` | `revenue_growth_yoy_pct` |
| `info_net_debt` | `netDebt` | `net_debt_to_ebitda` (numerator, when present) |
| `info_total_debt` | `totalDebt` | Used with `info_total_cash` when `netDebt` is null |
| `info_total_cash` | `totalCash` | Used with `info_total_debt` when `netDebt` is null |
| `info_ebitda` | `ebitda` | `net_debt_to_ebitda` (denominator) |
| `info_return_on_equity` | `returnOnEquity` | `roe_pct` (data-only; computed in dbt, not yet carded/exported) |
| `info_current_ratio` | `currentRatio` | `current_ratio` (data-only) |
| `info_price_to_book` | `priceToBook` | `price_to_book` (data-only) |
| `info_price_to_sales` | `priceToSalesTrailing12Months` | `price_to_sales` (data-only) |
| `info_ev_to_ebitda` | `enterpriseToEbitda` | `ev_to_ebitda` (data-only) |
| `info_free_cashflow` | `freeCashflow` | `fcf_yield_pct` numerator (data-only) |
| `info_market_cap` | `marketCap` | `fcf_yield_pct` denominator (data-only) |
| `info_dividend_yield` | `dividendYield` | Dividend yield, USUALLY already in percent (0.94 = 0.94%), but some rows arrive fraction-scale: issue #10 (data-only) |
| `info_payout_ratio` | `payoutRatio` | Payout ratio, decimal (data-only) |
| `info_sector` | `sector` | Sector grouping / benchmarks |
| `info_currency` | `currency` | Export display |
| `info_long_name` | `longName` | Company name fallback |
| `info_business_summary` | `longBusinessSummary` | Company description on card (nullable) |

Store `info_*` values exactly as returned (`null` if missing). Do not coerce types beyond
safe numeric parsing for parquet.

**Decimals → percent:** `revenueGrowth` is a decimal (e.g. `0.12` = 12%); dbt multiplies by 100
for `revenue_growth_yoy_pct`. Operating margin is computed as a percent in dbt from quarterly
statement sums.

### From financial statements

Use the **latest annual fiscal period** (most recent column) from:

- `ticker.income_stmt` (or `ticker.financials`)
- `ticker.cashflow`

| Raw column (parquet) | Statement row label | Statement |
|----------------------|----------------------|-----------|
| `stmt_total_revenue` | `Total Revenue` | income_stmt |
| `stmt_free_cash_flow` | `Free Cash Flow` | cashflow |
| `stmt_operating_cash_flow` | `Operating Cash Flow` | cashflow |
| `stmt_capital_expenditure` | `Capital Expenditure` (negative = outflow) | cashflow |
| `stmt_interest_expense` | `Interest Expense` (positive magnitude) | income_stmt |
| `stmt_net_income` | `Net Income` | income_stmt |
| `stmt_net_income_common` | `Net Income Common Stockholders` (after minority interest & preferred dividends) | income_stmt |
| `qtr_operating_income_0` … `_3` | Operating-profit row (fallback labels) | quarterly_income_stmt |
| `qtr_total_revenue_0` … `_3` | `Total Revenue` | quarterly_income_stmt |
| `qtr_operating_revenue_0` … `_3` | `Operating Revenue` | quarterly (UK banks) |
| `qtr_operating_expense_0` … `_3` | `Operating Expense` | quarterly (UK banks) |
| `stmt_operating_income` | Operating-profit row (fallback labels) | income_stmt |
| `stmt_operating_revenue` | `Operating Revenue` | income_stmt |
| `stmt_operating_expense` | `Operating Expense` | income_stmt |
| `stmt_fiscal_period_end` | column date | metadata |

Also persist `stmt_currency` if available on the statement object.

These fields feed **FCF margin** in dbt only. Do not compute ratios in ingestion.

**Sign conventions & derived FCF (for downstream dbt, not computed here):** `stmt_capital_expenditure`
is **negative** (a cash outflow), so a computed free cash flow is `stmt_operating_cash_flow +
stmt_capital_expenditure` — a distinct, transparent FCF source from the pre-computed `stmt_free_cash_flow`
row and the `info_free_cashflow` scalar. `stmt_interest_expense` is landed as a **positive** magnitude.

### From the balance sheet

Point-in-time (a stock, not a flow), so use the **latest annual column** from
`ticker.balance_sheet` — no TTM summing. yfinance canonicalises row labels to a fixed key set, so one
label per line resolves across markets (only equity keeps a second real fallback; see
[`intl-balance-sheet-row-labels.md`](intl-balance-sheet-row-labels.md)).
Landed as raw inputs for the Sector/Lifecycle Router to compute statement-based metrics
(debt-to-equity, current ratio, working capital, tangible-book valuation, net cash, ROA). The raw
columns themselves are not catalogued or exported; their derived metrics are catalogued and exported
per company type (see the `metric_catalogue` seed).

| Raw column (parquet) | Statement row label (first-match fallback) | Statement |
|----------------------|---------------------------------------------|-----------|
| `stmt_stockholders_equity` | `Stockholders Equity` → `Common Stock Equity` (common equity attributable to the parent; excludes minority interest) | balance_sheet |
| `stmt_total_debt` | `Total Debt` | balance_sheet |
| `stmt_current_assets` | `Current Assets` | balance_sheet |
| `stmt_current_liabilities` | `Current Liabilities` | balance_sheet |
| `stmt_cash_and_equivalents` | `Cash And Cash Equivalents` (narrow; excludes short-term investments) | balance_sheet |
| `stmt_tangible_book_value` | `Tangible Book Value` | balance_sheet |
| `stmt_total_assets` | `Total Assets` | balance_sheet |

Nullable — e.g. financials have no current/non-current split, so `stmt_current_assets` /
`stmt_current_liabilities` are null for banks. Not clipped.

### Card metrics — dbt formulas (v1)

> **Single source of truth:** each metric's definition — formula spec, label, `format`, `perspective`,
> `direction`, tier/order, the analytical definition (`calculation` / `interpretation` /
> `applicability`), and plain-language copy — lives in the [`metric_catalogue` seed](../dbt_analytics/seeds/metric_catalogue.csv)
> (see [`metric_layer.md`](metric_layer.md)). The table below is the computed reference; the seed is
> authoritative for display, labels, and format, and the frontend reads `frontend/metrics.json`
> (generated from it). `int_stock__card_metrics` is where the metrics are computed, once.

| # | Card metric | Formula | Primary inputs |
|---|-------------|---------|----------------|
| 1 | `forward_pe` | `info_forward_pe` (**no longer catalogued** — still computed and stored, no card renders it) | `ticker.info` |
| 2 | `ebit_margin_pct` | TTM: `sum(eff_op_0..3) / sum(qtr_total_revenue_0..3) * 100`; else annual `eff_stmt_op / stmt_total_revenue * 100` | quarterly + annual income_stmt |
| 3 | `revenue_growth_yoy_pct` | `info_revenue_growth * 100` | `ticker.info` |
| 4 | `net_debt_to_ebitda` | `coalesce(info_net_debt, info_total_debt - info_total_cash) / info_ebitda` | `ticker.info` |
| 5 | `fcf_margin_pct` | `stmt_free_cash_flow / stmt_total_revenue * 100` | cashflow + income_stmt |

**Additional computed metrics — formula reference:** computed once in `int_stock__card_metrics`. The
authoritative display definitions live in the [`metric_catalogue` seed](../dbt_analytics/seeds/metric_catalogue.csv);
many of the below are now catalogued and exported per company type by the Sector/Lifecycle Router (the
operating solvency/returns set, the bank set, and the pre-revenue survival set), while several remain
data-only intermediates (the info-scalar duplicates, `interest_coverage`, `computed_fcf`, and
`net_cash_to_ev`). Nullable; not clipped.

- `roe_pct` = `info_return_on_equity * 100` (Yahoo `returnOnEquity`); may be negative (loss-makers).
- `current_ratio` = `info_current_ratio` (Yahoo `currentRatio`).
- `price_to_book` = `info_price_to_book` (Yahoo `priceToBook`).
- `price_to_sales` = `info_price_to_sales` (Yahoo `priceToSalesTrailing12Months`).
- `ev_to_ebitda` = `info_ev_to_ebitda` (Yahoo `enterpriseToEbitda`).
- `fcf_yield_pct` = `info_free_cashflow / info_market_cap * 100` (Yahoo `freeCashflow` ÷ `marketCap`). Uses
  Yahoo's trailing free cash flow — distinct from the annual `stmt_free_cash_flow` used by `fcf_margin_pct`
  — so the cash figure matches the period of the current `marketCap` denominator.
- `debt_to_equity` = `stmt_total_debt / stmt_stockholders_equity` (statement-based; equity excludes minority interest; guarded on zero equity).
- `interest_coverage` = `eff_stmt_op / abs(stmt_interest_expense)` (operating income over interest; `abs()` defends the landed sign).
- `current_ratio_stmt` = `stmt_current_assets / stmt_current_liabilities` (statement-based; coexists with the info-scalar `current_ratio`; null for financials).
- `working_capital` = `stmt_current_assets - stmt_current_liabilities` (currency level; null for financials).
- `price_to_tangible_book` = `info_market_cap / stmt_tangible_book_value` (both totals; guarded on tangible book > 0). **No longer catalogued** — computed and stored, but no card renders it.
- `net_margin_pct` = `stmt_net_income / stmt_total_revenue * 100`.
- `roa_pct` = `stmt_net_income / stmt_total_assets * 100` (total net income over total assets; leverage-neutral).
- `statement_roe_pct` = `stmt_net_income_common / stmt_stockholders_equity * 100` (common income over common equity — both exclude minority interest; coexists with the info-scalar `roe_pct`).
- `dividend_yield_pct` = `info_dividend_yield` (Yahoo `dividendYield`, no x100). Yahoo returns this as a
  percent for MOST rows (0.94 = 0.94%) but not all: production holds fraction-scale rows too, so do not
  treat the passthrough as unconditionally safe. See issue #10. **No longer catalogued**: computed and
  stored, but no card renders it.
- `net_cash` = `stmt_cash_and_equivalents - stmt_total_debt` (a money amount in the company's reporting currency). Pre-revenue card metric; replaced `net_cash_to_market_cap` because that ratio divided by market cap and therefore moved with the share price, which a twice-monthly pipeline cannot keep current.
- `computed_fcf` = `stmt_operating_cash_flow + stmt_capital_expenditure` (capex negative; a transparent FCF distinct from `stmt_free_cash_flow` / `info_free_cashflow`; the burn basis for cash runway).
- `cash_runway_months` = `stmt_cash_and_equivalents / (-computed_fcf) * 12` when `computed_fcf < 0` (null when not burning).
- `burn_rate_monthly` = `-computed_fcf / 12` when `computed_fcf < 0` (null when not burning).
- `net_cash_to_ev` = `(stmt_cash_and_equivalents - stmt_total_debt) / (info_market_cap + stmt_total_debt - stmt_cash_and_equivalents)` (guarded on zero EV).

**Company-type classification:** `company_type` is computed once in `int_stock__card_metrics`,
alongside the metrics, to label each snapshot for the Sector/Lifecycle Router. It is not itself a
catalogued metric (not in the `metric_catalogue` or `frontend/metrics.json`), but it **drives the
per-type `is_card_eligible` branch** (the `CASE company_type` switch key) and **is exported to
Supabase**. Always non-null — evaluated in order, first match wins:

1. `financial` — when `coalesce(info_sector, dim_stock.sector) = 'Financial Services'`.
2. `pre_revenue` — else when `stmt_total_revenue` is present and `<= 0`, **or** when it's positive
   but under 0.1% of `info_market_cap` (revenue negligible relative to valuation — e.g. a
   development-stage miner/biotech the strict `<= 0` test alone misses; a ratio, not an absolute
   currency floor, since this app spans 6 currencies with no FX normalization in the pipeline).
   Real example: Deep Yellow (ASX: DYL) — $15,949 revenue against a $1.7B market cap (~0.001%).
3. `operating` — else (the default). A **null** `stmt_total_revenue`, or a positive-but-negligible
   `stmt_total_revenue` with no `info_market_cap` to compare it against, is treated as a data gap
   and stays `operating`, not `pre_revenue`.

`financial` takes precedence over `pre_revenue`. `company_type` drives the per-type metric sets,
eligibility, and card display (the Sector/Lifecycle Router).

**Operating margin:** prefer TTM — sum four quarters of operating profit and **Total Revenue**
from `quarterly_income_stmt`. Operating profit coalesces Yahoo row-label fallbacks (see
`docs/intl-quarterly-row-labels.md`) and **Operating Revenue − Operating Expense** when needed.
When four quarters are incomplete, use latest annual operating profit / annual total revenue.
`ebit_margin_basis` records `ttm_quarterly` vs `annual_latest`. `info_operating_margins` is
audit-only.

**Net debt / EBITDA:** dbt uses `coalesce(info_net_debt, info_total_debt - info_total_cash)` as the
numerator when `info_ebitda` is non-null and non-zero. If both `netDebt` and the debt/cash pair
are missing, `net_debt_to_ebitda` is null → ineligible. Do not rebuild EBITDA from statements in v1.

**No fallbacks:** if the primary field for a metric is null, the ticker is ineligible — do not
substitute ROE, ROA, or hand-built ROIC.

---

## Card eligibility (dbt)

`is_card_eligible` uses **per-type required sets**, keyed on `company_type` (the Sector/Lifecycle Router):

- **operating** — all four of `ebit_margin_pct`, `revenue_growth_yoy_pct`,
  `net_debt_to_ebitda`, `fcf_margin_pct` non-null.
- **financial** — `statement_roe_pct`, `net_margin_pct` non-null (the operating
  solvency/cash metrics are unsourceable for banks).
- **pre_revenue** — `net_cash` non-null, i.e. cash and total debt are both present (the
  operating metrics break for revenue ≤ 0, and for positive-but-negligible revenue).

`forward_pe` was dropped from the operating and financial sets, and
pre_revenue moved from `net_cash_to_market_cap` to `net_cash`. A card must not be gated on a
metric it does not display, and all three price-carrying metrics were removed from the
catalogue (see below). The practical effect is that **more companies qualify**: eligibility
no longer requires a forward P/E, nor a market cap for a pre-revenue company.

Missing any required metric → excluded from the discover pool.

**`missing_metrics`** (DuckDB-only, on `int_stock__card_metrics` and `mart_stock_eligibility_gaps`):
VARCHAR list of the `company_type`'s required metric column names that are null for that snapshot.
Empty when eligible. Used for pipeline QA — **not** exported to Supabase.

Field-level mapping and dbt formulas: **§ yfinance raw field mapping** above.

---

## Sector benchmarks (dbt → export)

Computed per `(market_code, sector)` over **card-eligible** tickers in that market:

| Output | Description |
|--------|-------------|
| `sector_peer_count` | Count of eligible peers in sector |
| `sector_median_*` | Median for each benchmarked metric (9; forward_pe is no longer one) |
| `sector_min_*` | Minimum for each benchmarked metric (card range mark) |
| `sector_max_*` | Maximum for each benchmarked metric (card range mark) |
| `sector_q1_*` / `sector_q3_*` | 25th/75th percentile for each benchmarked metric (outlier-aware range-mark display clamp, Gemini feedback point 5 -- see [`ui/card_metric_cell.md`](ui/card_metric_cell.md)'s "Range mark mechanics" for how these feed the clamp) |

Benchmarked: `ebit_margin_pct`, `net_debt_to_ebitda`, `fcf_margin_pct`, `debt_to_equity`,
`current_ratio_stmt` (operating-only); `net_margin_pct`, `roa_pct` (financial-only);
`revenue_growth_yoy_pct`, `statement_roe_pct` (both operating and financial). `debt_to_equity`
and `statement_roe_pct`'s benchmark aggregates exclude peers with negative stockholders' equity
(a sign-flipped ratio, not just an extreme one -- see `int_stock__sector_benchmarks.sql`'s own
comment). Pre-revenue's 4 metrics (`net_cash`, `working_capital`, `cash_runway_months`,
`burn_rate_monthly`) are deliberately excluded: only 3 pre-revenue companies exist app-wide,
which can never clear the 8-peer rendering threshold (see "Peer threshold" below).

**Peer threshold:** if `sector_peer_count < 8`, export `null` medians/min/max/quartiles; UI omits benchmark line.

Benchmark availability does **not** affect `is_card_eligible`.

---

## Freshness

| Layer | Cadence | Owner |
|-------|---------|-------|
| Constituents | On demand / when index changes | `refresh_constituents.py` |
| Fundamentals | **Every two weeks** (or on statement refresh) | GitLab CI `data-pipeline` job |
| Daily prices | Every two weeks or daily (supporting only) | Same pipeline |
| Supabase export | After successful dbt build | `export_to_supabase.py` |
| News (Phase 2) | Daily | Separate workflow |

**Stale export policy:** if the scheduled pipeline run fails the completeness gate, **keep
last good Supabase snapshot**; do not truncate to empty.

**Checked by `dbt source freshness`** (`data-pipeline` job, before `dbt build`; also run in
`validate:full` on every merge request, against CI fixture data, to catch a broken freshness
query itself before it ever reaches production -- fixture data is always fresh, so that run
proves the query still parses and references real columns, not that staleness detection
works). All three raw tables covered, using each table's own real ingest timestamp
(`ingested_at` on constituents and daily prices, `snapshot_date` on fundamentals -- daily
prices gained an `ingested_at` column, stamped once per yfinance download batch, specifically
so this check could cover it too). Warn at 20 days, error at 30 days -- sized against the real
schedule's worst-case gap (up to 17 days in a long month), not the rounded "every two weeks"
above.

**Table-level, not per-market:** each `loaded_at_query` takes `MAX(...)` over the union of
every active market's raw file, so this check passes as long as ANY one active market has a
recent ingest timestamp, even if a specific other market's ingestion has been silently broken
since before the current warn/error window. It catches "the whole pipeline stopped running,"
not "one market's ingestion quietly broke while the rest kept going." Per-market freshness
would need its own mechanism (e.g. a singular test grouping by `market_code`); not built here,
an owner-level scope call if this gap is ever worth closing.

**Local dev note:** a `storage/raw/` populated before daily prices gained `ingested_at` (i.e.
from before this column existed) will fail `stg_yf__daily_prices`'s new `not_null` test on that
column until re-ingested -- run ingestion fresh (or `--force-refetch`) for any market with
old-schema price parquet before running `dbt build` locally. Not a risk in CI or production:
`validate:full`'s fixtures always stamp `ingested_at`, and the scheduled pipeline job starts
from an empty `storage/raw/` every run (no cache/artifacts across jobs), so this mixed-schema
state can only arise in a local checkout that predates this change.

---

## Percent-scale passthrough guard

Three metrics pass a Yahoo `info` scalar through with a fixed multiplier, so their correctness
depends entirely on the provider's units staying put:

| Metric | Source scalar | Yahoo unit today | Model | A units flip makes it |
|--------|---------------|------------------|-------|-----------------------|
| `dividend_yield_pct` | `dividendYield` | percent | passthrough | **100x smaller** |
| `revenue_growth_yoy_pct` | `revenueGrowth` | fraction | x100 | **100x larger** |
| `roe_pct` | `returnOnEquity` | fraction | x100 | **100x larger** |

**The direction differs, which is why the guard is two-sided.** A percent source can only break
downward and a fraction source can only break upward; a one-sided floor would have been blind to
two of the three.

`dbt_analytics/tests/assert_percent_scale_passthroughs.sql` asserts the shape of each
distribution per market on `int_stock__card_metrics`, comparing the median absolute value
against a band:

| Metric | Band | Observed market medians, lowest to highest | Binding flip case against the band |
|--------|------|-------------------------------------------|------------------------------------|
| `dividend_yield_pct` | 0.5 to 50 | 1.81 (`us_sp500`) to 3.53 (`au_asx200`) | down to 0.035 (`au_asx200`), 14x below the floor |
| `revenue_growth_yoy_pct` | 1.0 to 100 | 4.50 (`fr_cac40`) to 12.00 (`jp_nikkei225`) | up to 450 (`fr_cac40`), 4.5x above the ceiling |
| `roe_pct` | 1.0 to 200 | proxy only: 9.31 to 23.72 | up to 931 (`jp_nikkei225`), 4.7x above the ceiling |

The flip column states the BINDING case: the market whose post-flip median lands nearest its
bound, which is where detection is weakest. Which market that is depends on the direction, and
the two are opposites. A percent source breaks DOWNWARD toward a floor, so dividing by 100
leaves the HIGHEST market nearest the floor (`au_asx200` 3.53 -> 0.035, only 14x clear, against
`us_sp500`'s 28x). A fraction source breaks UPWARD toward a ceiling, so multiplying by 100
leaves the LOWEST market nearest the ceiling (`fr_cac40` 4.50 -> 450, 4.5x clear, against
`jp_nikkei225`'s 12x). Quoting the other extreme in either case overstates the margin.

**What the observed figures are measured on.** They come from the exported Supabase mart, which
is eligible-only (`mart_stock_cards.sql` filters `where m.is_card_eligible`). The test reads
`int_stock__card_metrics`, a superset that also carries ineligible tickers.

The direction of that difference is NOT established. The ineligible population is precisely
what the export leaves behind, so no measurement of it exists here, and nothing in the repo
characterises its distribution. The margins above are what was measured on the eligible subset;
how closely they describe the tested population is unknown.

They were also measured on a population KNOWN to be contaminated, and for `dividend_yield_pct`
only: the mis-scaled rows of issue #10 are ~100x too small and sit at the bottom of that one
distribution. Nothing establishes contamination in `revenue_growth_yoy_pct` or `roe_pct`, whose
binding side is the ceiling in any case.

It cuts two ways, and the two must not be conflated. Contamination LOWERS the observed median.
That INFLATES the flip-detection margins quoted in the table above, because a lower median
divides to a lower post-flip value and so sits further below the floor: the 14x is marginally
optimistic (a clean median of 3.60 would give 13.9x). It simultaneously lowers the current
headroom between the median and the floor, which is the conservative direction. Neither effect
is material at these magnitudes.

The material risk is attribution. If the mis-scaled share grows, this guard eventually fires on
contamination while the tables above point whoever is debugging it at a provider units change.

`roe_pct` is not exported at all, so its band is set from `statement_roe_pct` as the closest
available proxy: pooled median absolute value 13.37, per-market medians 9.31 (`jp_nikkei225`) to
23.72 (`ch_smi`). The per-market range is what the band is derived from, since the test groups
by market. Stated rather than glossed, because the margins are the whole justification for the
bands.

**Population is payers only.** The test counts rows where the value is non-null and non-zero, so
"median" here means the median across companies that actually pay a dividend or report the
metric, not across all constituents. A dividend-suspension wave removes rows rather than
depressing the median.

**Why the median of the absolute value.** `revenue_growth_yoy_pct` and `roe_pct` are signed (14%
and 10% of rows are negative), so a signed median understates scale and would fall in a
recession, failing on correct data.

**Why per market.** A single market ingesting post-flip is caught. A pooled median is a majority
vote and would stay quiet until more than half the universe had flipped.

**The sample floor is 5** populated rows per market per metric. Below that a median cannot
support the assertion, so the guard stays silent rather than failing on thin data. In the
exported mart at the latest snapshot the smallest market, `ch_smi`, had 20 eligible rows and all
20 carried a dividend; CI fixtures give 6 per market. Both clear the floor, so the guard is
exercised rather than skipped in either environment.

**What this does NOT cover.** A metric going entirely null -- a provider dropping or renaming a
field, likelier than a units change -- passes having asserted nothing; that is a coverage
assertion, and the project has no `accepted_range` or fill-rate tests anywhere. Nor does a
market-median guard see per-row mixed units, which production currently has (issue #10).

---

## Completeness gates

Run on **scheduled pipeline** (Tier C), not on every PR. Implemented by
`scripts/check_pipeline_completeness.py`.

### Per active market (`ingest_active: true`)

| Check | Fail | Warn |
|-------|------|------|
| Constituent seed exists | 0 rows in seed CSV | — |
| Raw fundamentals parquet exists | File missing after ingest | — |
| Card-eligible count | **< 5** tickers | **< 20** tickers |

Warn exits 0; fail exits 1 and blocks export.

### Registry

`scripts/check_registry_var_sync.py` ensures `dbt_project.yml` `active_market_codes` matches
registry `ingest_active: true` entries (CI on every PR).

---

## Supabase export — `mart_stock_cards`

Grain: one row per `(market_code, ticker, snapshot_date)`.

**Schema is dbt-contract-enforced** (`config: {contract: {enforced: true}}` in
`dbt_analytics/models/5_marts/_marts.yml`): `dbt build` fails if a column's name, type, or
count drifts from what's declared there. This guarantees the DuckDB mart matches its own
documented shape, on every merge request, before anything downstream ever sees a bad schema --
it does not auto-sync `scripts/export_to_supabase.py`'s separate `EXPORT_COLUMNS` allowlist or
the Postgres migration schema, which stay hand-maintained, separate surfaces the contract
cannot see.

| Column | Type | Notes |
|--------|------|-------|
| `market_code` | text | FK → `markets` |
| `ticker` | text | Provider symbol |
| `company_name` | text | |
| `sector` | text | |
| `currency` | text | |
| `business_summary` | text | Yahoo `longBusinessSummary`; nullable |
| `forward_pe` | numeric | Superseded; still computed and stored, no longer catalogued. |
| `ebit_margin_pct` | numeric | |
| `revenue_growth_yoy_pct` | numeric | |
| `net_debt_to_ebitda` | numeric | |
| `fcf_margin_pct` | numeric | |
| `debt_to_equity` | numeric | Operating-card solvency (statement-based); nullable. |
| `current_ratio_stmt` | numeric | Operating-card liquidity (statement-based); nullable, null for financials. |
| `statement_roe_pct` | numeric | Operating/financial-card returns (statement-based, period-end); nullable. |
| `price_to_tangible_book` | numeric | Superseded; still computed and stored, no longer catalogued. Nullable. |
| `net_margin_pct` | numeric | Financial-card profitability; nullable. |
| `roa_pct` | numeric | Financial-card returns (statement-based, period-end); nullable. |
| `dividend_yield_pct` | numeric | Superseded; still computed and stored, no longer catalogued. Nullable. |
| `net_cash_to_market_cap` | numeric | Superseded by `net_cash`; still computed and stored, no longer catalogued. Nullable. |
| `net_cash` | numeric | Pre-revenue-card cash metric (cash minus total debt, a money amount); nullable. |
| `working_capital` | numeric | Pre-revenue-card liquidity (current assets − liabilities, a currency amount); nullable. |
| `cash_runway_months` | numeric | Pre-revenue-card cash (months of cash left; null when not burning); nullable. |
| `burn_rate_monthly` | numeric | Pre-revenue-card cash (monthly burn, a currency amount; null when not burning); nullable. |
| `is_card_eligible` | boolean | |
| `company_type` | text | Sector/lifecycle class — `operating`, `financial`, or `pre_revenue`; always set (defaults to `operating`). Drives which metrics render per card type and selects the per-type eligibility branch behind `is_card_eligible`. |
| `sector_peer_count` | integer | |
| `sector_median_forward_pe` | numeric | nullable |
| `sector_median_ebit_margin_pct` | numeric | nullable |
| `sector_median_revenue_growth_yoy_pct` | numeric | nullable |
| `sector_median_net_debt_to_ebitda` | numeric | nullable |
| `sector_median_fcf_margin_pct` | numeric | nullable |
| `sector_median_debt_to_equity` | numeric | nullable |
| `sector_median_current_ratio_stmt` | numeric | nullable |
| `sector_median_statement_roe_pct` | numeric | nullable |
| `sector_median_net_margin_pct` | numeric | nullable |
| `sector_median_roa_pct` | numeric | nullable |
| `sector_min_forward_pe` | numeric | nullable |
| `sector_max_forward_pe` | numeric | nullable |
| `sector_min_ebit_margin_pct` | numeric | nullable |
| `sector_max_ebit_margin_pct` | numeric | nullable |
| `sector_min_revenue_growth_yoy_pct` | numeric | nullable |
| `sector_max_revenue_growth_yoy_pct` | numeric | nullable |
| `sector_min_net_debt_to_ebitda` | numeric | nullable |
| `sector_max_net_debt_to_ebitda` | numeric | nullable |
| `sector_min_fcf_margin_pct` | numeric | nullable |
| `sector_max_fcf_margin_pct` | numeric | nullable |
| `sector_min_debt_to_equity` | numeric | nullable |
| `sector_max_debt_to_equity` | numeric | nullable |
| `sector_min_current_ratio_stmt` | numeric | nullable |
| `sector_max_current_ratio_stmt` | numeric | nullable |
| `sector_min_statement_roe_pct` | numeric | nullable |
| `sector_max_statement_roe_pct` | numeric | nullable |
| `sector_min_net_margin_pct` | numeric | nullable |
| `sector_max_net_margin_pct` | numeric | nullable |
| `sector_min_roa_pct` | numeric | nullable |
| `sector_max_roa_pct` | numeric | nullable |
| `sector_q1_ebit_margin_pct` | numeric | nullable |
| `sector_q3_ebit_margin_pct` | numeric | nullable |
| `sector_q1_revenue_growth_yoy_pct` | numeric | nullable |
| `sector_q3_revenue_growth_yoy_pct` | numeric | nullable |
| `sector_q1_net_debt_to_ebitda` | numeric | nullable |
| `sector_q3_net_debt_to_ebitda` | numeric | nullable |
| `sector_q1_fcf_margin_pct` | numeric | nullable |
| `sector_q3_fcf_margin_pct` | numeric | nullable |
| `sector_q1_debt_to_equity` | numeric | nullable |
| `sector_q3_debt_to_equity` | numeric | nullable |
| `sector_q1_current_ratio_stmt` | numeric | nullable |
| `sector_q3_current_ratio_stmt` | numeric | nullable |
| `sector_q1_statement_roe_pct` | numeric | nullable |
| `sector_q3_statement_roe_pct` | numeric | nullable |
| `sector_q1_net_margin_pct` | numeric | nullable |
| `sector_q3_net_margin_pct` | numeric | nullable |
| `sector_q1_roa_pct` | numeric | nullable |
| `sector_q3_roa_pct` | numeric | nullable |
| `snapshot_date` | date | Fundamentals as-of date |
| `exported_at` | timestamptz | |

**Removed from v1 card contract:** `latest_price`, `price_change_1d_pct`, `price_change_5d_pct`,
and `roic` (see migration `002_fundamentals_mart.sql`).

---

## Supabase assessments — `card_assessments`

AI **health assessment** per card, written by `scripts/generate_assessments.py` after the mart export
(scheduled pipeline). Educational only — **not** investment advice. **Slice 5a** writes the deterministic
verdict + `input_hash`; **Slice 5b** fills `ai_read` / `read_model` with a **Claude Haiku**
(`claude-haiku-4-5`) prose read that reasons only from the card's own numbers and ends on the verdict's
meaning — regenerated only when `input_hash` changes or `ai_read` is null. The card renders it in **Slice 6**.

**Structured output + hallucination guard (Gemini feedback points 3/4).** The Haiku call forces
tool-use (`tool_choice`, `write_card_read`): the model returns `read` (the prose) plus
`referenced_metrics`, one `{label, value_as_shown}` entry per metric the read explicitly cites,
copied exactly as shown in the prompt's own facts block. `validate_read_metrics` checks each pair
against `_present_metric_renderings`, the same rendering the model was shown: a numeric
cross-check, not an LLM judge. It catches the model stating a number that does not match the
card's data, not an unsupported qualitative claim that cites no wrong number (an LLM-judge second
pass would catch that too, at roughly double the cost; not built here). Any mismatch, unknown
label, or malformed tool response fails exactly like an API exception already does: `ai_read` /
`read_model` stay absent, and the existing regenerate-on-`input_hash`-change path picks the card
up again next run. No retry, no separate failure state.

A deterministic style guard (`find_read_style_violations`, same file) runs after the numeric
guard and checks a subset of the system prompt's own rules that a plain string/regex check can
enforce without semantic judgment: no em/en-dash, no exclamation marks or emoji, no
investment-advice language, none of the prompt's own named AI-tell phrases, no "this
year"/"over the year" about growth, and the read must end on the verdict's meaning. Any
violation fails exactly the same way the numeric guard does -- fail closed, self-heals next
`input_hash` change, no retry.

When `ai_read` is absent (a brand-new card, a per-card API failure, a hallucination-guard
reject, or a style-guard reject), the card shows a deterministic,
non-AI one-line summary under its own "What the verdict means" heading instead of the AI-written
read (`frontend/card_copy.py`'s `VERDICT_FALLBACK_READ`), never AI-attributed, phrased as a
general summary rather than a description of the rules below since neither the decisive-vs-
supporting metric split nor the per-metric thresholds are shown anywhere on the card.

**Grain:** one row per `(market_code, ticker)` — latest snapshot only (differs from `mart_stock_cards`,
keyed on `(…, snapshot_date)`). Public-read RLS; service-role writes (migration `010_card_assessments.sql`).

| Column | Type | Notes |
|--------|------|-------|
| `market_code` | text | FK → `markets` |
| `ticker` | text | Provider symbol |
| `company_type` | text | `operating` / `financial` / `pre_revenue` |
| `health_verdict` | text | `green` \| `yellow` \| `red` (the frontend maps to 🟢/🟡/🔴 in Slice 6) |
| `ai_read` | text | Claude Haiku prose read (`claude-haiku-4-5`); educational, never advice; reasons only from the card's numbers |
| `read_model` | text | model id that wrote `ai_read` (from the Claude API response) |
| `input_hash` | text | sha256 of the verdict inputs plus the display currency; drives 5b regenerate-on-change |
| `snapshot_date` | date | the mart snapshot the assessment reflects |
| `generated_at` | timestamptz | last write |

**Verdict rules (deterministic, per `company_type`).** The color is decided by transparent rules — **not**
the LLM — and measures **financial health / resilience** on the card's own numbers.
Conservative — one serious weakness caps it:
- **operating** — leverage (`net_debt_to_ebitda`), profitability (`ebit_margin_pct`), cash (`fcf_margin_pct`);
  `debt_to_equity` / `current_ratio_stmt` / `statement_roe_pct` are supporting (tie-breakers).
- **Sign-inversion guards.** Three metrics can flip sign when a denominator goes negative, and
  banding the flipped value by raw magnitude used to read a distressed or thin-equity company as
  good on that axis (`docs/backlog/gemini_verdict_feedback.md` point 1 and its sibling-bug note).
  All three guards check the ratio's own raw denominator directly, not the ratio's sign:
  `net_debt_to_ebitda`'s sign alone cannot tell a genuine net-cash position apart from real debt
  divided by negative earnings, and `debt_to_equity`'s numerator (total debt) can be exactly
  zero, which divides out to a zero ratio regardless of equity's sign, so checking the ratio's
  own sign would miss a debt-free company with negative equity. `net_debt_to_ebitda` is banded
  `unknown` (not by magnitude) when `info_ebitda` is present and `<= 0`; `debt_to_equity` and
  `statement_roe_pct` are banded `weak` (not `unknown`, which would be a no-op on a supporting
  axis) when `stmt_stockholders_equity` is present and `<= 0`. Negative equity is not always
  distress by itself for an operating company (a healthy company's own buybacks can produce it
  too, per the metric catalogue's own applicability note), so `weak` there is deliberately the
  mildest band that still changes anything, a caution rather than a verdict on the cause, giving
  the same yellow-capping ceiling any other weak supporting axis already has, never forcing red
  on its own. All raw denominators are carried through the mart for exactly these checks and are
  not themselves displayed metrics.
- **`statement_roe_pct`'s guard bands `unknown`, not `weak`, on financial cards.** On `operating`
  it is a supporting axis, same treatment as `debt_to_equity` above (`weak`, capping at yellow).
  On `financial` it is effectively a core axis (`good` is required for green; only `weak` on this
  or `net_margin_pct` forces red), so the guard bands `unknown` instead: it blocks green (an
  `unknown` roe is never `good`) without forcing red on its own. This is a deliberate, narrower
  choice than a first version that banded `weak` (forcing red outright), reasoned from US bank
  capital regulation. Corrected in review: `company_type == 'financial'` is the whole GICS
  "Financial Services" sector (insurers, asset managers, broker-dealers, payment networks,
  exchanges, mortgage finance, not only depository banks), spans markets under entirely different
  regulatory regimes (this app covers US, UK, Japan, Australia, Germany, France, Netherlands,
  Switzerland, Spain), and includes firms known for the same benign buyback-driven negative
  equity operating companies can have. Nothing in the data distinguishes a bank in genuine
  distress from a payment network mid-buyback, so `unknown` -- the same neutral treatment every
  other axis gets for information this app cannot actually determine -- is the honest choice.
- **Joint liquidity evaluation, operating only.** `current_ratio_stmt` and free cash flow used
  to be graded fully independently, so a company with excellent free cash flow but a
  merely-weak current ratio was capped at yellow regardless of how strong its cash generation was
  (`docs/backlog/gemini_verdict_feedback.md` points 6/8). `current_ratio_stmt` now bands `ok`
  instead of `weak` when free cash flow (`stmt_free_cash_flow`, a raw dollar figure) covers the
  working-capital shortfall (`stmt_free_cash_flow >= -working_capital`, both carried through for
  exactly this check) AND `current_ratio_stmt` is at or above
  `CURRENT_RATIO_LIQUIDITY_FLOOR` (`0.5`) -- below that floor, current liabilities are more than
  double current assets, a real distress signal no amount of free cash flow should override. A
  dollar comparison, not `fcf_margin_pct` (free cash flow ÷ revenue): margin is scaled by
  revenue, not by the size of the liquidity gap, which isn't proportional to revenue for a
  company whose current liabilities carry a near-term debt-maturity wall -- a revenue-scaled
  check would have wrongly relieved that case. `fcf_margin_pct` still gates green in its own
  right as a core axis, unrelated to this relief. Relief lands on `ok`, never `good`: it stops
  the ratio blocking green on its own, but does not claim the ratio itself is strong, and does
  not rescue any other weak axis. `debt_to_equity` and `statement_roe_pct` get no analogous
  relief -- this is scoped to the one metric pair the feedback and the owner's decision named.
- **financial** — `statement_roe_pct` / `net_margin_pct` / `roa_pct` (**profitability only** — capital
  adequacy such as CET1/Tier 1 is unsourceable from yfinance, so the bank verdict stays modest).
  This limit is also shown card-face on every financial-type card, not just instructed in the
  AI-read prompt (`frontend/card_copy.py`'s `FINANCIAL_CAPITAL_ADEQUACY_CAVEAT`, rendered by
  `frontend/card_ui.py`'s `_health_block_html` regardless of whether `ai_read` is present) --
  the prompt only asks the model to mention it, never guarantees the model does.
- **`revenue_growth_yoy_pct` — ONE-SIDED, on operating and financial cards**.
  Growth below `GROWTH_DECLINE_THRESHOLD_PCT` (0.0, any year-over-year decline, no tolerance
  band) **blocks green**. It can do nothing else: growth never earns green, and it never causes
  red. That asymmetry is deliberate and load-bearing — a shrinking top line is a real health
  risk, while fast growth proves nothing about resilience (a company can grow into losses),
  which is why growth sat outside the verdict entirely until the rule "every metric a card
  shows must feed the verdict" forced the question. Null growth is NOT a decline and never
  blocks green. Do not make this a symmetric good/weak axis.
  **For a financial company the caveat differs and is not covered by the wording above.** A
  bank's top line is net interest income plus fees, which moves with the rate cycle rather
  than with the bank's own resilience, and a bank deliberately shrinking a loan book can
  improve its resilience while its revenue falls. The gate is still defensible there because
  it only ever withholds green and never causes red, but the reason a bank's line moved is
  not the reason an operating company's did.
- **pre_revenue** — `cash_runway_months` / `net_cash` / `working_capital`. The net-cash axis
  now bands on zero for both weak and good (is there more cash than debt?), because a money
  amount has no scale-free "good" level the way the old ratio's 0.2 did.

Missing inputs are treated as unknown/neutral, never faked; an all-unknown card falls back to `yellow`.
Thresholds live in `scripts/assessment_rules.py`, whose `INPUT_FIELDS_BY_TYPE` / `DIRECTION_BY_METRIC`
mirror this seed's `applies_to` / `direction` (a `tests/tooling` guard enforces it).

**`input_hash`:** sha256 over the per-type card metric set + `company_type` + `health_verdict` +
the card's display currency + `INPUT_HASH_VERSION` (numerics rounded to 6dp, NaN → null). The currency is
in the payload because the prompt names it and the prose read quotes it, so a card whose currency is
corrected upstream has to regenerate rather than keep prose naming the old one; it is hashed in its
normalised display form, so a `GBp`/`GBP` case change does not churn every FTSE read. The verdict + hash
recompute every run; the prose read regenerates only when the hash changes or `ai_read` is null. Bump
`INPUT_HASH_VERSION` to force a global read refresh (e.g. after a prompt or model change).

---

## Market activation checklist

`ingest_active: true` is set in step 1, not held back to the end, because several later steps
READ it and would otherwise do nothing: `refresh_constituents.py` skips a market that is not
active and exits 1, `sync_dbt_vars.py` filters on it and would write the old market list,
`audit_yfinance_coverage.py` and `seed_ci_raw_fixtures.py` both do the same, the guard tests
parametrise on it and would pass vacuously for the new market, and the CI baseline would be
written for a market set that does not yet exist.

The audit in steps 5 and 6 is the real gate, and it straddles the first pipeline run: the
sample half runs now, the full-run half can only be confirmed afterwards. A market is not proven
until both halves are done. Record the open half in `.claude/active_work.md`, not in a task
contract, which the next task overwrites.

1. Add row to `market_registry.yml` and `constituent_sources.yml`, with `ingest_active: true`
2. Refresh or import constituent seed (`scripts/refresh_constituents.py --market <code>`)
3. Run `python scripts/sync_dbt_vars.py`, which reads `ingest_active` and writes
   `dbt_project.yml`
4. Verify the seed's tickers resolve AND return a populated `sector`. Resolving alone is not
   enough: one of France's 40 came back as a Yahoo stub with no sector, industry or market cap
5. Run **coverage audit** over the operating-type eligibility metrics, the majority case for
   any market's constituents, on **sample and full run**. The sample is
   `scripts/audit_yfinance_coverage.py --market <code> --sample-size 20`, which prints a
   percentage only. The full-run half is the eligible count the first real pipeline run
   produces for that market, which the sample can only estimate: check it before treating the
   market as proven, and do not treat a healthy sample as the whole step
6. Confirm the market's card-eligible count clears the warn threshold
   (`WARN_ELIGIBLE_THRESHOLD`, currently 20, in `scripts/check_pipeline_completeness.py`).
   Estimated from the sample before the run, confirmed from the run itself afterwards
7. **Add a Supabase `markets` row in a numbered migration.** There is NO upsert fallback:
   `export_to_supabase.py` writes `mart_stock_cards` only, and three tables foreign-key to
   `public.markets` (`mart_stock_cards`, `user_interactions`, `card_assessments`), so a
   missing row aborts the export for every market on the next
   production run. No CI job catches it. See `supabase/migrations/014_fr_cac40_market.sql`.
   Put `market_code` FIRST in the VALUES tuple and give it the same `index_name`,
   `exchange_suffix` and `source` as the registry: `tests/ingestion/test_market_onboarding.py`
   checks both, and its migration scan is a text match rather than a SQL parser, so a different
   column order fails closed.
8. Update [`operations_guide.md`](operations_guide.md) market table AND
   `frontend/markets.py` (`MARKET_DISPLAY_NAMES`, or the filter renders "Fr Cac40") and
   `frontend/live_quote.py` (`_EXCHANGE_SUFFIX`, needed whenever the source table gives bare
   tickers rather than suffixed ones)
9. Run `python scripts/seed_ci_raw_fixtures.py` before any local `dbt build`: the staging
   models read a per-market parquet path that does not exist until fixtures are written. CI
   does this itself; a local run does not.
10. Run `pytest tests/ingestion/test_market_onboarding.py`. It pins every join above and
   detects a constituent that resolves to the same Yahoo symbol under two markets. That is
   usually a seed copied wrong, but occasionally a real dual-index membership: Airbus sits in
   both the DAX and the CAC 40, and ArcelorMittal is in the CAC 40 while listing in Amsterdam.
   Decide which it is, and if the membership is genuine add the symbol to
   `KNOWN_DUAL_INDEX_SYMBOLS` with the reason rather than editing a seed. Note the deck then
   shows that company once per market it belongs to (issue #7).
   **There are TWO collision guards and they take different allowlists.** The symbol one above is
   keyed on the resolved Yahoo symbol, so it only sees a company whose two indices track the same
   listing. A company listed on two venues resolves to two symbols and is caught instead by
   `test_no_unrecorded_company_appears_under_two_markets`, which is keyed on the company NAME and
   takes `KNOWN_CROSS_MARKET_COMPANIES`. ArcelorMittal needs both: `MT.AS` twice is a symbol
   collision, `MTS.MC` is a name collision. Adding to the wrong list leaves the test failing.
   The name guard keys on a punctuation-insensitive form, so it DOES catch a company spelled two
   ways ("News Corp (Class B)" against "News Corp Class B"), and allowlist keys must be written
   in that normalised form (lower case, ASCII letters and digits only, since the key deletes
   accented letters rather than folding them, so `Telefónica` keys to `telefnica` with the
   letter gone, not `telefonica`) or the
   stale-entry test rejects them. What it still cannot see is a pair differing by more than
   punctuation, and the whole
   same-market case, where one company ships two share classes inside one index.
11. Update `scripts/eligibility_baseline.ci.json` (a deterministic fixture count, 7 per active
   market). The production `scripts/eligibility_baseline.json` is NOT edited by hand; it is
   rewritten after a verified healthy run.

European expansion order: document in the registry, and run the coverage audit once per market.
Whether a branch carries one market or several is the owner's call; the per-market audit is not.
