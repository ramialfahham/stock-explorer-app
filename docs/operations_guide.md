# Operations guide — Stock Swipe App

How production data moves and how to respond when it breaks. Product rules live in
[`north_star.md`](north_star.md); field-level contracts in [`data_contract.md`](data_contract.md).

---

## Production architecture

```
GitLab CI (schedule)
  → refresh constituents (optional / on change)
  → run_ingestion.py (yfinance → parquet)
  → dbt build (DuckDB)
  → check_pipeline_completeness.py
  → check_eligibility_baseline.py
  → check_export_health.py
  → export_to_supabase.py
  → Streamlit reads Supabase (anon key)
```

Nothing in this path runs on a developer laptop in production.

---

## Schedules

| Job | Trigger | Purpose |
|-----|---------|---------|
| [`validate:full`](../.gitlab-ci.yml) | Every MR + push to `main` | Fast integrity checks (Tier A/B) |
| [`data-pipeline`](../.gitlab-ci.yml) | 1st/15th 06:00 UTC pipeline schedule + manual web dispatch | Full ingest, dbt, completeness, export (Tier C) |

### Verify production pipeline

1. Ensure `SUPABASE_DB_HOST` and `SUPABASE_DB_PORT` are set as GitLab CI/CD variables (see
   below), **Protected** (they're only needed by protected-branch pipelines). Without them,
   `apply_supabase_migrations` fails with **HTTP 403** when the Management API fallback is used.
2. CI/CD → Pipelines → **Run pipeline** on `main` (this is a `web`-source dispatch; the
   `data-pipeline` job appears with a manual play button — click it to actually start it).
3. Expect: migrate → ingest → `dbt build` → completeness → eligibility baseline → export health → export.

If migrate fails with 403, use `python scripts/discover_supabase_db_host.py` locally and set
`SUPABASE_DB_HOST` / `SUPABASE_DB_PORT` as GitLab CI/CD variables ([`supabase_setup.md`](supabase_setup.md)).

After a successful export, deploy or refresh the UI: [`streamlit_deploy.md`](streamlit_deploy.md).

**Saved-tab headlines:** fetched on demand when the user opens a saved company (yfinance,
session cache ~1 hour). Not part of the scheduled fundamentals pipeline and not shown on Discover.

---

## CI/CD variables (GitLab)

Unlike GitHub Actions' per-step `secrets:` mapping, GitLab injects every project CI/CD
variable into every job. These must be marked **Protected** — that's what limits them to
the two jobs that actually use them (`supabase-migrate`, `data-pipeline`, both restricted to
protected-branch pipelines), and it only works if `main` is genuinely a protected branch.

| Variable | Used by |
|--------|---------|
| `SUPABASE_URL` | Migrate, data pipeline, export |
| `SUPABASE_DB_PASSWORD` | Migrate, data pipeline |
| `SUPABASE_DB_HOST` | Migrate, data pipeline (Session pooler hostname) |
| `SUPABASE_DB_PORT` | Migrate, data pipeline (usually `5432`) |
| `SUPABASE_ACCESS_TOKEN` | Migrate (optional Management API pooler fallback) |
| `SUPABASE_SERVICE_ROLE_KEY` | Data pipeline export (bypasses RLS — still needs the table-level `GRANT`s in `supabase/migrations/011_grant_roles.sql`; see `supabase_setup.md`) |
| `ANTHROPIC_API_KEY` | Data pipeline (assessment prose reads; soft dependency — skipped when unset) |

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
| `fr_cac40` | ^FCHI | Active |

**Planned (inactive until coverage audit):** `nl_aex`, `ch_smi`, `es_ibex35`, plus Finland,
Sweden, Denmark, Norway (OBX), Canada (TSX 60) and Italy (FTSE MIB), which are agreed but not
yet in the registry.

---

## Manual operations

### Apply database migrations

```bash
python scripts/apply_supabase_migrations.py
python scripts/apply_supabase_migrations.py --dry-run
```

Also runs automatically via GitLab CI (`supabase-migrate` job) when migration
files change on `main`, and before the data pipeline export step.

### Test a migration or export change before it ships

Add `--target dev` to either script to write to a `dev` schema in the same Supabase
project instead of `public` — no separate project, no new secret. See
[`supabase_setup.md`](supabase_setup.md#3b-testing-against-a-dev-schema) for the one-time
setup step and the `dev-schema-check` CI button.

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
2. If yfinance outage: retry the pipeline; Supabase retains last export.
3. If single market degraded: set `ingest_active: false` temporarily, sync dbt vars, re-run.
4. Do not export partial empty tables over good data.

### Registry / dbt var drift

CI fails `check_registry_var_sync.py`. Run `sync_dbt_vars.py` and commit.

### New Supabase migration

Run SQL from `supabase/migrations/` via `python scripts/apply_supabase_migrations.py` or the
`supabase-migrate` GitLab CI job — not the Dashboard SQL Editor. See [`supabase_setup.md`](supabase_setup.md).

---

## Monitoring (v1)

Until dashboards exist, rely on:

- GitLab CI pipeline status on `main`
- Completeness script stdout (eligible counts per market)
- Manual spot-check in Supabase table editor after export ships

Target: every active market **≥ 20** card-eligible tickers (warn below, fail below 5).
