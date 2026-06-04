-- Every fundamentals fact ticker must exist on the stock dimension.
with
fct as (
    select * from {{ ref('fct_fundamentals_snapshot') }}
),

dim as (
    select * from {{ ref('dim_stock') }}
),

orphans as (
    select
        f.market_code,
        f.ticker
    from fct as f
    left join dim as d
        on f.market_code = d.market_code
        and f.ticker = d.ticker
    where d.ticker is null
)

select *
from orphans
