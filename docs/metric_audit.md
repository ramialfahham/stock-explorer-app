# Metric audit — mart vs live yfinance

Compare [`mart_stock_cards`](../dbt_analytics/models/5_marts/mart_stock_cards.sql) values to a **fresh yfinance pull**, recomputed by **rebuilding `int_stock__card_metrics` through dbt** on the fresh raw. There is no second (Python) formula — the dbt model is the single source of every metric (see [`metric_layer.md`](metric_layer.md)). Use this before changing card metrics or labels.

## Run locally

After a healthy `dbt build` (or scheduled pipeline run):

```bash
# DuckDB mart (default) — fresh yfinance fetch + dbt rebuild
python scripts/audit_mart_vs_yfinance.py \
  --duckdb-path storage/stock_data.db \
  --sample-size 30 \
  --always ABNB,NVDA,AAPL,ALB

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
| `mart_*` | Value on the exported mart row |
| `fresh_*` | Value recomputed by rebuilding `int_stock__card_metrics` through dbt on a fresh yfinance pull (same formula, by construction) |
| `drift_pct_*` | Signed percent difference of `mart_*` from `fresh_*` |
| `dbt_rebuild_ok` | Whether the fresh dbt rebuild produced a row for this ticker |
| `live_fetch_ok` | Whether the fresh yfinance fetch succeeded |
| `snapshot_age_days` | Days since mart `snapshot_date` — large age explains stale forward P/E |
| `business_summary_present` | Whether `longBusinessSummary` reached the mart |

High `drift_pct_*` with **low** `snapshot_age_days` → the mart and a fresh rebuild disagree on current data: investigate the export or a since-changed upstream — not the formula, which is identical (the same dbt model produced both).

High `drift_pct_*` with **high** `snapshot_age_days` → the mart is simply stale; run export / wait for the next scheduled pipeline run.

Offline mode (`--offline`, the CI smoke) reports only the `mart_*`, `snapshot_age_days`, and `business_summary_present` columns — no fetch, no rebuild.

## Decision log (metric-by-metric)

| Metric | Audit finding | Decision | PR |
|--------|---------------|----------|-----|
| Forward P/E | ABNB ~22.1 aligns with Yahoo forward P/E | Keep `info_forward_pe`; monitor snapshot age | — |
| Operating margin | ABNB mart ~3.2% matches `reference_operating_margin_info` (latest quarter); TTM reference ~15–21% | **Replace card metric with TTM** from quarterly Operating Income / Total Revenue | Pipeline PR |
| Rev growth YoY | ABNB ~17.9% matches Yahoo quarterly YoY | Keep `info_revenue_growth`; relabel as quarter in UI PR | Labels PR |
| Net debt / EBITDA | ABNB −3.62 plausible (net cash / EBITDA) | Keep info-based formula | — |
| FCF margin | ABNB ~38% aligns with annual stmt / info trailing | Keep annual statement formula; label already says (annual) | — |
| Dividend yield | Added to the comparison set, not from an audit finding | Compare it here too, so the set matches what the scale guard covers; the real guard is `assert_percent_scale_passthroughs.sql`, since this script cannot detect a settled flip | Scale-guard PR |

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
