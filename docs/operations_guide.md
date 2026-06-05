# Operations guide — Stock Swipe App

How production data moves and how to respond when it breaks. Product rules live in
[`north_star.md`](north_star.md); field-level contracts in [`data_contract.md`](data_contract.md).

---

## Production architecture

```
GitHub Actions (schedule)
  → refresh constituents (optional / on change)
  → run_ingestion.py (yfinance → parquet)
  → dbt build (DuckDB)
  → check_pipeline_completeness.py
  → export_to_supabase.py
  → Streamlit reads Supabase (anon key)
```

Nothing in this path runs on a developer laptop in production.

---

## Schedules

| Workflow | Trigger | Purpose |
|----------|---------|---------|
| [`ci-validate.yml`](../.github/workflows/ci-validate.yml) | Every PR + push to `main` | Fast integrity checks (Tier A/B) |
| [`data_pipeline.yml`](../.github/workflows/data_pipeline.yml) | Mon 06:00 UTC + `workflow_dispatch` | Full ingest, dbt, completeness, export (Tier C) |

### Verify production pipeline

1. Ensure `SUPABASE_DB_HOST` and `SUPABASE_DB_PORT` are set in GitHub secrets (see below).
   Without them, `apply_supabase_migrations` fails with **HTTP 403** when the Management API
   fallback is used.
2. Actions → **Data Pipeline** → **Run workflow** on `main`.
3. Expect: migrate → ingest → `dbt build` → `check_pipeline_completeness.py` → export.

If migrate fails with 403, use `python scripts/discover_supabase_db_host.py` locally and set
`SUPABASE_DB_HOST` / `SUPABASE_DB_PORT` in repo secrets ([`supabase_setup.md`](supabase_setup.md)).

After a successful export, deploy or refresh the UI: [`streamlit_deploy.md`](streamlit_deploy.md).

News (Phase 2): separate workflow, daily, does not block fundamentals export.

---

## Secrets (GitHub Actions)

| Secret | Used by |
|--------|---------|
| `SUPABASE_URL` | Migrate, data pipeline, export |
| `SUPABASE_DB_PASSWORD` | Migrate, data pipeline |
| `SUPABASE_DB_HOST` | Migrate, data pipeline (Session pooler hostname) |
| `SUPABASE_DB_PORT` | Migrate, data pipeline (usually `5432`) |
| `SUPABASE_ACCESS_TOKEN` | Migrate (optional Management API pooler fallback) |
| `SUPABASE_SERVICE_ROLE_KEY` | Data pipeline export (bypasses RLS) |

Streamlit uses the **anon** key in its own hosting secrets — not in the data pipeline.
See [`supabase_setup.md`](supabase_setup.md) for local `.env` and pooler discovery.

---

## Active markets

Synced from [`market_registry.yml`](market_registry.yml). After registry edits:

```bash
python scripts/sync_dbt_vars.py
python scripts/check_registry_var_sync.py
```

| market_code | Index | Status |
|-------------|-------|--------|
| `us_sp500` | ^GSPC | Active |
| `uk_ftse100` | ^FTSE | Active |
| `jp_nikkei225` | ^N225 | Active (manual seed) |
| `au_asx200` | ^AXJO | Active |
| `de_dax` | ^GDAXI | Active |

**Planned (inactive until coverage audit):** `fr_cac40`, `nl_aex`, `ch_smi`, `es_ibex35`.

---

## Manual operations

### Apply database migrations

```bash
python scripts/apply_supabase_migrations.py
python scripts/apply_supabase_migrations.py --dry-run
```

Also runs automatically via GitHub Actions (`supabase-migrate` workflow) when migration
files change on `main`, and before the data pipeline export step.

### Refresh constituents

```bash
python scripts/refresh_constituents.py
python scripts/refresh_constituents.py --market de_dax
```

### Audit yfinance coverage (before full ingest)

```bash
python scripts/audit_yfinance_coverage.py --market us_sp500 --sample-size 10
python scripts/audit_yfinance_coverage.py   # all active markets, 10 tickers each
```

Informational only — shows per-field hit rates and estimated card eligibility.

### Run ingestion locally

```bash
python scripts/run_ingestion.py --max-tickers 3 --delay-seconds 0   # smoke (fast)
python scripts/run_ingestion.py --market us_sp500                   # one market (default 0.25s delay)
python scripts/run_ingestion.py                                     # all markets; long run
```

Use `--delay-seconds` (default `0.25`) to reduce Yahoo 429 rate limits on fundamentals.
Run per-market if a full run hits rate limits.

### Full local transform (when models exist)

```bash
dbt build --project-dir dbt_analytics --profiles-dir .
```

### Completeness check (post-dbt)

```bash
python scripts/check_pipeline_completeness.py
python scripts/check_pipeline_completeness.py --duckdb-path storage/stock_data.db
```

---

## Failure playbooks

### Pipeline failed on completeness gate

1. Check logs for which market failed (eligible count vs raw missing).
2. If yfinance outage: re-run workflow; Supabase retains last export.
3. If single market degraded: set `ingest_active: false` temporarily, sync dbt vars, re-run.
4. Do not export partial empty tables over good data.

### Registry / dbt var drift

CI fails `check_registry_var_sync.py`. Run `sync_dbt_vars.py` and commit.

### New Supabase migration

Run SQL from `supabase/migrations/` via `python scripts/apply_supabase_migrations.py` or the
`supabase-migrate` GitHub Action — not the Dashboard SQL Editor. See [`supabase_setup.md`](supabase_setup.md).

---

## Monitoring (v1)

Until dashboards exist, rely on:

- GitHub Actions run status on `main`
- Completeness script stdout (eligible counts per market)
- Manual spot-check in Supabase table editor after export ships

Target: every active market **≥ 20** card-eligible tickers (warn below, fail below 5).
