-- Stock Explorer -- fundamentals mart + DAX activation
-- Applied by scripts/apply_supabase_migrations.py

-- ---------------------------------------------------------------------------
-- Activate DAX (aligned with docs/market_registry.yml)
-- ---------------------------------------------------------------------------

update public.markets
set ingest_active = true, updated_at = now()
where market_code = 'de_dax';

-- ---------------------------------------------------------------------------
-- Replace price-based mart with fundamentals card contract
-- Safe when mart is empty or pre-launch; drops legacy price columns.
-- ---------------------------------------------------------------------------

drop table if exists public.mart_stock_cards;

create table public.mart_stock_cards (
    id bigint generated always as identity primary key,
    market_code text not null references public.markets (market_code),
    ticker text not null,
    company_name text,
    sector text,
    currency text,
    forward_pe numeric(18, 6),
    ebit_margin_pct numeric(10, 4),
    revenue_growth_yoy_pct numeric(10, 4),
    net_debt_to_ebitda numeric(18, 6),
    fcf_margin_pct numeric(10, 4),
    is_card_eligible boolean not null default false,
    sector_peer_count integer,
    sector_median_forward_pe numeric(18, 6),
    sector_median_ebit_margin_pct numeric(10, 4),
    sector_median_revenue_growth_yoy_pct numeric(10, 4),
    sector_median_net_debt_to_ebitda numeric(18, 6),
    sector_median_fcf_margin_pct numeric(10, 4),
    snapshot_date date not null,
    exported_at timestamptz not null default now(),
    unique (market_code, ticker, snapshot_date)
);

create index mart_stock_cards_snapshot_date_idx
    on public.mart_stock_cards (snapshot_date desc);

create index mart_stock_cards_market_code_idx
    on public.mart_stock_cards (market_code);

create index mart_stock_cards_eligible_idx
    on public.mart_stock_cards (market_code, is_card_eligible)
    where is_card_eligible = true;

alter table public.mart_stock_cards enable row level security;

create policy "stock cards are readable by everyone"
    on public.mart_stock_cards
    for select
    to anon, authenticated
    using (true);
