# Metric audit — mart vs live yfinance

Compare [`mart_stock_cards`](../dbt_analytics/models/5_marts/mart_stock_cards.sql) values to a **fresh yfinance pull** using the same raw fields and dbt formulas. Use this before changing card metrics or labels.

## Run locally

After a healthy `dbt build` (or weekly pipeline):

```bash
# DuckDB mart (default) — live yfinance calls
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
| `mart_*` | Value on exported mart row |
| `live_*` | Value recomputed from fresh yfinance using [`metric_formulas.py`](../scripts/metric_formulas.py) (same as dbt) |
| `drift_pct_*` | Absolute percent difference vs live |
| `reference_fcf_margin_info` | `freeCashflow / totalRevenue` from info — Yahoo-trailing style reference, not mart |
| `reference_forward_pe` | Raw `forwardPE` from info |
| `reference_operating_margin_info` | `operatingMargins × 100` from info — often **latest quarter**, not TTM |
| `reference_operating_margin_ttm` | Sum of last 4Q Operating Income ÷ sum of last 4Q Total Revenue × 100 |
| `drift_pct_ebit_margin_vs_info` | Mart operating margin vs info reference |
| `drift_pct_ebit_margin_vs_ttm` | Mart operating margin vs TTM reference (target after pipeline fix) |
| `snapshot_age_days` | Days since mart `snapshot_date` — large age explains stale forward P/E |
| `business_summary_present` | Whether `longBusinessSummary` reached the mart |

High drift on `live_*` with low `snapshot_age_days` → likely **formula/label mismatch**, not pipeline lag.

High drift with high `snapshot_age_days` → run export / wait for pipeline before changing dbt.

Large gap between `mart_fcf_margin_pct` and `reference_fcf_margin_info` → annual statement FCF margin vs trailing info ratio (known NVDA pattern).

Large gap between `reference_operating_margin_info` and `reference_operating_margin_ttm` on the same ticker (e.g. ABNB ~3% vs ~15–21%) → mart uses info `operatingMargins` today; switch card metric to TTM from quarterly statements.

## Decision log (metric-by-metric)

| Metric | Audit finding | Decision | PR |
|--------|---------------|----------|-----|
| Forward P/E | ABNB ~22.1 aligns with Yahoo forward P/E | Keep `info_forward_pe`; monitor snapshot age | — |
| Operating margin | ABNB mart ~3.2% matches `reference_operating_margin_info` (latest quarter); TTM reference ~15–21% | **Replace card metric with TTM** from quarterly Operating Income / Total Revenue | Pipeline PR |
| Rev growth YoY | ABNB ~17.9% matches Yahoo quarterly YoY | Keep `info_revenue_growth`; relabel as quarter in UI PR | Labels PR |
| Net debt / EBITDA | ABNB −3.62 plausible (net cash / EBITDA) | Keep info-based formula | — |
| FCF margin | ABNB ~38% aligns with annual stmt / info trailing | Keep annual statement formula; label already says (annual) | — |

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
