-- Lock migration tracking table from PostgREST (anon/authenticated).
-- Applied by scripts/apply_supabase_migrations.py

alter table public.schema_migrations enable row level security;

-- No policies: API roles cannot read or write; postgres (migrations) and service_role still work.
