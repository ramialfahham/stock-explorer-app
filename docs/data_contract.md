# Data contract — Stock Swipe App

> DURABLE. **Owns:** grains, freshness, completeness, export shape, eligibility and the verdict
> rules.
> **Never:** agent process. Where a metric's formula, label or format is authoritative is
> settled in [`metric_layer.md`](metric_layer.md), not here. The market-activation checklist
> near the end is operational and sits here because it is contract-driven; the day-to-day runbook
> is [`operations_guide.md`](operations_guide.md).

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

### Card metrics

> **Single source of truth:** each metric's definition (formula spec, label, `format`,
> `perspective`, `direction`, tier/order, `applies_to`, the analytical definition and the
> plain-language copy) lives in the [`metric_catalogue` seed](../dbt_analytics/seeds/metric_catalogue.csv)
> (see [`metric_layer.md`](metric_layer.md)). `int_stock__card_metrics` computes every metric
> once; the frontend reads `frontend/metrics.json`, generated from the seed. The table below is
> generated from the seed too (`scripts/render_metric_table.py`); a test fails when it is stale.
> The formula spec is the seed's `numerator_expr` / `denominator_expr`; the model's fallbacks
> and scaling (TTM versus annual, the `* 100`) are its own and are described in the prose after
> the table.

<!-- metric_table:start (generated by scripts/render_metric_table.py, do not edit) -->
| Card metric | Label | Shown for | Formula spec, over `fct_fundamentals_snapshot` | Format | Direction |
|---|---|---|---|---|---|
| `ebit_margin_pct` | Operating margin (TTM) | operating | `(qtr_operating_income_0 + qtr_operating_income_1 + qtr_operating_income_2 + qtr_operating_income_3) / (qtr_total_revenue_0 + qtr_total_revenue_1 + qtr_total_revenue_2 + qtr_total_revenue_3)` | `percent_1` | higher better |
| `revenue_growth_yoy_pct` | Rev growth YoY (quarter) | operating, financial | `info_revenue_growth * 100` | `percent_1` | higher better |
| `net_debt_to_ebitda` | Net debt / EBITDA | operating | `(coalesce(info_net_debt, info_total_debt - info_total_cash)) / (info_ebitda)` | `ratio_2` | lower better |
| `fcf_margin_pct` | FCF margin (annual) | operating | `(stmt_free_cash_flow * 100) / (stmt_total_revenue)` | `percent_1` | higher better |
| `debt_to_equity` | Debt / equity | operating | `(stmt_total_debt) / (stmt_stockholders_equity)` | `ratio_2` | lower better |
| `current_ratio_stmt` | Current ratio | operating | `(stmt_current_assets) / (stmt_current_liabilities)` | `ratio_2` | higher better |
| `statement_roe_pct` | Return on equity | operating, financial | `(stmt_net_income_common * 100) / (stmt_stockholders_equity)` | `percent_1` | higher better |
| `net_margin_pct` | Net margin | financial | `(stmt_net_income * 100) / (stmt_total_revenue)` | `percent_1` | higher better |
| `roa_pct` | Return on assets | financial | `(stmt_net_income * 100) / (stmt_total_assets)` | `percent_1` | higher better |
| `net_cash` | Net cash | pre_revenue | `stmt_cash_and_equivalents - stmt_total_debt` | `currency_compact` | higher better |
| `working_capital` | Working capital | pre_revenue | `stmt_current_assets - stmt_current_liabilities` | `currency_compact` | higher better |
| `cash_runway_months` | Cash runway | pre_revenue | `(stmt_cash_and_equivalents * 12) / (-(stmt_operating_cash_flow + stmt_capital_expenditure))` | `ratio_1` | higher better |
| `burn_rate_monthly` | Cash burn (monthly) | pre_revenue | `(-(stmt_operating_cash_flow + stmt_capital_expenditure)) / (12)` | `currency_compact` | lower better |
<!-- metric_table:end -->

**Data-only intermediates**, computed in `int_stock__card_metrics` and stored, rendered on no
card and absent from the seed (the model is their only definition): `forward_pe`, `roe_pct`,
`current_ratio`, `price_to_book`, `price_to_sales`, `ev_to_ebitda`, `fcf_yield_pct`,
`interest_coverage`, `price_to_tangible_book`, `computed_fcf`, `net_cash_to_ev`,
`net_cash_to_market_cap`, and `dividend_yield_pct`. Nullable; not clipped.

