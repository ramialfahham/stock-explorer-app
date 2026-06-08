-- Add Yahoo longBusinessSummary to mart export for card company context.

alter table public.mart_stock_cards
    add column if not exists business_summary text;
