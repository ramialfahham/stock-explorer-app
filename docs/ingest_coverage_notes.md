# yfinance coverage notes (2026-06-03)

From `python scripts/audit_yfinance_coverage.py --sample-size 5` on all active markets.

## Summary

| Field | Typical hit rate (5-ticker sample) |
|-------|-------------------------------------|
| forwardPE, operatingMargins, revenueGrowth, ebitda | ~80–100% |
| Total Revenue / Free Cash Flow (statements) | 100% |
| **netDebt** | **0%** in this sample |

**Estimated card_eligible:** 0% in sample — all five metrics require `info_net_debt`; Yahoo often omits `netDebt` in `ticker.info`.

Price fetch: `history` and `download` both OK for sampled symbols (including `.L`, `.T`, `.DE`).

## Implications

- Smoke/full ingest can succeed while **mart eligible count stays low** until netDebt coverage improves or product revisits the contract.
- `check_pipeline_completeness.py` may fail the **&lt;5 eligible** gate until this changes — expected for now.
- Run full ingest per market with default `--delay-seconds 0.25`; use `workflow_dispatch` on Data Pipeline after a one-market pilot.

## Commands

```bash
python scripts/audit_yfinance_coverage.py --sample-size 10
python scripts/run_ingestion.py --market us_sp500
```
