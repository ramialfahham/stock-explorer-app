-- Explicit role grants — previously implicit via "Automatically expose new tables" on
-- project creation, which the owner now deliberately disables on new projects (manual
-- access control, per Supabase's own recommendation). RLS policies only restrict which
-- rows a role can touch; the underlying table-level GRANT is still required regardless,
-- and prior migrations' "service role bypasses RLS by default" comments assumed a grant
-- that a project without that setting never receives.
--
-- Matches each table's existing RLS policy exactly — no broader access than what's
-- already declared readable/writable in 001/002/010.

grant select on public.markets to anon, authenticated;
grant select on public.mart_stock_cards to anon, authenticated;
grant select on public.card_assessments to anon, authenticated;

grant select, insert on public.user_interactions to authenticated;

-- Service role: written by scripts/export_to_supabase.py (mart_stock_cards) and
-- scripts/generate_assessments.py (card_assessments upsert).
grant select, insert, update on public.mart_stock_cards to service_role;
grant select, insert, update on public.card_assessments to service_role;

-- Service role: read-only, needed by scripts/check_supabase_connection.py — the
-- documented post-migration verification step prefers SUPABASE_SERVICE_ROLE_KEY when
-- set and selects from markets/mart_stock_cards/user_interactions.
grant select on public.markets to service_role;
grant select on public.user_interactions to service_role;
