# International balance-sheet row labels

Yahoo `ticker.balance_sheet` normalises row labels to a fixed key set, so a single canonical
label per line is consistent across markets (confirmed by the probe below). The balance sheet
is **point-in-time** (a stock, not a flow), so ingestion lands the **latest annual column
only** — no TTM summing (unlike the quarterly income-statement machinery in
[`intl-quarterly-row-labels.md`](intl-quarterly-row-labels.md)).

## Fallback order (ingestion)

`ingestion/yfinance/balance_sheet.py` lands each raw `stmt_*` field from its canonical Yahoo
row label. yfinance canonicalises these labels, so one label per line resolves across all
markets; only **equity** keeps a second real fallback (`Common Stock Equity`) for names that
report it instead of `Stockholders Equity`:

| Field | Row label(s) |
|-------|--------------|
| `stmt_stockholders_equity` | `Stockholders Equity` → `Common Stock Equity` |
| `stmt_total_debt` | `Total Debt` |
| `stmt_current_assets` | `Current Assets` |
| `stmt_current_liabilities` | `Current Liabilities` |
| `stmt_cash_and_equivalents` | `Cash And Cash Equivalents` (narrow; excludes short-term investments) |
| `stmt_tangible_book_value` | `Tangible Book Value` |

Raw scalars only — no ratios are computed in ingestion (dbt owns debt-to-equity, current
ratio, working capital, tangible-book valuation, etc.).

## Coverage probe

```bash
python scripts/probe_balance_sheet_labels.py --sample 5        # all active markets
python scripts/probe_balance_sheet_labels.py --market uk_ftse100 --sample 20
```

Live probe (2026-07-06, `--sample 5 --seed 42`, share of sample where a fallback label
resolved to a value):

| Field | us_sp500 | uk_ftse100 | jp_nikkei225 | au_asx200 | de_dax |
|-------|----------|------------|--------------|-----------|--------|
| `stmt_stockholders_equity` | 100% | 100% | 100% | 100% | 100% |
| `stmt_total_debt` | 100% | 100% | 100% | 100% | 100% |
| `stmt_current_assets` | 100% | 80% | 80% | 100% | 100% |
| `stmt_current_liabilities` | 100% | 80% | 80% | 100% | 100% |
| `stmt_cash_and_equivalents` | 100% | 100% | 100% | 100% | 100% |
| `stmt_tangible_book_value` | 100% | 100% | 100% | 100% | 100% |

Balance sheet present for 100% of the sample in every market; the fallback labels above
resolved without needing market-specific additions.

## Notes

- **Current assets / liabilities are absent for ~20% of UK and JP names.** These are
  **financials** (banks/insurers), whose balance sheets have no current/non-current split.
  The fields are nullable and are correct to be null there — the Router does not use a
  liquidity metric for financials.
- `Tangible Book Value` is present in every market, so price-to-tangible-book is sourceable
  directly rather than derived from goodwill/intangibles. (Which metrics each company type
  actually shows is a later-slice owner decision — this doc only records sourcing.)
- Sample size is small (5/market); the full universe is validated on the next pipeline
  re-ingest. Re-run the probe if coverage regresses.
