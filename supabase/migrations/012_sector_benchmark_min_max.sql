-- Sector min/max alongside the existing sector median (card-face range mark).
-- All nullable + additive: pre-migration rows read null until the next full re-export.
-- Same peer_threshold >= 8 gating as sector_median_* -- see docs/data_contract.md.

alter table public.mart_stock_cards
    add column if not exists sector_min_forward_pe numeric,
    add column if not exists sector_max_forward_pe numeric,
    add column if not exists sector_min_ebit_margin_pct numeric,
    add column if not exists sector_max_ebit_margin_pct numeric,
    add column if not exists sector_min_revenue_growth_yoy_pct numeric,
    add column if not exists sector_max_revenue_growth_yoy_pct numeric,
    add column if not exists sector_min_net_debt_to_ebitda numeric,
    add column if not exists sector_max_net_debt_to_ebitda numeric,
    add column if not exists sector_min_fcf_margin_pct numeric,
    add column if not exists sector_max_fcf_margin_pct numeric;
