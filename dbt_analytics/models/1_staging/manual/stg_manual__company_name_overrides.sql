with source_data as (
    select * from {{ ref('company_name_overrides') }}
),

renamed as (
    select
        cast(market_code as varchar) as market_code,
        cast(ticker as varchar) as ticker,
        cast(company_name as varchar) as company_name,
        cast(reason as varchar) as reason
    from source_data
)

select * from renamed