`dividend_yield_pct` carries one rule worth stating here because it is about the raw data, not
the metric: Yahoo sends `dividendYield` as a percent for most rows and a fraction for a few
(0.0387 = 3.87%, issue #10), so the model passes a value at or above 0.05 through and scales
one below it by 100 (4 dp). When the rule was set no genuine yield sat below 0.05% and no
fraction row belonged to a 5%+ payer; either would break it. `assert_dividend_yield_suspects`
(warn) lists the raw rows below 0.05 each run.

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
are missing, `net_debt_to_ebitda` is null → ineligible. Why both sides are Yahoo figures: the
catalogue row's `calculation`, the one statement of that definition.

**No fallbacks:** if the primary field for a metric is null, the ticker is ineligible — do not
substitute ROE, ROA, or hand-built ROIC.

**Standing rules for metric work.** Compute from the period-matched statement line where one
is landed, not the `info` scalar that duplicates it; the one metric defined otherwise,
`net_debt_to_ebitda`, says so in its catalogue row. Do not clip or hide outlier magnitudes at
the data layer; route to the
right lens and let the display clamp compress ([`ui/card_metric_cell.md`](ui/card_metric_cell.md));
the dividend-yield rescale corrects units, it caps nothing. Tier 1, CET1, NPL and ARR are not in
yfinance, NIM has no landed inputs, ROIC and multi-year series are deliberately not built (no
fallbacks; latest period only): leave the gap honest, never fake it.

---

## Card eligibility (dbt)

`is_card_eligible` uses **per-type required sets**, keyed on `company_type` (the Sector/Lifecycle Router):

- **operating** — all four of `ebit_margin_pct`, `revenue_growth_yoy_pct`,
  `net_debt_to_ebitda`, `fcf_margin_pct` non-null.
- **financial**: `statement_roe_pct`, `net_margin_pct` non-null. The operating metrics are
  not required BY CLASSIFICATION, not because they cannot be fetched: rule 1 above keys on
  `sector = 'Financial Services'` alone, and EBITDA and free cash flow are perfectly sourceable
  for an exchange or a ratings agency. They are dropped because leverage and cash-conversion
  ratios do not mean for a balance-sheet business what they mean for an operating one. Banks and
  insurers are the paradigm; the other members of the sector (exchanges, ratings agencies) are
  carried along by the coarse sector key.
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

**The export is atomic**, so a partial snapshot is not a state the pipeline can produce.
`scripts/export_to_supabase.py` sends the whole deck to `replace_cards_snapshot`
(`supabase/migrations/018_atomic_card_export.sql`), which deletes and re-inserts every
`(market_code, snapshot_date)` pair the payload covers, inside one transaction. Either every row lands or none does and the previous
snapshot stays intact. It previously wrote in batches of 500 with no transaction, so a failure
partway left some tickers on the new snapshot and the rest on the old one, which the frontend
then served as a mix with nothing marking it.

Three things worth knowing.

It replaces every `snapshot_date` the payload carries, not one. The mart holds one row per
`(market_code, ticker)`, but markets can sit on different dates: a per-market re-run after a
partial ingest legitimately produces more than one date across the payload, so refusing that
would turn a documented recovery step into a total export failure.

A ticker that was in a `(market, date)` pair the payload covers, but is no longer in the
mart, is deleted and not re-inserted. The old upsert left it.

What that does to the deck depends on what else the ticker has. Nothing has ever deleted from
this table, so it holds roughly one row per `(ticker, snapshot_date)` ever exported. If any of
its rows sit at pairs the payload does NOT cover, those survive and the ticker rolls BACK to
the newest of them: the reader sees a staler card whose `As of` date is correct but whose move BACKWARDS is
unannounced, rather than nothing. It leaves
the deck when the covered pairs take ALL of its remaining rows, which a multi-date payload can
do without any single pair having been its last. Both outcomes touch the unmade decision about
whether the deck should evict.

The reachable path is narrower than it first looks, and the condition matters. A ticker is
only evicted if its last exported `(market, date)` pair is one that some STILL-eligible ticker
of the same market currently occupies in the mart. A ticker that simply failed to refresh
keeps its row and its eligibility, so an un-refreshed market alone evicts nothing.

Two ways to reach it. A PARTIALLY refreshed market, where one ticker refreshes and becomes
ineligible (so it drops out of the mart) while another ticker of the same market failed to
refresh and still sits at the first one's old date. Or an eligibility-rule or seed change that
flips a ticker ineligible with no re-ingest at all.

Whether the deck SHOULD evict this way is an open question, and is not settled by this
mechanism having made it possible.

It inserts only the columns the payload carries, so a column the export does not send keeps
its DEFAULT, and it raises if the payload names a column the table does not have rather than
silently dropping it.

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
| `dividend_yield_pct` | `dividendYield` | percent, fraction for a few rows | passthrough at or above 0.05, x100 below | **100x smaller** (guard reads the RAW value) |
| `revenue_growth_yoy_pct` | `revenueGrowth` | fraction | x100 | **100x larger** |
| `roe_pct` | `returnOnEquity` | fraction | x100 | **100x larger** |

**The direction differs, which is why the guard is two-sided.** A percent source can only break
downward and a fraction source can only break upward; a one-sided floor would have been blind to
two of the three.

`dbt_analytics/tests/assert_percent_scale_passthroughs.sql` asserts the shape of each
distribution per market, comparing the median absolute value against a band. The x100 metrics
are read from `int_stock__card_metrics`; dividend yield is read RAW from
`fct_fundamentals_snapshot`, because the model's per-row correction would absorb a wholesale
flip for every yield under 5% and blind this guard. On the raw value a flip still moves every
market's median below the floor.

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
`int_stock__card_metrics` (raw `fct_fundamentals_snapshot` for the dividend branch, the same
rows), a superset that also carries ineligible tickers.

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

**What this does NOT cover.** Per-row mixed units, which production currently has (issue #10):
a market-median guard structurally cannot see them. A metric going entirely null, a provider
dropping or renaming a field, is covered by the fill floor below, not by this guard.

**`accepted_range` sanity guard** (severity: warn, `_marts.yml`). Seven metrics prone to
near-zero-denominator explosion per their own catalogue caveats -- `ebit_margin_pct`,
`revenue_growth_yoy_pct`, `net_debt_to_ebitda`, `fcf_margin_pct`, `debt_to_equity`,
`statement_roe_pct`, `net_margin_pct` -- get a wide bound, not a business-rule definition of a
valid value. Measured against the full exported history (5,726 rows):
`ebit_margin_pct` ranges -90,333.7% (DYL, a known accepted pre-revenue outlier) to 44,944.9%
(IAG -- large, real, unexplained; flagged, not root-caused here); `net_margin_pct`, which
shares `fcf_margin_pct`'s revenue denominator and the same "breaks for pre-revenue firms"
catalogue caveat, ranges -66,685.5% (DYL again) to 203.9% (PNI). Bounds sit well past every
measured extreme: `ebit_margin_pct` +-100000; `net_debt_to_ebitda`/`debt_to_equity` +-200;
`fcf_margin_pct`/`net_margin_pct` +-150000; `statement_roe_pct` +-5000;
`revenue_growth_yoy_pct` -100 to 15000 (floored, revenue cannot fall further). Warn-only:
catches an orders-of-magnitude pipeline bug, not a business judgment about plausibility.

An eighth metric, `cash_runway_months`, has no catalogue caveat naming this risk but the same
underlying shape: `int_stock__card_metrics.sql` divides cash on hand by unfloored monthly
burn (`-computed_fcf`, only required to be greater than zero, never bounded away from it), so
a company sitting right at cash-flow breakeven can push the ratio arbitrarily high. The
column is computed for every `company_type` (the SQL's only gate is `computed_fcf < 0`, no
type filter), though only the `pre_revenue` card renders it -- and the test itself carries no
`where` clause, so it runs over the full computed population, not just what's displayed. Not
theoretical: measured range across that full population (599 non-null rows) is
0.06 months (SRE, `operating`) to 1093.1 months (~91 years, LLOY, `financial`) -- a bank or a
capital-heavy operating company having one period of small negative free cash flow, not a
startup nearing breakeven. Within just the 11 rows the pre_revenue card actually renders, the
range is far narrower: 1.50 to 41.31 months. Bound 0 to 100000 covers both populations with
room to spare. The metric is structurally non-negative (cash and
burn are both non-negative by construction), so the floor is a real fact, not a margin, and
the ceiling sits ~90x past the measured extreme.

Two other metrics with a revenue/liability-style denominator were checked and left out:
`roa_pct` (divides by total assets, which a real operating company's balance sheet does not
carry near zero) measured -94.9% to 169.3% with no sign of the explosion mode this guard
targets; `current_ratio_stmt` (divides by current liabilities) measured 0.08 to 59.9, still
bounded, unlike the ratio-of-thin-or-negative-equity/revenue metrics above -- both denominators
stay structurally far from zero across the full measured history, not just by luck this run.
Two more, `price_to_tangible_book` (denominator: tangible book value) and
`net_cash_to_market_cap` (denominator: market cap), divide by figures that are rarely near
zero for a real traded company, and are excluded for a second, independent reason: both are
documented dead columns in `_marts.yml` -- `price_to_tangible_book`'s description says "no
card renders it", `net_cash_to_market_cap`'s says "superseded by `net_cash`" -- still exported
to Supabase, but nothing a user sees depends on either's value, so a guard here would not
protect anything the eligibility/display layer trusts.

**Fill floor** (`assert_metric_fill_floor.sql`). For every `(market_code, company_type,
metric)` where the catalogue says the metric applies to that type, at least half of the
eligible cards must carry a value; groups under five rows are skipped. Owner-set: a sanity
floor between normal gaps (measured 79% at worst with five or more rows) and a dropped field
(0%), not a metric definition. Metrics that gate eligibility are already 100% among eligible
rows by construction; this floor exists for the displayed-but-not-required ones. CI fixtures
hold five operating rows per market and one each of the other types, so CI exercises the floor
for operating metrics only.

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

### At ingestion, before dbt

| Check | Fail | Continue |
|-------|------|----------|
| Fundamentals fetch failures, per market | **> 5%** of its tickers | at or below; tickers named |

Implemented in `ingestion/main.py`; the 5% is the baseline gate's `warn_drop_fraction`, pinned
equal by a test. A failed run skips the export, so Supabase keeps its last good snapshot. A
ticker that fails under the line has no new row, so its previous snapshot stays in the deck:
the card's `As of` date is older, but nothing on it says a refresh was attempted. The stderr
line is the only trace of the attempt.

### Registry

`scripts/check_registry_var_sync.py` ensures `dbt_project.yml` `active_market_codes` matches
registry `ingest_active: true` entries (CI on every PR).

---

## Supabase export -- `mart_stock_cards` table

Grain: one row per `(market_code, ticker, snapshot_date)` -- the Postgres TABLE's grain,
which accumulates snapshot dates per ticker. The dbt MODEL of the same name declares a
narrower grain, `(market_code, ticker)` at each market's latest snapshot only (see its own
description in `dbt_analytics/models/5_marts/_marts.yml`); this heading names the table.

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
The write is `_upsert_records()`, batched **by each record's exact set of present keys**, never
a single upsert of the whole batch -- PostgREST computes `columns` as the union of keys across
every record in ONE call, so a "carried" record (omits `ai_read`/`read_model` to keep the
stored value) sharing a call with a "generated" one gets that value nulled, not preserved --
production evidence: a run logging `carried=853` had 839 of those rows come out null.
`_fetch_existing_assessments()` paginates for the same reason -- an
unranged select silently caps at PostgREST's default 1000 rows, missing later cards.

The AI-read step is the pipeline's dominant runtime cost (one sequential API call per
regenerating card, no retry). `--max-reads` caps new calls per run, unbounded by default;
no-stored-read cards fill before refresh-only ones, and anything the cap misses is eligible
again next run. A capped or failed card's stale stored read is explicitly cleared, not left
showing under fresh numbers -- `attach_assessments()`'s snapshot_date guard
(frontend/explore_filters.py) can't see `input_hash`. See `attach_reads()`'s docstring for
both mechanisms.

