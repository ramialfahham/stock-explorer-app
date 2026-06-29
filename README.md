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
  → processed stock data (anon read); user_interactions table reserved for future auth

Streamlit Community Cloud
  → reads card marts via anon key; save/skip in browser localStorage (v1, no signup)
```

Nothing runs on a developer machine in production.

## Project layout

```
stock-swipe-app/
├── CLAUDE.md                  # Entry doc for Claude Code — points to guardrails + docs
├── .claude/                   # dbt-agent-kit guardrails: working-agreement.md, review_routing.json, active_work.md, task/
├── docs/
│   ├── working_agreement.md     # UX PR gate + redirect (agent process now in .claude/)
│   ├── layering.md              # dbt layer rules
│   ├── engineering_standards.md # Naming, testing, CI
│   ├── project_context.md       # Stock-specific extensions
│   ├── market_registry.yml      # Active markets (registry-driven)
│   └── supabase_setup.md        # Supabase project + secrets checklist
├── supabase/migrations/       # SQL schema (applied via apply_supabase_migrations.py)
├── scripts/                   # Migrations, layer contract, registry sync, connection check
├── dbt_analytics/             # dbt project (1_staging → 5_marts)
├── ingestion/                 # Raw data fetch scripts
├── frontend/                  # Streamlit app (app.py)
├── .github/workflows/         # CI + data pipeline
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

3. **Configure Supabase**

   Follow [`docs/supabase_setup.md`](docs/supabase_setup.md): create a project, fill `.env`, then:

   ```bash
   copy .env.example .env
   python scripts/apply_supabase_migrations.py
   python scripts/check_supabase_connection.py
   ```

4. **Markets** — see `docs/market_registry.yml`. After edits, run `python scripts/sync_dbt_vars.py`.

5. **Refresh constituents** (optional — updates seed CSVs from Wikipedia):

   ```bash
   python scripts/refresh_constituents.py
   ```

6. **Run ingestion** (writes parquet to `storage/raw/`):

   ```bash
   python scripts/run_ingestion.py --max-tickers 5   # small local test
   python scripts/run_ingestion.py                   # all active markets
   ```

7. **Transform and export** (after ingestion):

   ```bash
   set DBT_RAW_PATH=storage/raw
   dbt build --project-dir dbt_analytics --profiles-dir .
   python scripts/check_pipeline_completeness.py
   python scripts/export_to_supabase.py
   ```

8. **Streamlit app** (requires Supabase Auth enabled):

   ```bash
   streamlit run frontend/app.py
   ```

## Standards (non-negotiable)

Agent process / guardrails: [`CLAUDE.md`](CLAUDE.md) → [`.claude/working-agreement.md`](.claude/working-agreement.md) (from the [`dbt-agent-kit`](https://github.com/ramialfahham/dbt-agent-kit) plugin).

Engineering standards:

- [`docs/layering.md`](docs/layering.md) — dbt layer rules
- [`docs/engineering_standards.md`](docs/engineering_standards.md) — naming, testing, CI
- [`docs/working_agreement.md`](docs/working_agreement.md) — UX PR gate (frontend changes)

Stock-specific extensions:

- [`docs/project_context.md`](docs/project_context.md) — markets, DuckDB, ingestion, Supabase export

## Project conventions

- No business logic in ingestion — raw fields only
- All credentials via `.env` + python-dotenv
- dbt layers: `1_staging/` → `2_base/` → `3_core/` → `4_intermediate/` → `5_marts/`
- Never commit `.env` or `profiles.yml`
- Every PR must pass `ci-validate`
