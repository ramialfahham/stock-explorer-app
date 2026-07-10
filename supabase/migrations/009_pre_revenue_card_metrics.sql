-- Sector/Lifecycle Router (Slice 4c) pre-revenue / survival card metric values.
-- All nullable + additive: pre-migration rows read null until the next full re-export.
-- Rendered on the pre-revenue card (net cash vs value, working capital, cash runway, monthly burn).

alter table public.mart_stock_cards
    add column if not exists net_cash_to_market_cap numeric,
    add column if not exists working_capital numeric,
    add column if not exists cash_runway_months numeric,
    add column if not exists burn_rate_monthly numeric;
