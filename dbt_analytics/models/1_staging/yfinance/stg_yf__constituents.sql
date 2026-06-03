with source_data as (
    {{ raw_parquet_union('yf_constituents.parquet') }}
),

renamed as (
    select
        cast(market_code as varchar) as market_code,
        cast(ticker as varchar) as ticker,
        cast(company_name as varchar) as company_name,
        cast(refreshed_at as varchar) as refreshed_at,
        cast(source as varchar) as source,
        cast(ingested_at as varchar) as ingested_at
    from source_data
)

select * from renamed
