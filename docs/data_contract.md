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

### Card metrics — dbt formulas (v1)

> **Single source of truth:** each metric's definition — formula spec, label, `format`, `perspective`,
> `direction`, tier/order, the analytical definition (`calculation` / `interpretation` /
> `applicability`), and plain-language copy — lives in the [`metric_catalogue` seed](../dbt_analytics/seeds/metric_catalogue.csv)
> (see [`metric_layer.md`](metric_layer.md)). The table below is the computed reference; the seed is
> authoritative for display, labels, and format, and the frontend reads `frontend/metrics.json`
> (generated from it). `int_stock__card_metrics` is where the metrics are computed, once.

| # | Card metric | Formula | Primary inputs |
|---|-------------|---------|----------------|
| 1 | `forward_pe` | `info_forward_pe` | `ticker.info` |
| 2 | `ebit_margin_pct` | TTM: `sum(eff_op_0..3) / sum(qtr_total_revenue_0..3) * 100`; else annual `eff_stmt_op / stmt_total_revenue * 100` | quarterly + annual income_stmt |
| 3 | `revenue_growth_yoy_pct` | `info_revenue_growth * 100` | `ticker.info` |
| 4 | `net_debt_to_ebitda` | `coalesce(info_net_debt, info_total_debt - info_total_cash) / info_ebitda` | `ticker.info` |
| 5 | `fcf_margin_pct` | `stmt_free_cash_flow / stmt_total_revenue * 100` | cashflow + income_stmt |

**Data-only metrics (computed in dbt, not yet on the card):** `roe_pct` = `info_return_on_equity * 100`
(Yahoo `returnOnEquity`), computed once in `int_stock__card_metrics`. **Not** part of `is_card_eligible`,
the `metric_catalogue`, `frontend/metrics.json`, or the Supabase export — staged for the Sector/Lifecycle
Router to catalogue, gate, and display per company type. Nullable; may be negative (loss-makers); not clipped.

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

A ticker is **`is_card_eligible = true`** when **all five** metrics are non-null:

1. `forward_pe`
2. `ebit_margin_pct`
3. `revenue_growth_yoy_pct`
4. `net_debt_to_ebitda`
5. `fcf_margin_pct`

Missing any metric → excluded from discovery queue.

**`missing_metrics`** (DuckDB-only, on `int_stock__card_metrics` and `mart_stock_eligibility_gaps`):
VARCHAR list of the five metric column names that are null for that snapshot.
Empty when eligible. Used for pipeline QA — **not** exported to Supabase.

Field-level mapping and dbt formulas: **§ yfinance raw field mapping** above.

---

## Sector benchmarks (dbt → export)

Computed per `(market_code, sector)` over **card-eligible** tickers in that market:

| Output | Description |
|--------|-------------|
| `sector_peer_count` | Count of eligible peers in sector |
| `sector_median_*` | Median for each of the five metrics |

**Peer threshold:** if `sector_peer_count < 8`, export `null` medians; UI omits benchmark line.

Benchmark availability does **not** affect `is_card_eligible`.

---

## Freshness

| Layer | Cadence | Owner |
|-------|---------|-------|
| Constituents | On demand / when index changes | `refresh_constituents.py` |
| Fundamentals | **Weekly** (or on statement refresh) | GitHub Actions `data_pipeline.yml` |
| Daily prices | Weekly or daily (supporting only) | Same pipeline |
| Supabase export | After successful dbt build | `export_to_supabase.py` |
| News (Phase 2) | Daily | Separate workflow |

**Stale export policy:** if weekly pipeline fails completeness gate, **keep last good Supabase
snapshot**; do not truncate to empty.

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

| Column | Type | Notes |
|--------|------|-------|
| `market_code` | text | FK → `markets` |
| `ticker` | text | Provider symbol |
| `company_name` | text | |
| `sector` | text | |
| `currency` | text | |
| `business_summary` | text | Yahoo `longBusinessSummary`; nullable |
| `forward_pe` | numeric | |
| `ebit_margin_pct` | numeric | |
| `revenue_growth_yoy_pct` | numeric | |
| `net_debt_to_ebitda` | numeric | |
| `fcf_margin_pct` | numeric | |
| `is_card_eligible` | boolean | |
| `sector_peer_count` | integer | |
| `sector_median_forward_pe` | numeric | nullable |
| `sector_median_ebit_margin_pct` | numeric | nullable |
| `sector_median_revenue_growth_yoy_pct` | numeric | nullable |
| `sector_median_net_debt_to_ebitda` | numeric | nullable |
| `sector_median_fcf_margin_pct` | numeric | nullable |
| `snapshot_date` | date | Fundamentals as-of date |
| `exported_at` | timestamptz | |

**Removed from v1 card contract:** `latest_price`, `price_change_1d_pct`, `price_change_5d_pct`,
and `roic` (see migration `002_fundamentals_mart.sql`).

---

## Market activation checklist

Before setting `ingest_active: true` for a new market:

1. Add row to `market_registry.yml` and `constituent_sources.yml`
2. Run `python scripts/sync_dbt_vars.py`
3. Refresh or import constituent seed
4. Run **coverage audit** (all five metrics on sample + full run)
5. Confirm eligible count ≥ warn threshold
6. Add Supabase `markets` row (or rely on export upsert)
7. Update [`operations_guide.md`](operations_guide.md) market table

European expansion order after DAX: document in registry; activate one market per audit cycle.
