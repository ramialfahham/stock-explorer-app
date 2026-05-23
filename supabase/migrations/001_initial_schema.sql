-- Stock Swipe App — initial Supabase schema
-- Run in Supabase Dashboard → SQL Editor (New query → Run)

-- ---------------------------------------------------------------------------
-- Reference: active markets (aligned with docs/market_registry.yml)
-- ---------------------------------------------------------------------------

create table public.markets (
    market_code text primary key,
    index_name text not null,
    exchange_suffix text not null default '',
    source text not null default 'yfinance',
    ingest_active boolean not null default true,
    updated_at timestamptz not null default now()
);

insert into public.markets (market_code, index_name, exchange_suffix, source, ingest_active)
values
    ('us_sp500', '^GSPC', '', 'yfinance', true),
    ('uk_ftse100', '^FTSE', '.L', 'yfinance', true),
    ('jp_nikkei225', '^N225', '.T', 'yfinance', true),
    ('au_asx200', '^AXJO', '.AX', 'yfinance', true),
    ('de_dax', '^GDAXI', '.DE', 'yfinance', false);

-- ---------------------------------------------------------------------------
-- Mart export target: consumption-ready stock cards for Streamlit
-- ---------------------------------------------------------------------------

create table public.mart_stock_cards (
    id bigint generated always as identity primary key,
    market_code text not null references public.markets (market_code),
    ticker text not null,
    company_name text,
    sector text,
    currency text,
    latest_price numeric(18, 6),
    price_change_1d_pct numeric(10, 4),
    price_change_5d_pct numeric(10, 4),
    snapshot_date date not null,
    exported_at timestamptz not null default now(),
    unique (market_code, ticker, snapshot_date)
);

create index mart_stock_cards_snapshot_date_idx
    on public.mart_stock_cards (snapshot_date desc);

create index mart_stock_cards_market_code_idx
    on public.mart_stock_cards (market_code);

-- ---------------------------------------------------------------------------
-- User interactions (save / skip)
-- ---------------------------------------------------------------------------

create table public.user_interactions (
    id bigint generated always as identity primary key,
    user_id uuid not null references auth.users (id) on delete cascade,
    market_code text not null references public.markets (market_code),
    ticker text not null,
    action text not null check (action in ('save', 'skip')),
    session_id uuid,
    created_at timestamptz not null default now()
);

create index user_interactions_user_id_idx
    on public.user_interactions (user_id, created_at desc);

create index user_interactions_session_id_idx
    on public.user_interactions (session_id);

-- ---------------------------------------------------------------------------
-- Row Level Security
-- ---------------------------------------------------------------------------

alter table public.markets enable row level security;
alter table public.mart_stock_cards enable row level security;
alter table public.user_interactions enable row level security;

-- Public read for stock data (Streamlit anon key)
create policy "markets are readable by everyone"
    on public.markets
    for select
    to anon, authenticated
    using (true);

create policy "stock cards are readable by everyone"
    on public.mart_stock_cards
    for select
    to anon, authenticated
    using (true);

-- Users manage their own interactions
create policy "users can read own interactions"
    on public.user_interactions
    for select
    to authenticated
    using (auth.uid() = user_id);

create policy "users can insert own interactions"
    on public.user_interactions
    for insert
    to authenticated
    with check (auth.uid() = user_id);

-- Service role (GitHub Actions export) bypasses RLS by default.
