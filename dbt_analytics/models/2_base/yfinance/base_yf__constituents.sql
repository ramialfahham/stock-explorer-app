with staged as (
    select * from {{ ref('stg_yf__constituents') }}
),

-- Name corrections are entity resolution, so they live here, not in the seeds or staging.
overrides as (
    select * from {{ ref('stg_manual__company_name_overrides') }}
),

deduped as (
    select *
    from staged
    qualify row_number() over (
        partition by market_code, ticker
        order by ingested_at desc nulls last
    ) = 1
),

corrected as (
    select
        deduped.market_code,
        deduped.ticker,
        coalesce(overrides.company_name, deduped.company_name) as company_name,
        deduped.refreshed_at,
        deduped.source,
        deduped.ingested_at
    from deduped
    left join overrides
        on deduped.market_code = overrides.market_code
        and deduped.ticker = overrides.ticker
)

select * from corrected
