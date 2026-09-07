with source_data as (
    {{ raw_parquet_union('yf_daily_prices.parquet') }}
),

renamed as (
    select
        cast(market_code as varchar) as market_code,
        cast(ticker as varchar) as ticker,
        cast(trading_date as date) as trading_date,
        cast(open as double) as open,
        cast(high as double) as high,
        cast(low as double) as low,
        cast(close as double) as close,
        cast(volume as double) as volume,
        cast(dividends as double) as dividends,
        cast(stock_splits as double) as stock_splits,
        cast(ingested_at as varchar) as ingested_at
    from source_data
)

select * from renamed
