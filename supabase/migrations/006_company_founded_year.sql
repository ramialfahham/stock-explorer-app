-- Add Yahoo founded year for card plain-summary prefix.

alter table public.mart_stock_cards
    add column if not exists company_founded_year bigint;
