-- Register France (CAC 40) in public.markets.
-- Applied by scripts/apply_supabase_migrations.py
--
-- WHY THIS IS REQUIRED, not optional. `public.markets` is seeded with five rows in
-- 001_initial_schema.sql and nothing has added one since. Three tables carry a foreign key to
-- it: mart_stock_cards (declared in 001, recreated in 002), user_interactions (001) and
-- card_assessments (010).
-- scripts/export_to_supabase.py upserts mart_stock_cards only and never touches markets, so
-- the first 500-row batch containing an fr_cac40 row would raise a foreign-key violation,
-- abort the export for EVERY market, and stop generate_assessments.py from running at all.
--
-- No CI job exercises the production export, so that failure would appear for the first time
-- on the scheduled run with every check green beforehand.
--
-- The market activation checklist in docs/data_contract.md used to offer "Add Supabase
-- markets row (or rely on export upsert)". The parenthetical does not hold in this codebase:
-- there is no upsert path to markets. The checklist has been corrected alongside this
-- migration so the next nine activations do not repeat it.
--
-- No insert-on-conflict precedent exists in this repo: 002_fundamentals_mart.sql activated
-- de_dax with an UPDATE, because 001 had already inserted that row. A new market has no row to
-- update, so this inserts, and is idempotent via on conflict so a re-apply is harmless.
insert into public.markets (market_code, index_name, exchange_suffix, source, ingest_active)
values ('fr_cac40', '^FCHI', '.PA', 'yfinance', true)
on conflict (market_code) do update
set index_name = excluded.index_name,
    exchange_suffix = excluded.exchange_suffix,
    source = excluded.source,
    ingest_active = excluded.ingest_active,
    updated_at = now();
