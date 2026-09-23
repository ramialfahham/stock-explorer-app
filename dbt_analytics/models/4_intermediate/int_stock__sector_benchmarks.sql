{% set peer_threshold = 8 %}

with eligible as (
    -- Pre-revenue companies have no benchmarkable metrics, so they must not inflate a sector's
    -- peer count; financial and operating never share a sector, so each peer set is one type.
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
    -- Aggregates skip nulls, so combined gates each metric on its own non-null count
    -- (n_<metric>) rather than sector_peer_count.
    select
        market_code,
        sector,
        median(forward_pe) as sector_median_forward_pe,
        min(forward_pe) as sector_min_forward_pe,
        max(forward_pe) as sector_max_forward_pe,
        count(forward_pe) as n_forward_pe,
        median(ebit_margin_pct) as sector_median_ebit_margin_pct,
        min(ebit_margin_pct) as sector_min_ebit_margin_pct,
        max(ebit_margin_pct) as sector_max_ebit_margin_pct,
        -- Quartiles feed the outlier-aware clamp on the card's range mark.
        quantile_cont(ebit_margin_pct, 0.25) as sector_q1_ebit_margin_pct,
        quantile_cont(ebit_margin_pct, 0.75) as sector_q3_ebit_margin_pct,
        count(ebit_margin_pct) as n_ebit_margin_pct,
        median(revenue_growth_yoy_pct) as sector_median_revenue_growth_yoy_pct,
        min(revenue_growth_yoy_pct) as sector_min_revenue_growth_yoy_pct,
        max(revenue_growth_yoy_pct) as sector_max_revenue_growth_yoy_pct,
        quantile_cont(revenue_growth_yoy_pct, 0.25) as sector_q1_revenue_growth_yoy_pct,
        quantile_cont(revenue_growth_yoy_pct, 0.75) as sector_q3_revenue_growth_yoy_pct,
        count(revenue_growth_yoy_pct) as n_revenue_growth_yoy_pct,
        median(net_debt_to_ebitda) as sector_median_net_debt_to_ebitda,
        min(net_debt_to_ebitda) as sector_min_net_debt_to_ebitda,
        max(net_debt_to_ebitda) as sector_max_net_debt_to_ebitda,
        quantile_cont(net_debt_to_ebitda, 0.25) as sector_q1_net_debt_to_ebitda,
        quantile_cont(net_debt_to_ebitda, 0.75) as sector_q3_net_debt_to_ebitda,
        count(net_debt_to_ebitda) as n_net_debt_to_ebitda,
        median(fcf_margin_pct) as sector_median_fcf_margin_pct,
        min(fcf_margin_pct) as sector_min_fcf_margin_pct,
        max(fcf_margin_pct) as sector_max_fcf_margin_pct,
        quantile_cont(fcf_margin_pct, 0.25) as sector_q1_fcf_margin_pct,
        quantile_cont(fcf_margin_pct, 0.75) as sector_q3_fcf_margin_pct,
        count(fcf_margin_pct) as n_fcf_margin_pct,
        -- Negative equity flips these two ratios into ordinary-looking values that would skew the
        -- sector stats unnoticed, so those peers are left out (n_<metric> counts what remains).
        median(
            case when stmt_stockholders_equity is null or stmt_stockholders_equity > 0
                then debt_to_equity
            end
        ) as sector_median_debt_to_equity,
        min(
            case when stmt_stockholders_equity is null or stmt_stockholders_equity > 0
                then debt_to_equity
            end
        ) as sector_min_debt_to_equity,
        max(
            case when stmt_stockholders_equity is null or stmt_stockholders_equity > 0
                then debt_to_equity
            end
        ) as sector_max_debt_to_equity,
        quantile_cont(
            case when stmt_stockholders_equity is null or stmt_stockholders_equity > 0
                then debt_to_equity
            end,
            0.25
        ) as sector_q1_debt_to_equity,
        quantile_cont(
            case when stmt_stockholders_equity is null or stmt_stockholders_equity > 0
                then debt_to_equity
            end,
            0.75
        ) as sector_q3_debt_to_equity,
        count(
            case when stmt_stockholders_equity is null or stmt_stockholders_equity > 0
                then debt_to_equity
            end
        ) as n_debt_to_equity,
        median(current_ratio_stmt) as sector_median_current_ratio_stmt,
        min(current_ratio_stmt) as sector_min_current_ratio_stmt,
        max(current_ratio_stmt) as sector_max_current_ratio_stmt,
        quantile_cont(current_ratio_stmt, 0.25) as sector_q1_current_ratio_stmt,
        quantile_cont(current_ratio_stmt, 0.75) as sector_q3_current_ratio_stmt,
        count(current_ratio_stmt) as n_current_ratio_stmt,
        median(
            case when stmt_stockholders_equity is null or stmt_stockholders_equity > 0
                then statement_roe_pct
            end
        ) as sector_median_statement_roe_pct,
        min(
            case when stmt_stockholders_equity is null or stmt_stockholders_equity > 0
                then statement_roe_pct
            end
        ) as sector_min_statement_roe_pct,
        max(
            case when stmt_stockholders_equity is null or stmt_stockholders_equity > 0
                then statement_roe_pct
            end
        ) as sector_max_statement_roe_pct,
        quantile_cont(
            case when stmt_stockholders_equity is null or stmt_stockholders_equity > 0
                then statement_roe_pct
            end,
            0.25
        ) as sector_q1_statement_roe_pct,
        quantile_cont(
            case when stmt_stockholders_equity is null or stmt_stockholders_equity > 0
                then statement_roe_pct
            end,
            0.75
        ) as sector_q3_statement_roe_pct,
        count(
            case when stmt_stockholders_equity is null or stmt_stockholders_equity > 0
                then statement_roe_pct
            end
        ) as n_statement_roe_pct,
        median(net_margin_pct) as sector_median_net_margin_pct,
        min(net_margin_pct) as sector_min_net_margin_pct,
        max(net_margin_pct) as sector_max_net_margin_pct,
        quantile_cont(net_margin_pct, 0.25) as sector_q1_net_margin_pct,
        quantile_cont(net_margin_pct, 0.75) as sector_q3_net_margin_pct,
        count(net_margin_pct) as n_net_margin_pct,
        median(roa_pct) as sector_median_roa_pct,
        min(roa_pct) as sector_min_roa_pct,
        max(roa_pct) as sector_max_roa_pct,
        quantile_cont(roa_pct, 0.25) as sector_q1_roa_pct,
        quantile_cont(roa_pct, 0.75) as sector_q3_roa_pct,
        count(roa_pct) as n_roa_pct
    from eligible
    group by 1, 2
),