**Structured output + hallucination guard (Gemini feedback points 3/4).** The Haiku call forces
tool-use (`tool_choice`, `write_card_read`): the model returns `read` (the prose) plus
`referenced_metrics`, one `{label, value_as_shown}` entry per metric the read explicitly cites,
copied exactly as shown in the prompt's own facts block. That facts block names each metric
the way the card face does on that row (the catalogue's label, or operating margin's per-row
"(annual)" form when `ebit_margin_basis` is `annual_latest`) and renders its value exactly as
the card face does (`format_metric_value` in `frontend/card_copy.py`), both pinned by tests in
`tests/tooling`, so a read can only cite what the reader sees beside it. `validate_read_metrics`
checks each pair
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

**The whole health block is withheld when the assessment's `snapshot_date` differs from the
card's** -- verdict and read together, with no placeholder; the financial caveat is not in
the block and stays. That is a
different case from the five below, which all keep the verdict and drop only `ai_read`. It
happens when the two jobs disagree about which snapshot the card is on: the assessments step
failing after a successful export, or the export rolling a card back to an earlier snapshot
(see "Stale export policy"). It self-heals on the next healthy run except for a ticker that
has dropped out of the dbt mart while older Supabase rows survive: it keeps rendering a card,
and `generate_assessments.py` reads only the DuckDB mart, so its assessment row is never
rewritten and the mismatch is permanent. A ticker whose rows are ALL deleted is a different
case and not this one -- it renders no card at all, so it has no verdict to withhold.

