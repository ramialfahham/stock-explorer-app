-- Export contract: an eligible card has every required metric for its company_type populated.
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