combined as (
    select
        c.market_code,
        c.sector,
        c.sector_peer_count,
        case
            when m.n_forward_pe >= {{ peer_threshold }} then m.sector_median_forward_pe
        end as sector_median_forward_pe,
        case
            when m.n_forward_pe >= {{ peer_threshold }} then m.sector_min_forward_pe
        end as sector_min_forward_pe,
        case
            when m.n_forward_pe >= {{ peer_threshold }} then m.sector_max_forward_pe
        end as sector_max_forward_pe,
        case
            when m.n_ebit_margin_pct >= {{ peer_threshold }} then m.sector_median_ebit_margin_pct
        end as sector_median_ebit_margin_pct,
        case
            when m.n_ebit_margin_pct >= {{ peer_threshold }} then m.sector_min_ebit_margin_pct
        end as sector_min_ebit_margin_pct,
        case
            when m.n_ebit_margin_pct >= {{ peer_threshold }} then m.sector_max_ebit_margin_pct
        end as sector_max_ebit_margin_pct,
        case
            when m.n_ebit_margin_pct >= {{ peer_threshold }} then m.sector_q1_ebit_margin_pct
        end as sector_q1_ebit_margin_pct,
        case
            when m.n_ebit_margin_pct >= {{ peer_threshold }} then m.sector_q3_ebit_margin_pct
        end as sector_q3_ebit_margin_pct,
        case
            when m.n_revenue_growth_yoy_pct >= {{ peer_threshold }} then m.sector_median_revenue_growth_yoy_pct
        end as sector_median_revenue_growth_yoy_pct,
        case
            when m.n_revenue_growth_yoy_pct >= {{ peer_threshold }} then m.sector_min_revenue_growth_yoy_pct
        end as sector_min_revenue_growth_yoy_pct,
        case
            when m.n_revenue_growth_yoy_pct >= {{ peer_threshold }} then m.sector_max_revenue_growth_yoy_pct
        end as sector_max_revenue_growth_yoy_pct,
        case
            when m.n_revenue_growth_yoy_pct >= {{ peer_threshold }} then m.sector_q1_revenue_growth_yoy_pct
        end as sector_q1_revenue_growth_yoy_pct,
        case
            when m.n_revenue_growth_yoy_pct >= {{ peer_threshold }} then m.sector_q3_revenue_growth_yoy_pct
        end as sector_q3_revenue_growth_yoy_pct,
        case
            when m.n_net_debt_to_ebitda >= {{ peer_threshold }} then m.sector_median_net_debt_to_ebitda
        end as sector_median_net_debt_to_ebitda,
        case
            when m.n_net_debt_to_ebitda >= {{ peer_threshold }} then m.sector_min_net_debt_to_ebitda
        end as sector_min_net_debt_to_ebitda,
        case
            when m.n_net_debt_to_ebitda >= {{ peer_threshold }} then m.sector_max_net_debt_to_ebitda
        end as sector_max_net_debt_to_ebitda,
        case
            when m.n_net_debt_to_ebitda >= {{ peer_threshold }} then m.sector_q1_net_debt_to_ebitda
        end as sector_q1_net_debt_to_ebitda,
        case
            when m.n_net_debt_to_ebitda >= {{ peer_threshold }} then m.sector_q3_net_debt_to_ebitda
        end as sector_q3_net_debt_to_ebitda,
        case
            when m.n_fcf_margin_pct >= {{ peer_threshold }} then m.sector_median_fcf_margin_pct
        end as sector_median_fcf_margin_pct,
        case
            when m.n_fcf_margin_pct >= {{ peer_threshold }} then m.sector_min_fcf_margin_pct
        end as sector_min_fcf_margin_pct,
        case
            when m.n_fcf_margin_pct >= {{ peer_threshold }} then m.sector_max_fcf_margin_pct
        end as sector_max_fcf_margin_pct,
        case
            when m.n_fcf_margin_pct >= {{ peer_threshold }} then m.sector_q1_fcf_margin_pct
        end as sector_q1_fcf_margin_pct,
        case
            when m.n_fcf_margin_pct >= {{ peer_threshold }} then m.sector_q3_fcf_margin_pct
        end as sector_q3_fcf_margin_pct,
        case
            when m.n_debt_to_equity >= {{ peer_threshold }} then m.sector_median_debt_to_equity
        end as sector_median_debt_to_equity,
        case
            when m.n_debt_to_equity >= {{ peer_threshold }} then m.sector_min_debt_to_equity
        end as sector_min_debt_to_equity,
        case
            when m.n_debt_to_equity >= {{ peer_threshold }} then m.sector_max_debt_to_equity
        end as sector_max_debt_to_equity,
        case
            when m.n_debt_to_equity >= {{ peer_threshold }} then m.sector_q1_debt_to_equity
        end as sector_q1_debt_to_equity,
        case
            when m.n_debt_to_equity >= {{ peer_threshold }} then m.sector_q3_debt_to_equity
        end as sector_q3_debt_to_equity,
        case
            when m.n_current_ratio_stmt >= {{ peer_threshold }} then m.sector_median_current_ratio_stmt
        end as sector_median_current_ratio_stmt,
        case
            when m.n_current_ratio_stmt >= {{ peer_threshold }} then m.sector_min_current_ratio_stmt
        end as sector_min_current_ratio_stmt,
        case
            when m.n_current_ratio_stmt >= {{ peer_threshold }} then m.sector_max_current_ratio_stmt
        end as sector_max_current_ratio_stmt,
        case
            when m.n_current_ratio_stmt >= {{ peer_threshold }} then m.sector_q1_current_ratio_stmt
        end as sector_q1_current_ratio_stmt,
        case
            when m.n_current_ratio_stmt >= {{ peer_threshold }} then m.sector_q3_current_ratio_stmt
        end as sector_q3_current_ratio_stmt,
        case
            when m.n_statement_roe_pct >= {{ peer_threshold }} then m.sector_median_statement_roe_pct
        end as sector_median_statement_roe_pct,
        case
            when m.n_statement_roe_pct >= {{ peer_threshold }} then m.sector_min_statement_roe_pct
        end as sector_min_statement_roe_pct,
        case
            when m.n_statement_roe_pct >= {{ peer_threshold }} then m.sector_max_statement_roe_pct
        end as sector_max_statement_roe_pct,
        case
            when m.n_statement_roe_pct >= {{ peer_threshold }} then m.sector_q1_statement_roe_pct
        end as sector_q1_statement_roe_pct,
        case
            when m.n_statement_roe_pct >= {{ peer_threshold }} then m.sector_q3_statement_roe_pct
        end as sector_q3_statement_roe_pct,
        case
            when m.n_net_margin_pct >= {{ peer_threshold }} then m.sector_median_net_margin_pct
        end as sector_median_net_margin_pct,
        case
            when m.n_net_margin_pct >= {{ peer_threshold }} then m.sector_min_net_margin_pct
        end as sector_min_net_margin_pct,
        case
            when m.n_net_margin_pct >= {{ peer_threshold }} then m.sector_max_net_margin_pct
        end as sector_max_net_margin_pct,
        case
            when m.n_net_margin_pct >= {{ peer_threshold }} then m.sector_q1_net_margin_pct
        end as sector_q1_net_margin_pct,
        case
            when m.n_net_margin_pct >= {{ peer_threshold }} then m.sector_q3_net_margin_pct
        end as sector_q3_net_margin_pct,
        case
            when m.n_roa_pct >= {{ peer_threshold }} then m.sector_median_roa_pct
        end as sector_median_roa_pct,
        case
            when m.n_roa_pct >= {{ peer_threshold }} then m.sector_min_roa_pct
        end as sector_min_roa_pct,
        case
            when m.n_roa_pct >= {{ peer_threshold }} then m.sector_max_roa_pct
        end as sector_max_roa_pct,
        case
            when m.n_roa_pct >= {{ peer_threshold }} then m.sector_q1_roa_pct
        end as sector_q1_roa_pct,
        case
            when m.n_roa_pct >= {{ peer_threshold }} then m.sector_q3_roa_pct
        end as sector_q3_roa_pct
    from sector_counts as c
    inner join sector_medians as m
        on c.market_code = m.market_code
        and c.sector = m.sector
)

select * from combined
