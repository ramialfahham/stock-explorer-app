-- Register Finland (OMX Helsinki 25), Sweden (OMX Stockholm 30), Denmark (OMX Copenhagen 25),
-- Norway (OBX), Canada (S&P/TSX 60) and Italy (FTSE MIB) in public.markets.
-- Applied by scripts/apply_supabase_migrations.py
--
-- REQUIRED, not optional. Three tables foreign-key to public.markets (mart_stock_cards,
-- user_interactions, card_assessments) and scripts/export_to_supabase.py writes the mart only,
-- never markets. A missing row aborts the export for EVERY market on the next production run,
-- and no CI job exercises that path. See 014_fr_cac40_market.sql for the same reasoning.
--
-- market_code is FIRST in each VALUES tuple and every value matches docs/market_registry.yml:
-- tests/ingestion/test_market_onboarding.py checks both, and its migration scan is a text match
-- rather than a SQL parser, so a different column order fails closed.
--
-- Idempotent via on conflict, so a re-apply after an interrupted run is harmless.
insert into public.markets (market_code, index_name, exchange_suffix, source, ingest_active)
values
    ('fi_omxh25', '^OMXH25', '.HE', 'yfinance', true),
    ('se_omxs30', '^OMX', '.ST', 'yfinance', true),
    ('dk_omxc25', '^OMXC25', '.CO', 'yfinance', true),
    ('no_obx', 'OBX.OL', '.OL', 'yfinance', true),
    ('ca_tsx60', 'TX60.TS', '.TO', 'yfinance', true),
    ('it_ftsemib', 'FTSEMIB.MI', '.MI', 'yfinance', true)
on conflict (market_code) do update
set index_name = excluded.index_name,
    exchange_suffix = excluded.exchange_suffix,
    source = excluded.source,
    ingest_active = excluded.ingest_active,
    updated_at = now();
