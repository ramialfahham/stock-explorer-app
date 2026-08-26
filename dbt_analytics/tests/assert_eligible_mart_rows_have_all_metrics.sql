-- Export contract: an eligible card must have its company_type's required metrics populated
-- (operating on the four-metric set; financial on the pair; pre_revenue on net_cash). forward_pe left
-- both sets on 2026-08-26 with the metric itself: a card must not be gated on something it never shows.
with
mart as (
    select * from {{ ref('mart_stock_cards') }}
),

violations as (
    select
        market_code,
        ticker
    from mart
    where is_card_eligible
        and case company_type
            when 'financial' then (
                statement_roe_pct is null
                or net_margin_pct is null
            )
            when 'pre_revenue' then (
                net_cash is null
            )
            else (
                ebit_margin_pct is null
                or revenue_growth_yoy_pct is null
                or net_debt_to_ebitda is null
                or fcf_margin_pct is null
            )
        end
)

select *
from violations
