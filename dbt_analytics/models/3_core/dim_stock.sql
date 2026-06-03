with constituents as (
    select * from {{ ref('base_yf__constituents') }}
),

fundamentals as (
    select
        market_code,
        ticker,
        info_long_name,
        info_sector,
        info_currency
    from {{ ref('base_yf__fundamentals') }}
    qualify row_number() over (
        partition by market_code, ticker
        order by snapshot_date desc
    ) = 1
),

joined as (
    select
        c.market_code,
        c.ticker,
        coalesce(c.company_name, f.info_long_name) as company_name,
        f.info_sector as sector,
        f.info_currency as currency
    from constituents as c
    left join fundamentals as f
        on c.market_code = f.market_code
        and c.ticker = f.ticker
)

select * from joined
