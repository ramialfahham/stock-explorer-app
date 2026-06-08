# Metric audit — mart vs live yfinance

Compare [`mart_stock_cards`](../dbt_analytics/models/5_marts/mart_stock_cards.sql) values to a **fresh yfinance pull** using the same raw fields and dbt formulas. Use this before changing card metrics or labels.

## Run locally

After a healthy `dbt build` (or weekly pipeline):

```bash
# DuckDB mart (default) — live yfinance calls
python scripts/audit_mart_vs_yfinance.py \
  --duckdb-path storage/stock_data.db \
  --sample-size 30 \
  --always NVDA,AAPL,ALB

# Production Supabase mart
python scripts/audit_mart_vs_yfinance.py --source supabase --sample-size 30

# CI / offline — mart load only, no network
python scripts/audit_mart_vs_yfinance.py \
  --duckdb-path /tmp/stock_data_ci.db \
  --offline \
  --sample-size 5
```

Reports are written to `storage/audit/metric_audit_<timestamp>.csv` and `.json`.

## Reading the report

| Column | Meaning |
|--------|---------|
| `mart_*` | Value on exported mart row |
| `live_*` | Value recomputed from fresh yfinance using [`metric_formulas.py`](../scripts/metric_formulas.py) (same as dbt) |
| `drift_pct_*` | Absolute percent difference vs live |
| `reference_fcf_margin_info` | `freeCashflow / totalRevenue` from info — Yahoo-trailing style reference, not mart |
| `reference_forward_pe` | Raw `forwardPE` from info |
| `snapshot_age_days` | Days since mart `snapshot_date` — large age explains stale forward P/E |
| `business_summary_present` | Whether `longBusinessSummary` reached the mart |

High drift on `live_*` with low `snapshot_age_days` → likely **formula/label mismatch**, not pipeline lag.

High drift with high `snapshot_age_days` → run export / wait for pipeline before changing dbt.

Large gap between `mart_fcf_margin_pct` and `reference_fcf_margin_info` → annual statement FCF margin vs trailing info ratio (known NVDA pattern).

## Decision log (metric-by-metric)

Record decisions here before PR B metric fixes:

| Metric | Audit finding | Decision | PR |
|--------|---------------|----------|-----|
| Forward P/E | | align / relabel / ops | |
| EBIT margin | | relabeled Operating margin; audit before formula change | PR B v2.4 |
| Rev growth YoY | | | |
| Net debt / EBITDA | | | |
| FCF margin | | footnote: annual statements; audit reference_fcf_margin_info | PR B v2.4 |

## Fail on drift (optional)

After review, tighten thresholds for pilot tickers:

```bash
python scripts/audit_mart_vs_yfinance.py \
  --duckdb-path storage/stock_data.db \
  --fail-on-drift \
  --max-drift-pct 25 \
  --pilot-tickers NVDA,AAPL,ALB
```

Start with warn-only; do not enable in CI against live yfinance until rate limits are understood.
