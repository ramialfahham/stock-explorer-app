with metrics as (
    select * from {{ ref('int_stock__card_metrics') }}
),

benchmarks as (
    select * from {{ ref('int_stock__sector_benchmarks') }}
),

final as (
    select
        m.market_code,
        m.ticker,
        m.company_name,
        m.sector,
        m.currency,
        m.business_summary,
        m.forward_pe,
        m.ebit_margin_pct,
        m.revenue_growth_yoy_pct,
        m.net_debt_to_ebitda,
        m.fcf_margin_pct,
        m.is_card_eligible,
        b.sector_peer_count,
        b.sector_median_forward_pe,
        b.sector_median_ebit_margin_pct,
        b.sector_median_revenue_growth_yoy_pct,
        b.sector_median_net_debt_to_ebitda,
        b.sector_median_fcf_margin_pct,
        m.snapshot_date
    from metrics as m
    left join benchmarks as b
        on m.market_code = b.market_code
        and m.sector = b.sector
)

select * from final
