-- Raw files live under storage/raw/<market_code>/ and carry a market_code column; the union
-- macro trusts the column, so a file copied into the wrong folder lands in the wrong market.
with
constituents as (
    {{ raw_parquet_partition('yf_constituents.parquet') }}
),

fundamentals as (
    {{ raw_parquet_partition('yf_fundamentals.parquet') }}
),

daily_prices as (
    {{ raw_parquet_partition('yf_daily_prices.parquet') }}
),

all_rows as (
    select * from constituents
    union all
    select * from fundamentals
    union all
    select * from daily_prices
),

mismatched as (
    select
        folder_market_code,
        market_code,
        filename,
        count(*) as row_count
    from all_rows
    where market_code is distinct from folder_market_code
    group by folder_market_code, market_code, filename
)

select * from mismatched
