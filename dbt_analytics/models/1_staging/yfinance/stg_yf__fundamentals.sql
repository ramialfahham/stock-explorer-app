with source_data as (
    {{ raw_parquet_union('yf_fundamentals.parquet') }}
),

renamed as (
    select
        cast(market_code as varchar) as market_code,
        cast(ticker as varchar) as ticker,
        cast(snapshot_date as date) as snapshot_date,
        cast(info_forward_pe as double) as info_forward_pe,
        cast(info_operating_margins as double) as info_operating_margins,
        cast(info_revenue_growth as double) as info_revenue_growth,
        cast(info_net_debt as double) as info_net_debt,
        cast(info_ebitda as double) as info_ebitda,
        cast(info_sector as varchar) as info_sector,
        cast(info_currency as varchar) as info_currency,
        cast(info_long_name as varchar) as info_long_name,
        cast(stmt_total_revenue as double) as stmt_total_revenue,
        cast(stmt_free_cash_flow as double) as stmt_free_cash_flow,
        cast(stmt_fiscal_period_end as date) as stmt_fiscal_period_end,
        cast(stmt_currency as varchar) as stmt_currency
    from source_data
)

select * from renamed
