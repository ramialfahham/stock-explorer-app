-- Export contract: an eligible card must have its company_type's required metrics populated
-- (operating/pre_revenue on the five-metric set; financial on the core three).
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
                forward_pe is null
                or statement_roe_pct is null
                or net_margin_pct is null
            )
            else (
                forward_pe is null
                or ebit_margin_pct is null
                or revenue_growth_yoy_pct is null
                or net_debt_to_ebitda is null
                or fcf_margin_pct is null
            )
        end
)

select *
from violations
