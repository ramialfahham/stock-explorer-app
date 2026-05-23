# Supabase setup

Phase 2 checklist for the Stock Swipe App warehouse and auth backend.

## 1. Create a Supabase project

1. Go to [supabase.com/dashboard](https://supabase.com/dashboard) and sign in.
2. **New project** → pick an org, name (e.g. `stock-swipe-app`), database password, region.
3. Wait for the project to finish provisioning.

## 2. Run the initial schema

1. Open **SQL Editor** in the Supabase dashboard.
2. Paste the contents of [`supabase/migrations/001_initial_schema.sql`](../supabase/migrations/001_initial_schema.sql).
3. Click **Run**.

This creates:

| Table | Purpose |
|---|---|
| `markets` | Registry mirror (seeded from `docs/market_registry.yml`) |
| `mart_stock_cards` | Export target for dbt marts → Streamlit card UI |
| `user_interactions` | Save / skip events per authenticated user |

Row Level Security is enabled: stock data is publicly readable; interactions are scoped to the signed-in user. The service role key (used in CI) bypasses RLS.

## 3. Configure local `.env`

1. In Supabase: **Project Settings → API**.
2. Copy **Project URL**, **anon public** key, and **service_role** key.
3. Locally:

   ```bash
   copy .env.example .env
   ```

4. Fill in `.env`:

   ```
   SUPABASE_URL=https://xxxxxxxx.supabase.co
   SUPABASE_ANON_KEY=eyJ...
   SUPABASE_SERVICE_ROLE_KEY=eyJ...
   ```

5. Verify:

   ```bash
   venv\Scripts\activate
   python scripts/check_supabase_connection.py
   ```

## 4. GitHub Actions secrets

In [github.com/ramialfahham/stock-swipe-app/settings/secrets/actions](https://github.com/ramialfahham/stock-swipe-app/settings/secrets/actions), add:

| Secret | Value |
|---|---|
| `SUPABASE_URL` | Project URL from Supabase API settings |
| `SUPABASE_SERVICE_ROLE_KEY` | service_role key (never expose in frontend or git) |

These will be used by the export step in `.github/workflows/data_pipeline.yml` once ingestion and dbt are implemented.

Via CLI:

```bash
gh secret set SUPABASE_URL --body "https://xxxxxxxx.supabase.co"
gh secret set SUPABASE_SERVICE_ROLE_KEY --body "eyJ..."
```

## 5. Streamlit Community Cloud (later)

When deploying the frontend, add the same three variables in the Streamlit app secrets. Use the **anon** key in production UI — not the service role key.

## 6. Auth (later)

User sign-up is handled by Supabase Auth. Enable your preferred providers under **Authentication → Providers**. The `user_interactions` table expects `auth.users` UUIDs from authenticated sessions.
