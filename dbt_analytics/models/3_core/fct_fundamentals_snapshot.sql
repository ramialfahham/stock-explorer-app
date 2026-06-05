with fundamentals as (
    select * from {{ ref('base_yf__fundamentals') }}
),

latest as (
    select *
    from fundamentals
    qualify row_number() over (
        partition by market_code, ticker
        order by snapshot_date desc
    ) = 1
)

select
    market_code,
    ticker,
    snapshot_date,
    info_forward_pe,
    info_operating_margins,
    info_revenue_growth,
    info_net_debt,
    info_total_debt,
    info_total_cash,
    info_ebitda,
    info_sector,
    info_currency,
    info_long_name,
    stmt_total_revenue,
    stmt_free_cash_flow,
    stmt_fiscal_period_end,
    stmt_currency
from latest
