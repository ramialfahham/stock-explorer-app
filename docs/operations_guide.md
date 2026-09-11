# Operations guide — Stock Swipe App

> DURABLE. **Owns:** how production data moves, and the runbook for when it breaks.
> **Never:** product rules or metric definitions.

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
| `nl_aex` | ^AEX | Active |
| `ch_smi` | ^SSMI | Active |
| `es_ibex35` | ^IBEX | Active |

**Planned (inactive until coverage audit):** Finland, Sweden (OMXS 30), Denmark, Norway (OBX),
Canada (TSX 60) and Italy (FTSE MIB), all agreed but not yet in the registry.

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

A ticker already fetched into today's (UTC) raw parquet is skipped on a re-run, not
refetched -- a re-run after a partial failure resumes rather than starting over, and a
suspiciously-fast run after an earlier one the same day is this, not a bug. Add
`--force-refetch` to ignore same-day cached output and refetch every ticker anyway. Freshness
is tracked by a same-named `.checkpoint` file next to each raw parquet (gitignored along with
the rest of `storage/raw/`), not the parquet's own timestamp -- other scripts that write these
same paths (`seed_ci_raw_fixtures.py`, `backfill_fundamentals_parquet_schema.py`) never touch
it, so a same-day write from one of them, before real ingestion runs, can't be mistaken for a
completed run.

Not covered by the marker: running one of those scripts against a real market_code AFTER real
ingestion already ran the same day. The marker still reads fresh (ingestion wrote it), but the
parquet content is no longer what ingestion produced. This is a narrow, deliberate action
sequence, not a normal workflow -- if data looks wrong and this ordering is suspected, use
`--force-refetch` rather than trusting the checkpoint.

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

**Pipeline failure email -- DONE.** Set via GitLab's built-in per-user notifications, not the
"Pipeline emails" project integration this guide previously described. The owner reported that
integration is not in the project's Settings → Integrations list (2026-09-08). The API is
consistent with that but does not prove it: `GET /integrations` returns only ACTIVATED
integrations (`[]` here) and the per-integration endpoint 404s for anything never configured,
so the API evidence establishes only that it was never set up -- which the old instruction
already admitted, having sat here as an unchecked pending action. The route that works: the
project's
notification dropdown (bell icon) → **Custom** → tick **Failed pipeline** (and **Fixed
pipeline**), reachable also at <https://gitlab.com/-/profile/notifications>.

Being per-user, it emails the account that set it rather than a configured recipient list --
for a solo project, the same outcome, but a second maintainer would have to set their own. It
is pipeline-level, not job-level: a `supabase-migrate` or `validate:*` failure on `main`
triggers the same email as a `data-pipeline` failure. It does **not** catch the schedule
silently never firing at all (a dead-man's-switch gap -- nothing runs, so there is nothing to
alert from); no zero-dependency fix exists for that today.

### Keep-alive monitors (UptimeRobot)

**Two monitors, and both are needed -- they cover different things that sleep independently.**

| Monitor | URL | Covers |
|---|---|---|
| App | `stock-explorer-app.onrender.com`, HTTP, 5 min | Render's free tier sleeps the web service after ~15 min idle |
| Database | `<SUPABASE_URL>/rest/v1/mart_stock_cards?select=ticker&limit=1&apikey=<publishable key>`, HTTP | Supabase's free tier pauses the project after ~7 days with no activity; any interval well under 7 days suffices |

**The app monitor does not keep the database awake, and this is not obvious.** A plain HTTP
request to a Streamlit app returns only the static page shell; Streamlit runs the app script
(and therefore any Supabase query) when a browser opens a websocket, which a monitor never
does. Verified 2026-09-08: the response body contains no card data at all. So an app-only
ping leaves the database entirely uncovered, which was the state until the second monitor was
added that day.

The database monitor's configured check interval was not captured when it was set up; only
the requirement above (well under 7 days) is known.

**Not yet observed working.** The database monitor was added 2026-09-08 and its effect cannot
show up for ~7 days. To verify: check that the Supabase project still serves a REST request
more than 7 days after the last pipeline write (writes land on the 1st and 15th), without
anyone having visited the app in between.

The database URL carries the `sb_publishable_` key as a query parameter. That is acceptable
because the key is publishable by design and because `mart_stock_cards` has row-level security
with a select-only policy for `anon` (`supabase/migrations/001_initial_schema.sql`,
`011_grant_roles.sql`). Note it is NOT acceptable on the grounds that the key already reaches
browsers -- it does not: Streamlit builds the Supabase client server-side
(`frontend/supabase_client.py`), so the key never leaves the server. Putting it in a monitor
URL genuinely widens where it exists. What makes that acceptable is primarily that the key is
publishable by design; the select-only `anon` policy limits what it can do against the REST
API specifically, and is not the control on every surface the key reaches. The `sb_secret_`
key must never be used here. Supabase's `/auth/v1/health` endpoint
was tried first to avoid a key in the URL and returns 401 without one, so it would read as
permanently down.

Beyond the email and the monitors, rely on:

- GitLab CI pipeline status on `main`
- Completeness script stdout (eligible counts per market)
- Manual spot-check in Supabase table editor after export ships

Target: every active market **≥ 20** card-eligible tickers (warn below, fail below 5).
