{% set peer_threshold = 8 %}

with eligible as (
    -- Benchmark peers are the types that carry the benchmarkable (operating) metrics. Pre-revenue
    -- companies (survival metrics, none benchmarkable) are excluded so they cannot inflate a sector's
    -- peer count or the >= 8 median gate for operating cards that share their sector (e.g. Healthcare).
    -- operating and financial are sector-disjoint, so each sector's peer set stays single-type.
    select *
    from {{ ref('int_stock__card_metrics') }}
    where is_card_eligible
        and sector is not null
        and company_type != 'pre_revenue'
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
        min(forward_pe) as sector_min_forward_pe,
        max(forward_pe) as sector_max_forward_pe,
        median(ebit_margin_pct) as sector_median_ebit_margin_pct,
        min(ebit_margin_pct) as sector_min_ebit_margin_pct,
        max(ebit_margin_pct) as sector_max_ebit_margin_pct,
        median(revenue_growth_yoy_pct) as sector_median_revenue_growth_yoy_pct,
        min(revenue_growth_yoy_pct) as sector_min_revenue_growth_yoy_pct,
        max(revenue_growth_yoy_pct) as sector_max_revenue_growth_yoy_pct,
        median(net_debt_to_ebitda) as sector_median_net_debt_to_ebitda,
        min(net_debt_to_ebitda) as sector_min_net_debt_to_ebitda,
        max(net_debt_to_ebitda) as sector_max_net_debt_to_ebitda,
        median(fcf_margin_pct) as sector_median_fcf_margin_pct,
        min(fcf_margin_pct) as sector_min_fcf_margin_pct,
        max(fcf_margin_pct) as sector_max_fcf_margin_pct
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
            when c.sector_peer_count >= {{ peer_threshold }} then m.sector_min_forward_pe
        end as sector_min_forward_pe,
        case
            when c.sector_peer_count >= {{ peer_threshold }} then m.sector_max_forward_pe
        end as sector_max_forward_pe,
        case
            when c.sector_peer_count >= {{ peer_threshold }} then m.sector_median_ebit_margin_pct
        end as sector_median_ebit_margin_pct,
        case
            when c.sector_peer_count >= {{ peer_threshold }} then m.sector_min_ebit_margin_pct
        end as sector_min_ebit_margin_pct,
        case
            when c.sector_peer_count >= {{ peer_threshold }} then m.sector_max_ebit_margin_pct
        end as sector_max_ebit_margin_pct,
        case
            when c.sector_peer_count >= {{ peer_threshold }} then m.sector_median_revenue_growth_yoy_pct
        end as sector_median_revenue_growth_yoy_pct,
        case
            when c.sector_peer_count >= {{ peer_threshold }} then m.sector_min_revenue_growth_yoy_pct
        end as sector_min_revenue_growth_yoy_pct,
        case
            when c.sector_peer_count >= {{ peer_threshold }} then m.sector_max_revenue_growth_yoy_pct
        end as sector_max_revenue_growth_yoy_pct,
        case
            when c.sector_peer_count >= {{ peer_threshold }} then m.sector_median_net_debt_to_ebitda
        end as sector_median_net_debt_to_ebitda,
        case
            when c.sector_peer_count >= {{ peer_threshold }} then m.sector_min_net_debt_to_ebitda
        end as sector_min_net_debt_to_ebitda,
        case
            when c.sector_peer_count >= {{ peer_threshold }} then m.sector_max_net_debt_to_ebitda
        end as sector_max_net_debt_to_ebitda,
        case
            when c.sector_peer_count >= {{ peer_threshold }} then m.sector_median_fcf_margin_pct
        end as sector_median_fcf_margin_pct,
        case
            when c.sector_peer_count >= {{ peer_threshold }} then m.sector_min_fcf_margin_pct
        end as sector_min_fcf_margin_pct,
        case
            when c.sector_peer_count >= {{ peer_threshold }} then m.sector_max_fcf_margin_pct
        end as sector_max_fcf_margin_pct
    from sector_counts as c
    inner join sector_medians as m
        on c.market_code = m.market_code
        and c.sector = m.sector
)

select * from combined
