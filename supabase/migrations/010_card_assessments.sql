-- Card assessments — AI health assessment per card (Sector/Lifecycle Router, Slice 5).
-- Applied by scripts/apply_supabase_migrations.py (auto-discovered NNN_*.sql).
--
-- 5a writes the deterministic per-type health verdict (green|yellow|red) + input_hash via
-- scripts/generate_assessments.py. 5b fills ai_read/read_model (Claude Haiku prose read),
-- regenerating only when input_hash changes. Educational only — NOT investment advice.

create table if not exists public.card_assessments (
    id bigint generated always as identity primary key,
    market_code text not null references public.markets (market_code),
    ticker text not null,
    company_type text not null,
    health_verdict text not null check (health_verdict in ('green', 'yellow', 'red')),
    ai_read text,               -- LLM prose read; null until Slice 5b
    read_model text,            -- model id that wrote ai_read; null until Slice 5b
    input_hash text not null,   -- sha256 of the verdict inputs; drives 5b regenerate-on-change
    snapshot_date date not null,
    generated_at timestamptz not null default now(),
    unique (market_code, ticker)
);

create index card_assessments_market_code_idx
    on public.card_assessments (market_code);

create index card_assessments_verdict_idx
    on public.card_assessments (health_verdict);

alter table public.card_assessments enable row level security;

-- Public read for the Streamlit anon key (like mart_stock_cards). Service-role writes
-- (scripts/generate_assessments.py) bypass RLS by default.
create policy "card assessments are readable by everyone"
    on public.card_assessments
    for select
    to anon, authenticated
    using (true);
