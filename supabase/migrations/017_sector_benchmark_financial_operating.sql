-- Sector median/min/max/Q1/Q3 for 5 more metrics (owner-approved follow-up to MR #22):
-- debt_to_equity, current_ratio_stmt (operating supporting axes) and statement_roe_pct,
-- net_margin_pct, roa_pct (financial-only). Same 5-statistic set and peer_threshold >= 8
-- gating as every existing sector_median_* column -- see docs/data_contract.md.
-- Pre-revenue's 4 metrics are deliberately excluded: only 3 pre-revenue companies exist
-- app-wide, which can never clear the 8-peer rendering threshold.
-- All nullable + additive: pre-migration rows read null until the next full re-export.

alter table public.mart_stock_cards
    add column if not exists sector_median_debt_to_equity numeric,
    add column if not exists sector_min_debt_to_equity numeric,
    add column if not exists sector_max_debt_to_equity numeric,
    add column if not exists sector_q1_debt_to_equity numeric,
    add column if not exists sector_q3_debt_to_equity numeric,
    add column if not exists sector_median_current_ratio_stmt numeric,
    add column if not exists sector_min_current_ratio_stmt numeric,
    add column if not exists sector_max_current_ratio_stmt numeric,
    add column if not exists sector_q1_current_ratio_stmt numeric,
    add column if not exists sector_q3_current_ratio_stmt numeric,
    add column if not exists sector_median_statement_roe_pct numeric,
    add column if not exists sector_min_statement_roe_pct numeric,
    add column if not exists sector_max_statement_roe_pct numeric,
    add column if not exists sector_q1_statement_roe_pct numeric,
    add column if not exists sector_q3_statement_roe_pct numeric,
    add column if not exists sector_median_net_margin_pct numeric,
    add column if not exists sector_min_net_margin_pct numeric,
    add column if not exists sector_max_net_margin_pct numeric,
    add column if not exists sector_q1_net_margin_pct numeric,
    add column if not exists sector_q3_net_margin_pct numeric,
    add column if not exists sector_median_roa_pct numeric,
    add column if not exists sector_min_roa_pct numeric,
    add column if not exists sector_max_roa_pct numeric,
    add column if not exists sector_q1_roa_pct numeric,
    add column if not exists sector_q3_roa_pct numeric;
