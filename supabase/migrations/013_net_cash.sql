-- Net cash as a money amount (cash minus total debt), replacing net_cash_to_market_cap on
-- the pre-revenue card. The ratio divided by market cap, so it moved with the share price;
-- this pipeline refreshes twice a month and cannot keep a price-derived figure current.
--
-- net_cash_to_market_cap is deliberately NOT dropped. It is simply no longer catalogued, so
-- no card renders it, and the column stays available in the warehouse. Dropping it would
-- reach through every dbt layer for no benefit today.
--
-- No GRANT statement is needed for an added COLUMN -- table-level privileges from
-- 011_grant_roles.sql already cover it. A new TABLE would need its own grants: this project
-- has "Automatically expose new tables" switched off, so nothing is granted implicitly.
-- See docs/supabase_setup.md.
alter table public.mart_stock_cards
    add column if not exists net_cash numeric;

comment on column public.mart_stock_cards.net_cash is
    'Cash and equivalents minus total debt, in the company reporting currency. Pre-revenue card metric; replaced net_cash_to_market_cap 2026-08-26.';
