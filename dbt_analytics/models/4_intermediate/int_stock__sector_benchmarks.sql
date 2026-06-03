{% set peer_threshold = 8 %}

with eligible as (
    select *
    from {{ ref('int_stock__card_metrics') }}
    where is_card_eligible
        and sector is not null
),

sector_counts as (
    select
        market_code,
        sector,
        count(*) as sector_peer_count
    from eligible
    group by 1, 2
),

sector_medians as (
    select
        market_code,
        sector,
        median(forward_pe) as sector_median_forward_pe,
        median(ebit_margin_pct) as sector_median_ebit_margin_pct,
        median(revenue_growth_yoy_pct) as sector_median_revenue_growth_yoy_pct,
        median(net_debt_to_ebitda) as sector_median_net_debt_to_ebitda,
        median(fcf_margin_pct) as sector_median_fcf_margin_pct
    from eligible
    group by 1, 2
),

combined as (
    select
        c.market_code,
        c.sector,
        c.sector_peer_count,
        case
            when c.sector_peer_count >= {{ peer_threshold }} then m.sector_median_forward_pe
        end as sector_median_forward_pe,
        case
            when c.sector_peer_count >= {{ peer_threshold }} then m.sector_median_ebit_margin_pct
        end as sector_median_ebit_margin_pct,
        case
            when c.sector_peer_count >= {{ peer_threshold }} then m.sector_median_revenue_growth_yoy_pct
        end as sector_median_revenue_growth_yoy_pct,
        case
            when c.sector_peer_count >= {{ peer_threshold }} then m.sector_median_net_debt_to_ebitda
        end as sector_median_net_debt_to_ebitda,
        case
            when c.sector_peer_count >= {{ peer_threshold }} then m.sector_median_fcf_margin_pct
        end as sector_median_fcf_margin_pct
    from sector_counts as c
    inner join sector_medians as m
        on c.market_code = m.market_code
        and c.sector = m.sector
)

select * from combined
