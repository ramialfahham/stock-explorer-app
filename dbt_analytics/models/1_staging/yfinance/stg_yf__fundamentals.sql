with source_data as (
    {{ raw_parquet_union('yf_fundamentals.parquet') }}
),

renamed as (
    select
        cast(s.market_code as varchar) as market_code,
        cast(s.ticker as varchar) as ticker,
        cast(s.snapshot_date as date) as snapshot_date,
        cast(s.info_forward_pe as double) as info_forward_pe,
        cast(s.info_operating_margins as double) as info_operating_margins,
        cast(s.info_revenue_growth as double) as info_revenue_growth,
        cast(s.info_net_debt as double) as info_net_debt,
        cast(s.info_total_debt as double) as info_total_debt,
        cast(s.info_total_cash as double) as info_total_cash,
        cast(s.info_ebitda as double) as info_ebitda,
        cast(s.info_sector as varchar) as info_sector,
        cast(s.info_currency as varchar) as info_currency,
        cast(s.info_long_name as varchar) as info_long_name,
        cast(s.info_business_summary as varchar) as info_business_summary,
        cast(s.stmt_total_revenue as double) as stmt_total_revenue,
        cast(s.stmt_free_cash_flow as double) as stmt_free_cash_flow,
        cast(s.stmt_fiscal_period_end as date) as stmt_fiscal_period_end,
        cast(s.stmt_currency as varchar) as stmt_currency
    from source_data as s
)

select * from renamed
