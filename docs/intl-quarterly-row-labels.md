# International quarterly operating-profit row labels

Yahoo `quarterly_income_stmt` uses different GAAP line names by market. The card
operating margin needs four quarters of operating profit and total revenue.

## Fallback order (ingestion)

`ingestion/yfinance/quarterly.py` lands `qtr_operating_income_0..3` using the first
non-null value per quarter from:

1. `Operating Income`
2. `Total Operating Income As Reported`
3. `Operating Profit`
4. `EBIT`

When those rows are absent but **Operating Revenue** and **Operating Expense** exist
(UK banks such as HSBA.L), ingestion also lands `qtr_operating_revenue_*` and
`qtr_operating_expense_*`. dbt derives operating profit as revenue minus expense.

## Annual path

When four quarterly values are incomplete, dbt falls back to latest annual operating
profit (`stmt_operating_income` with the same label order) divided by
`stmt_total_revenue`. `ebit_margin_basis` on the mart records `ttm_quarterly` vs
`annual_latest`.

## Coverage probe

```bash
python scripts/probe_quarterly_op_labels.py --market uk_ftse100 --sample 20
```

Post-ingest local snapshot (2026-06-09, before this change re-ingest):

| Market | 4Q op (primary label only) | Main blocker |
|--------|------------------------------|--------------|
| uk_ftse100 | ~7% | 86% lack quarterly stmt; remainder often bank layout |
| au_asx200 | ~5% | Quarterly stmt sparse; annual stmt available |
| jp_nikkei225 | ~5% | Alternate row labels on quarterly stmt |
| de_dax | ~75% | Mostly complete |

Re-run probe and `check_eligibility_baseline.py` after re-ingest to verify uplift.
