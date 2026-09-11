# Project context — Stock Swipe App

> DURABLE. **Owns:** stock-specific conventions that extend the general standards.
> **Never:** anything the general standards already state.

Stock-specific conventions that extend the general standards in
[`.claude/working-agreement.md`](../.claude/working-agreement.md), `layering.md` and
`engineering_standards.md`. When the general docs and this file
conflict on dbt layers, naming, or testing, the general docs win. This file covers
what is unique to this repo.

---

## What this project is

Card-based stock dashboard. Python ingestion → dbt (DuckDB) → Supabase → Streamlit.

Nothing runs on a developer machine in production. GitLab CI runs ingestion,
dbt, and export on a schedule.

---

## Stack

| Layer | Technology |
|-------|------------|
| Ingestion | Python + yfinance |
| Transform | dbt-core + dbt-duckdb (ephemeral DuckDB in CI) |
| Warehouse | Supabase (Postgres) |
| Frontend | Streamlit on Render |

---

## Market-agnostic by default

`market_code` is the partition key on all market-scoped models, metrics, and UI logic.
Never hardcode `us_sp500` or any other market identifier in business logic.

Single source of truth: [`market_registry.yml`](market_registry.yml).
Adding a market starts with one registry entry and is not finished by it: follow the market
activation checklist in `data_contract.md`. dbt var `active_market_codes` must stay in sync
(`python scripts/sync_dbt_vars.py`; CI enforces via `scripts/check_registry_var_sync.py`).

---

## DuckDB layout

One DuckDB file (`storage/stock_data.db` locally; ephemeral in CI) with one schema per layer:

| Schema | Folder |
|--------|--------|
| `staging` | `models/1_staging/` |
| `base` | `models/2_base/` |
| `core` | `models/3_core/` |
| `intermediate` | `models/4_intermediate/` |
| `marts` | `models/5_marts/` |

Raw landing is **parquet** under `storage/raw/{market_code}/`. dbt reads via `sources.yml`.
dbt var `raw_path` (default `../storage/raw`) must match ingestion output.

Run dbt from repo root:

```bash
dbt <command> --project-dir dbt_analytics --profiles-dir .
```

---

## Ingestion contract

- No business logic in ingestion — raw fields only, no derived metrics.
- Reads active markets from `market_registry.yml`; nothing hardcoded.
- **Hybrid constituents:** committed seeds in `storage/seeds/{market_code}/constituents.csv`;
  refresh via `scripts/refresh_constituents.py` using `docs/constituent_sources.yml`.
- Raw parquet output: `storage/raw/{market_code}/yf_constituents.parquet`, `yf_daily_prices.parquet`,
  and (Phase B) `yf_fundamentals.parquet`.
- Fundamentals ingestion: raw `ticker.info` keys + financial statement rows only — see
  [`data_contract.md`](data_contract.md) § yfinance raw field mapping. No ratios in Python.
- Run ingestion: `python scripts/run_ingestion.py` (optional `--max-tickers` for local dev).
- Credentials via `.env` + python-dotenv only.

---

## Supabase export contract

- Primary mart: `mart_stock_cards` (all markets; filter by `market_code` at export/UI).
- Do not create per-market mart copies.
- Exporter: `scripts/export_to_supabase.py` replaces the `mart_stock_cards` snapshot in one
  transaction (`replace_cards_snapshot`) using the service role key
  (scheduled via the `data-pipeline` job in [`.gitlab-ci.yml`](../.gitlab-ci.yml)).
- Streamlit reads Supabase with the **anon** key only.

Setup: [`supabase_setup.md`](supabase_setup.md).

---

## CI extensions

In addition to the gates in `engineering_standards.md` §8, every MR also runs:

- `python scripts/check_layer_contract.py`
- `python scripts/check_registry_var_sync.py`

See [`.gitlab-ci.yml`](../.gitlab-ci.yml) — `validate:full` job.

---

## Naming (yfinance source)

| Layer | Example |
|-------|---------|
| staging | `stg_yf__daily_prices` |
| base | `base_yf__daily_prices` |
| core | `dim_stock`, `fct_daily_price` |
| intermediate | `int_stock__price_changes` |
| marts | `mart_stock_cards` |

Staging SQL lives under `models/1_staging/yfinance/`, never at the `1_staging/` root.
