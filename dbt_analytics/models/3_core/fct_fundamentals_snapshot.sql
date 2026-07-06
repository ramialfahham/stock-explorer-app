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
    info_return_on_equity,
    info_current_ratio,
    info_price_to_book,
    info_price_to_sales,
    info_ev_to_ebitda,
    info_free_cashflow,
    info_market_cap,
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
    stmt_operating_expense,
    stmt_stockholders_equity,
    stmt_total_debt,
    stmt_current_assets,
    stmt_current_liabilities,
    stmt_cash_and_equivalents,
    stmt_tangible_book_value
from latest
