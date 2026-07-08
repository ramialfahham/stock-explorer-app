-- Sector/Lifecycle Router (Slice 4b) financial-card metric values.
-- All nullable + additive: pre-migration rows read null until the next full re-export.
-- Rendered on the bank card per company_type (P/TBV + P/E, net margin, ROE, ROA, dividend yield).

alter table public.mart_stock_cards
    add column if not exists price_to_tangible_book numeric,
    add column if not exists net_margin_pct numeric,
    add column if not exists roa_pct numeric,
    add column if not exists dividend_yield_pct numeric;
