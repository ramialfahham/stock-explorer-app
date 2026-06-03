with staged as (
    select * from {{ ref('stg_yf__fundamentals') }}
),

deduped as (
    select *
    from staged
    qualify row_number() over (
        partition by market_code, ticker, snapshot_date
        order by snapshot_date desc
    ) = 1
)

select * from deduped
