-- Sector Q1/Q3 alongside the existing sector min/median/max (outlier-aware range-mark display
-- clamp, Gemini feedback point 5). Only the 4 metrics with a card range mark today get these --
-- forward_pe already carries dead, unused min/median/max columns since it left the catalogue,
-- and gets no quartile columns.
-- All nullable + additive: pre-migration rows read null until the next full re-export.
-- Same peer_threshold >= 8 gating as sector_median_* -- see docs/data_contract.md.

alter table public.mart_stock_cards
    add column if not exists sector_q1_ebit_margin_pct numeric,
    add column if not exists sector_q3_ebit_margin_pct numeric,
    add column if not exists sector_q1_revenue_growth_yoy_pct numeric,
    add column if not exists sector_q3_revenue_growth_yoy_pct numeric,
    add column if not exists sector_q1_net_debt_to_ebitda numeric,
    add column if not exists sector_q3_net_debt_to_ebitda numeric,
    add column if not exists sector_q1_fcf_margin_pct numeric,
    add column if not exists sector_q3_fcf_margin_pct numeric;
