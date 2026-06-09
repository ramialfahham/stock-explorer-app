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
    info_business_summary,
    info_founded_year,
    stmt_total_revenue,
    stmt_free_cash_flow,
    stmt_fiscal_period_end,
    stmt_currency,
    qtr_operating_income_0,
    qtr_operating_income_1,
    qtr_operating_income_2,
    qtr_operating_income_3,
    qtr_total_revenue_0,
    qtr_total_revenue_1,
    qtr_total_revenue_2,
    qtr_total_revenue_3,
    qtr_operating_revenue_0,
    qtr_operating_revenue_1,
    qtr_operating_revenue_2,
    qtr_operating_revenue_3,
    qtr_operating_expense_0,
    qtr_operating_expense_1,
    qtr_operating_expense_2,
    qtr_operating_expense_3,
    stmt_operating_income,
    stmt_operating_revenue,
    stmt_operating_expense
from latest
