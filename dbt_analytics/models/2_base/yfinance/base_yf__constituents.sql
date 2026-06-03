with staged as (
    select * from {{ ref('stg_yf__constituents') }}
),

deduped as (
    select *
    from staged
    qualify row_number() over (
        partition by market_code, ticker
        order by ingested_at desc nulls last
    ) = 1
)

select * from deduped
