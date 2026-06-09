# yfinance coverage notes (2026-06-03)

From `python scripts/audit_yfinance_coverage.py --sample-size 5` on all active markets.

## Summary

| Field | Typical hit rate (5-ticker sample) |
|-------|-------------------------------------|
| forwardPE, operatingMargins, revenueGrowth, ebitda | ~80–100% |
| quarterly 4Q operating profit (intl) | varies — see `docs/intl-quarterly-row-labels.md` |
| Total Revenue / Free Cash Flow (statements) | 100% |
| **netDebt** | **0%** in prior sample (use totalDebt − totalCash in dbt) |
| **totalDebt + totalCash** | ~80–100% when netDebt missing |

**Estimated card_eligible:** was 0% before dbt coalesce on totalDebt/totalCash; re-run audit after merge.

Price fetch: `history` and `download` both OK for sampled symbols (including `.L`, `.T`, `.DE`).

## Implications

- `check_pipeline_completeness.py` may fail the **<5 eligible** gate when ebitda or other fields are missing for most tickers (e.g. banks).
- Land `info_total_debt` / `info_total_cash`; dbt coalesces net debt when `netDebt` is null.
- Run full ingest per market with default `--delay-seconds 0.25`; use `workflow_dispatch` on Data Pipeline after a one-market pilot.

## Commands

```bash
python scripts/audit_yfinance_coverage.py --sample-size 10
python scripts/run_ingestion.py --market us_sp500
```