When `ai_read` is absent (a brand-new card, a per-card API failure, a hallucination-guard
reject, a style-guard reject, or a card `--max-reads` did not reach this run), the card shows
a deterministic, non-AI one-line summary under its own "What the verdict means" heading
instead of the AI-written read (`frontend/card_copy.py`'s `VERDICT_FALLBACK_READ`), never
AI-attributed, phrased as a general summary rather than a description of the rules below
since neither the decisive-vs-supporting metric split nor the per-metric thresholds are shown
anywhere on the card. The first four causes are meant to be rare and self-correcting; a
capped card is not -- once the owner sets a real `--max-reads` value, this is the expected,
by-design outcome for every card past that run's cutoff. The upsert-clobbering bug above was
neither rare nor by design: for some real stretch of time before it was fixed, roughly 80% of
cards were in this state -- most readers saw the fallback line, not a real read. It self-heals
with no separate cleanup needed: `attach_reads()` regenerates
whenever `not existing.get("ai_read")`, independent of `input_hash`, so every clobbered row is
eligible for a fresh read on the very next scheduled run once the fix ships.

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
| `snapshot_date` | date | the mart snapshot the assessment reflects. Load-bearing at read time, not just provenance: the frontend attaches the verdict only when this equals the card's `snapshot_date` |
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
  adequacy such as CET1/Tier 1 is unsourceable from yfinance, so the verdict on a `financial`
  card stays modest -- for a whole sector, of which banks are only the part CET1/Tier 1 names).
  This limit is shown card-face rather than only instructed in the AI-read prompt
  (`frontend/card_copy.py`'s `FINANCIAL_CAPITAL_ADEQUACY_CAVEAT`, rendered by
  `frontend/card_ui.py`'s `_financial_caveat_html` under the metric stack of every financial
  card, whether or not a health block or `ai_read` is present) -- the prompt only asks the
  model to mention it, never guarantees the model does. It is independent of the health
  block on purpose: a card awaiting its first assessment, or whose assessment is on a
  different `snapshot_date`, has no block and still carries the caveat (gitlab issue #11).
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

**`burn_rate_monthly` is shown on the card and deliberately NOT read by the verdict.** That is
the one intentional exception to "every metric a card shows feeds the verdict", and the reason is
double counting: `cash_runway_months` already divides cash by burn, so reading burn separately
would weigh the same fact twice. It stays on the card because a ratio alone destroys the
magnitude information the raw number carries.

**Percentile or sector-relative ranking as a verdict threshold is rejected**, considered and
declined twice. Being in some top percentile can still mean an unhealthy state if the whole
sector is unhealthy, so a relative rank cannot answer "is this company financially sound". If
this is ever revisited, the legitimate shape to copy is a rating agency's per-industry ABSOLUTE
thresholds, not relative ranking. This is a different rule from the benchmark-display guidance in
[`north_star.md`](north_star.md), which concerns how peer context is SHOWN.

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
