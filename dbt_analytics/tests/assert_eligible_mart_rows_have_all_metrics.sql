-- Export contract: eligible cards must have all five metrics populated.
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
        and (
            forward_pe is null
            or ebit_margin_pct is null
            or revenue_growth_yoy_pct is null
            or net_debt_to_ebitda is null
            or fcf_margin_pct is null
        )
)

select *
from violations
