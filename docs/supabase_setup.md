# Supabase setup

Phase 2 checklist for the Stock Swipe App warehouse and auth backend.

**No manual SQL in the Dashboard.** Schema changes live in `supabase/migrations/` and are
applied by `scripts/apply_supabase_migrations.py` (locally or via GitHub Actions).

---

## 1. Create a Supabase project

1. Go to [supabase.com/dashboard](https://supabase.com/dashboard) and sign in.
2. **New project** → pick an org, name (e.g. `stock-swipe-app`), database password, region.
3. Wait for the project to finish provisioning.

This is the only step that requires the Supabase UI.

---

## 2. Configure local `.env`

1. In Supabase: **Project Settings → API** — copy **Project URL**, **anon** key, **service_role** key.
2. In **Project Settings → Database** — copy the **database password** (the one you set at create time).
3. Locally:

   ```bash
   copy .env.example .env
   ```

4. Fill in `.env`:

   ```
   SUPABASE_URL=https://xxxxxxxx.supabase.co
   SUPABASE_ANON_KEY=eyJ...
   SUPABASE_SERVICE_ROLE_KEY=eyJ...
   SUPABASE_DB_PASSWORD=your-database-password
   ```

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
the existing schema, records `001` as applied, and only runs newer migrations (e.g. `002`).

---

## 3. GitHub Actions secrets

In your repo **Settings → Secrets and variables → Actions**, add:

| Secret | Value |
|--------|--------|
| `SUPABASE_URL` | Project URL |
| `SUPABASE_DB_PASSWORD` | Database password |
| `SUPABASE_SERVICE_ROLE_KEY` | service_role key (data pipeline export) |

When migration files change on `main`, [`.github/workflows/supabase-migrate.yml`](../.github/workflows/supabase-migrate.yml)
applies them automatically. You can also trigger it manually (**Actions → supabase-migrate → Run workflow**).

Via CLI:

```bash
gh secret set SUPABASE_URL --body "https://xxxxxxxx.supabase.co"
gh secret set SUPABASE_DB_PASSWORD --body "your-database-password"
gh secret set SUPABASE_SERVICE_ROLE_KEY --body "eyJ..."
```

---

## 4. What gets created

| Table | Purpose |
|-------|---------|
| `markets` | Registry mirror (seeded from migrations) |
| `mart_stock_cards` | Export target for dbt marts → Streamlit card UI |
| `user_interactions` | Save / skip events per authenticated user |
| `schema_migrations` | Tracks applied migration files |

Row Level Security: stock data is publicly readable; interactions are scoped to the signed-in user.
The service role key (used in CI) bypasses RLS.

---

## 5. Streamlit Community Cloud (later)

When deploying the frontend, add `SUPABASE_URL` and `SUPABASE_ANON_KEY` in Streamlit app secrets.
Use the **anon** key — not the service role key.

---

## 6. Auth (later)

User sign-up is handled by Supabase Auth. Enable providers under **Authentication → Providers**.
The `user_interactions` table expects `auth.users` UUIDs from authenticated sessions.
