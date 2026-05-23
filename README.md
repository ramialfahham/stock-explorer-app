# Stock Swipe App

A card-based stock dashboard. Users are shown stock cards per session and interact with them (save / skip).

## Stack

| Layer | Technology |
|---|---|
| Ingestion | Python + yfinance |
| Transform | dbt-core + dbt-duckdb (ephemeral DuckDB) |
| Warehouse | Supabase (Postgres) |
| Frontend | Streamlit Community Cloud |

## Architecture

```
GitHub Actions (scheduled)
  → Python ingestion (yfinance → raw parquet)
  → dbt transforms (ephemeral DuckDB)
  → export marts to Supabase

Supabase (Postgres)
  → processed stock data + user interactions + auth

Streamlit Community Cloud
  → reads Supabase, serves UI
```

Nothing runs on a developer machine in production.

## Project layout

```
stock-swipe-app/
├── docs/market_registry.yml   # Active markets (registry-driven, no hardcoding)
├── ingestion/                 # Raw data fetch scripts
├── storage/
│   ├── raw/                   # Parquet from ingestion (gitignored)
│   └── stock_data.db          # Local DuckDB for dev (gitignored)
├── dbt_analytics/             # dbt project (staging → marts)
├── frontend/                  # Streamlit app
├── .github/workflows/         # CI pipeline
├── profiles.yml.example       # Copy to profiles.yml for local dbt
└── .env.example               # Copy to .env for Supabase credentials
```

## Local setup

1. **Clone and create a virtual environment**

   ```bash
   python -m venv venv
   venv\Scripts\activate        # Windows
   pip install -r requirements.txt
   ```

2. **Configure dbt**

   ```bash
   copy profiles.yml.example profiles.yml
   dbt debug --project-dir dbt_analytics --profiles-dir .
   ```

3. **Configure Supabase** (when ready)

   ```bash
   copy .env.example .env
   # Edit .env with your Supabase project values
   ```

4. **Markets** — see `docs/market_registry.yml` for the stock universe definition.

## Engineering standards

- No business logic in ingestion — raw fields only
- All credentials via `.env` + python-dotenv
- dbt model layers: `1_staging/` → `3_core/` → `4_intermediate/` → `5_marts/`
- Model naming: `stg_yf__<entity>`, `fct_<entity>`, `dim_<entity>`, `mart_<purpose>`
- Every dbt model needs at least one test
- Never commit `.env` or `profiles.yml`
