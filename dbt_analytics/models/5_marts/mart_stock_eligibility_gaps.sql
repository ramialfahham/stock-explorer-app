with card_metrics as (
    select * from {{ ref('int_stock__card_metrics') }}
),

final as (
    select
        market_code,
        ticker,
        snapshot_date,
        company_name,
        sector,
        missing_metrics,
        is_card_eligible
    from card_metrics
    where not is_card_eligible
)

select * from final
