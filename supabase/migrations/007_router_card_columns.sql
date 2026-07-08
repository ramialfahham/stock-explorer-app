-- Sector/Lifecycle Router (Slice 4a) card columns.
-- All nullable + additive: pre-migration rows read null until the next full re-export.
--   * company_type — operating | financial | pre_revenue (frontend treats a missing value as operating)
--   * debt_to_equity / current_ratio_stmt / statement_roe_pct — the operating card's new
--     solvency / liquidity / returns metrics (rendered per company_type; not in is_card_eligible).

alter table public.mart_stock_cards
    add column if not exists company_type text,
    add column if not exists debt_to_equity numeric,
    add column if not exists current_ratio_stmt numeric,
    add column if not exists statement_roe_pct numeric;
