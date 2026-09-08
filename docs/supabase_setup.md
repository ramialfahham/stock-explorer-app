# Supabase setup

Phase 2 checklist for the Stock Swipe App warehouse and auth backend.

**No manual SQL in the Dashboard.** Schema changes live in `supabase/migrations/` and are
applied by `scripts/apply_supabase_migrations.py` (locally or via GitLab CI).

---

## 1. Create a Supabase project

1. Go to [supabase.com/dashboard](https://supabase.com/dashboard) and sign in.
2. **New project** → pick an org, name (e.g. `stock-swipe-app`), database password, region.
3. **"Automatically expose new tables"** — leave this **unchecked** (Supabase's own
   recommendation; deliberate access control instead of exposing every table by default).
   This means `service_role`/`anon`/`authenticated` get **no implicit table privileges** —
   `supabase/migrations/011_grant_roles.sql` grants exactly what each table's RLS policy
   already declares. If a future migration adds a new table those roles need to touch, a
   matching `GRANT` has to be added explicitly; nothing grants it automatically.
4. Wait for the project to finish provisioning.

This is the only step that requires the Supabase UI.

---

## 2. Configure local `.env`

1. In Supabase: **Project Settings → API** — copy **Project URL**, **anon** key, **service_role** key.
2. In **Project Settings → Database** — copy the **database password** (the one you set at create time).
3. Locally:

   ```bash
   copy .env.example .env
   ```

4. Fill in `.env` (see [`.env.example`](../.env.example) for all keys).
5. Apply migrations (creates tables, RLS, seeds `markets`):

   ```bash
   pip install -r requirements.txt
   python scripts/apply_supabase_migrations.py
   ```

6. Verify:

   ```bash
   python scripts/check_supabase_connection.py
   ```

If you previously ran `001_initial_schema.sql` manually in the Dashboard, the script detects
the existing schema, records `001` as applied, and only runs newer migrations.

### Migrations on disk

| File | Purpose |
|------|---------|
| `001_initial_schema.sql` | Markets, legacy mart, `user_interactions`, RLS |
| `002_fundamentals_mart.sql` | Fundamentals `mart_stock_cards`, DAX active |
| `003_lock_schema_migrations.sql` | RLS on `schema_migrations` (no API policies) |
| `004_business_summary.sql` | `business_summary` text on mart (Yahoo longBusinessSummary) |
| `005_ebit_margin_basis.sql` | `ebit_margin_basis` on mart |
| `006_company_founded_year.sql` | `company_founded_year` on mart (optional; not shown on card yet) |
| `007_router_card_columns.sql` | `company_type` + operating-card solvency/liquidity/returns columns (Sector Router 4a) |
| `008_financial_card_metrics.sql` | Financial/bank-card metric columns (Sector Router 4b) |
| `009_pre_revenue_card_metrics.sql` | Pre-revenue/survival-card metric columns (Sector Router 4c) |
| `010_card_assessments.sql` | `card_assessments` table — health verdict + AI read (Slice 5) |
| `011_grant_roles.sql` | Explicit role grants — needed when "automatically expose new tables" (step 1) is off |
| `014_fr_cac40_market.sql` | France (CAC 40) row in `public.markets`. Required: three tables foreign-key to it and the export never inserts one |
| `015_nl_ch_es_markets.sql` | Netherlands (AEX), Switzerland (SMI), Spain (IBEX 35) rows in `public.markets`. Same requirement as 014 |

`012_sector_benchmark_min_max.sql` and `013_net_cash.sql` exist on disk but are missing from
this table. That gap predates the France work and is left rather than backfilled here, so
the omission is not mistaken for an error in the migration sequence.

After applying **004+**, run the data pipeline (ingest → dbt → export) so Streamlit receives
company descriptions. The app holds its deck in an in-process cache shared by all browser
sessions, with a 30-minute TTL, so neither a hard refresh nor a new browser session is enough
to pull a fresh export before that window elapses. Restarting the Streamlit process clears it
immediately.

---

## 3. GitLab CI/CD variables

In your project **Settings → CI/CD → Variables**, add each below. Mark each **Protected**
(GitLab injects every variable into every job by default — Protected is what limits these to
protected-branch pipelines, i.e. the `supabase-migrate` and `data-pipeline` jobs; this only
takes effect if `main` is actually a protected branch — verify with `glab api
projects/<NAMESPACE>%2F<REPO>/protected_branches`). None of these need **Masked** beyond
what GitLab requires by value shape; the service role key and DB password are still
sensitive and should stay Protected regardless.

| Variable | Used by | Notes |
|--------|---------|--------|
| `SUPABASE_URL` | Migrate, data pipeline, export | Project URL |
| `SUPABASE_DB_PASSWORD` | Migrate, data pipeline | Database password |
| `SUPABASE_DB_HOST` | Migrate, data pipeline | **Session pooler hostname only** (recommended for CI) |
| `SUPABASE_DB_PORT` | Migrate, data pipeline | Usually `5432` (Session pooler) |
| `SUPABASE_SERVICE_ROLE_KEY` | Data pipeline export | Bypasses RLS — still needs the table-level `GRANT`s in `011_grant_roles.sql` |
| `SUPABASE_ACCESS_TOKEN` | Migrate (optional) | Personal access token; Management API pooler lookup **fallback only** |

### CI migrations — recommended: host + port (not full URI)

GitLab's shared runners cannot reach the direct `db.*.supabase.co` host (IPv6). Use the
**Session pooler**:

1. Locally, discover the correct pooler host for your project:

   ```bash
   python scripts/discover_supabase_db_host.py
   ```

2. Set GitLab CI/CD variables from the script output:
   - `SUPABASE_DB_HOST` — hostname only (e.g. `aws-1-eu-central-2.pooler.supabase.com`)
   - `SUPABASE_DB_PORT` — `5432` unless the script reports otherwise
   - `SUPABASE_URL` and `SUPABASE_DB_PASSWORD` — as above

3. Re-run **supabase-migrate** (CI/CD → Pipelines → Run pipeline, `web` source, then click
   its manual play button).

[`scripts/apply_supabase_migrations.py`](../scripts/apply_supabase_migrations.py) resolution order:

1. `SUPABASE_URL` + `SUPABASE_DB_PASSWORD` + `SUPABASE_DB_HOST` (+ optional `SUPABASE_DB_PORT`) — **use this in CI**
2. **CI only:** same URL/password + `SUPABASE_ACCESS_TOKEN` → Management API pooler lookup (may return **403** if token lacks scope)
3. `SUPABASE_DB_URL` or `SUPABASE_DB_POOLER_URL` (full Postgres URI)
4. Local fallback: direct `db.{ref}.supabase.co:5432`

Pooler username format: **`postgres.{project_ref}`** (not `postgres` alone).

### Alternative: full pooler URI

If you prefer one secret instead of host/port:

1. Supabase Dashboard → **Project Settings → Database** → **Connection string** → **Session pooler**
2. Copy the URI and replace `[YOUR-PASSWORD]` with your database password
3. Add as `SUPABASE_DB_URL` in `.env` or as a GitLab CI/CD variable

Locally you can use direct connection (`SUPABASE_URL` + `SUPABASE_DB_PASSWORD`) or the same pooler URI.

### Management API 403 troubleshooting

If CI fails with `HTTP Error 403: Forbidden` on pooler config:

- Set `SUPABASE_DB_HOST` / `SUPABASE_DB_PORT` (skip the API), or
- Regenerate a personal access token at [Account → Access Tokens](https://supabase.com/dashboard/account/tokens) and test:

  ```bash
  python scripts/print_supabase_pooler_config.py
  ```

When migration files change on `main`, the [`supabase-migrate`](../.gitlab-ci.yml) job
applies them automatically. You can also trigger it manually (**CI/CD → Pipelines → Run
pipeline**, then the job's play button).

---

## 3b. Testing against a dev schema

There's one Supabase project, and it's production — `--dry-run` on either script skips the
write entirely, it doesn't exercise one. `--target dev` gives both scripts a safe place to
write for real, inside the *same* project (same `SUPABASE_URL` / credentials, no new secret):

```bash
python scripts/apply_supabase_migrations.py --target dev   # creates + populates dev.*
python scripts/export_to_supabase.py --target dev --duckdb-path storage/stock_data.db
```

`prod` (the default, unchanged) writes to `public.*` — what Streamlit reads. `dev` writes to
`dev.*`, created on first run by rewriting each migration file's `public.` references at
execution time; the files on disk never change, so a future migration works against both
targets automatically.

**One manual step, once, for the export half only:** `export_to_supabase.py` goes through
PostgREST, which only serves schemas explicitly listed in **Settings → API → Exposed
schemas** in the Supabase dashboard — add `dev` there. `apply_supabase_migrations.py` is a
raw Postgres connection and needs no such step.

**CI button:** the same check runs as [`dev-schema-check`](../.gitlab-ci.yml) — **CI/CD →
Pipelines → Run pipeline**, then that job's manual play button. Never runs automatically.

---

## 4. What gets created

| Table | Purpose |
|-------|---------|
| `markets` | Registry mirror (seeded from migrations) |
| `mart_stock_cards` | Export target for dbt marts → Streamlit card UI |
| `user_interactions` | Save / skip events per authenticated user |
| `schema_migrations` | Tracks applied migration files |

Row Level Security: stock data is publicly readable; interactions are scoped to the signed-in user.
`schema_migrations` has RLS enabled with no policies (not exposed via the anon key).
The service role key (used in CI export) bypasses RLS — but RLS bypass is not a substitute
for the table-level `GRANT`, which Postgres still enforces regardless of RLS. On a project
with "automatically expose new tables" off (step 1), nothing grants that privilege
implicitly; `supabase/migrations/011_grant_roles.sql` grants it explicitly, matching each
table's RLS policy scope exactly.

---

## 5. Deploy (Render)

Full checklist: [`streamlit_deploy.md`](streamlit_deploy.md).

1. Connect GitLab in Render and select this repo — the service config (build/start command,
   Python version) comes from the committed [`render.yaml`](../render.yaml) Blueprint.
2. When Render prompts for the two `sync: false` env vars, set `SUPABASE_URL` and
   `SUPABASE_ANON_KEY` (see `.streamlit/secrets.toml.example`).

Use the **anon** key — not the service role key.

---

## 6. Auth (Streamlit) — deferred

v1 Streamlit does **not** require login. The app reads `mart_stock_cards` with the anon key (public read RLS). Save and skip are stored in **browser localStorage** on the device.

The `user_interactions` table and auth-backed RLS remain in the schema for a future release when accounts are added. No Supabase Auth provider setup is required to deploy v1.

Run locally from the repo root:

```bash
streamlit run frontend/app.py
```
