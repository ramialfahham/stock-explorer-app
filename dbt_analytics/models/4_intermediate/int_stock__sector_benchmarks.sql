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
        -- Q1/Q3 (Gemini feedback point 5, docs/backlog/gemini_verdict_feedback.md): the display
        -- range clamp needs quartiles alongside min/median/max. quantile_cont is the same
        -- continuous-interpolation family median() already uses -- no new statistical convention
        -- introduced, just two more percentiles of it.
        quantile_cont(ebit_margin_pct, 0.25) as sector_q1_ebit_margin_pct,
        quantile_cont(ebit_margin_pct, 0.75) as sector_q3_ebit_margin_pct,
        median(revenue_growth_yoy_pct) as sector_median_revenue_growth_yoy_pct,
        min(revenue_growth_yoy_pct) as sector_min_revenue_growth_yoy_pct,
        max(revenue_growth_yoy_pct) as sector_max_revenue_growth_yoy_pct,
        quantile_cont(revenue_growth_yoy_pct, 0.25) as sector_q1_revenue_growth_yoy_pct,
        quantile_cont(revenue_growth_yoy_pct, 0.75) as sector_q3_revenue_growth_yoy_pct,
        median(net_debt_to_ebitda) as sector_median_net_debt_to_ebitda,
        min(net_debt_to_ebitda) as sector_min_net_debt_to_ebitda,
        max(net_debt_to_ebitda) as sector_max_net_debt_to_ebitda,
        quantile_cont(net_debt_to_ebitda, 0.25) as sector_q1_net_debt_to_ebitda,
        quantile_cont(net_debt_to_ebitda, 0.75) as sector_q3_net_debt_to_ebitda,
        median(fcf_margin_pct) as sector_median_fcf_margin_pct,
        min(fcf_margin_pct) as sector_min_fcf_margin_pct,
        max(fcf_margin_pct) as sector_max_fcf_margin_pct,
        quantile_cont(fcf_margin_pct, 0.25) as sector_q1_fcf_margin_pct,
        quantile_cont(fcf_margin_pct, 0.75) as sector_q3_fcf_margin_pct,
        -- 5-metric benchmark expansion (owner-approved follow-up to MR #22): the 2 remaining
        -- operating supporting axes plus the 3 financial-only metrics. Same 5-statistic set,
        -- same quantile_cont() convention, as every metric above. Pre-revenue's 4 metrics are
        -- deliberately excluded -- see docs/ui/card_metric_cell.md's Range mark mechanics.
        --
        -- debt_to_equity and statement_roe_pct both divide by stmt_stockholders_equity, which
        -- scripts/assessment_rules.py's _axis_unless_denominator_nonpositive guard already treats
        -- as sign-breaking when it goes negative (a genuine loss over negative equity divides out
        -- to a spuriously POSITIVE, non-extreme statement_roe_pct -- see that function's own
        -- comment block). That guard only covers the verdict color; a sign-flipped value would
        -- otherwise flow straight into these two metrics' sector median/min/max/quartiles,
        -- silently skewing the benchmark every peer in the sector is compared against, without
        -- tripping the existing outlier clamp (the value looks ordinary, not extreme). A MISSING
        -- stmt_stockholders_equity does not trigger the filter -- same "only a denominator we can
        -- actually see is bad" rule _axis_unless_denominator_nonpositive already uses, and in
        -- practice debt_to_equity/statement_roe_pct are never non-null when their own denominator
        -- is (int_stock__card_metrics.sql computes both from the same non-null check). The other 3
        -- new metrics' denominators (current liabilities, revenue, total assets) can't go negative
        -- in this data, so they need no equivalent filter.
        --
        -- Known, accepted limitation: this filter can drop the effective count feeding these two
        -- metrics' statistics below sector_peer_count in a sector with multiple negative-equity
        -- peers, while the column still renders (the >= peer_threshold gate below checks the
        -- unfiltered peer count, same as every other metric). Same tolerance this model already
        -- has for any metric that's null for some fraction of a sector's peers -- not a new
        -- fragility class, just this filter's own instance of it.
        median(case when stmt_stockholders_equity is null or stmt_stockholders_equity > 0 then debt_to_equity end) as sector_median_debt_to_equity,
        min(case when stmt_stockholders_equity is null or stmt_stockholders_equity > 0 then debt_to_equity end) as sector_min_debt_to_equity,
        max(case when stmt_stockholders_equity is null or stmt_stockholders_equity > 0 then debt_to_equity end) as sector_max_debt_to_equity,
        quantile_cont(case when stmt_stockholders_equity is null or stmt_stockholders_equity > 0 then debt_to_equity end, 0.25) as sector_q1_debt_to_equity,
        quantile_cont(case when stmt_stockholders_equity is null or stmt_stockholders_equity > 0 then debt_to_equity end, 0.75) as sector_q3_debt_to_equity,
        median(current_ratio_stmt) as sector_median_current_ratio_stmt,
        min(current_ratio_stmt) as sector_min_current_ratio_stmt,
        max(current_ratio_stmt) as sector_max_current_ratio_stmt,
        quantile_cont(current_ratio_stmt, 0.25) as sector_q1_current_ratio_stmt,
        quantile_cont(current_ratio_stmt, 0.75) as sector_q3_current_ratio_stmt,
        median(case when stmt_stockholders_equity is null or stmt_stockholders_equity > 0 then statement_roe_pct end) as sector_median_statement_roe_pct,
        min(case when stmt_stockholders_equity is null or stmt_stockholders_equity > 0 then statement_roe_pct end) as sector_min_statement_roe_pct,
        max(case when stmt_stockholders_equity is null or stmt_stockholders_equity > 0 then statement_roe_pct end) as sector_max_statement_roe_pct,
        quantile_cont(case when stmt_stockholders_equity is null or stmt_stockholders_equity > 0 then statement_roe_pct end, 0.25) as sector_q1_statement_roe_pct,
        quantile_cont(case when stmt_stockholders_equity is null or stmt_stockholders_equity > 0 then statement_roe_pct end, 0.75) as sector_q3_statement_roe_pct,
        median(net_margin_pct) as sector_median_net_margin_pct,
        min(net_margin_pct) as sector_min_net_margin_pct,
        max(net_margin_pct) as sector_max_net_margin_pct,
        quantile_cont(net_margin_pct, 0.25) as sector_q1_net_margin_pct,
        quantile_cont(net_margin_pct, 0.75) as sector_q3_net_margin_pct,
        median(roa_pct) as sector_median_roa_pct,
        min(roa_pct) as sector_min_roa_pct,
        max(roa_pct) as sector_max_roa_pct,
        quantile_cont(roa_pct, 0.25) as sector_q1_roa_pct,
        quantile_cont(roa_pct, 0.75) as sector_q3_roa_pct
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
            when c.sector_peer_count >= {{ peer_threshold }} then m.sector_q1_ebit_margin_pct
        end as sector_q1_ebit_margin_pct,
        case
            when c.sector_peer_count >= {{ peer_threshold }} then m.sector_q3_ebit_margin_pct
        end as sector_q3_ebit_margin_pct,
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
            when c.sector_peer_count >= {{ peer_threshold }} then m.sector_q1_revenue_growth_yoy_pct
        end as sector_q1_revenue_growth_yoy_pct,
        case
            when c.sector_peer_count >= {{ peer_threshold }} then m.sector_q3_revenue_growth_yoy_pct
        end as sector_q3_revenue_growth_yoy_pct,
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
            when c.sector_peer_count >= {{ peer_threshold }} then m.sector_q1_net_debt_to_ebitda
        end as sector_q1_net_debt_to_ebitda,
        case
            when c.sector_peer_count >= {{ peer_threshold }} then m.sector_q3_net_debt_to_ebitda
        end as sector_q3_net_debt_to_ebitda,
        case
            when c.sector_peer_count >= {{ peer_threshold }} then m.sector_median_fcf_margin_pct
        end as sector_median_fcf_margin_pct,
        case
            when c.sector_peer_count >= {{ peer_threshold }} then m.sector_min_fcf_margin_pct
        end as sector_min_fcf_margin_pct,
        case
            when c.sector_peer_count >= {{ peer_threshold }} then m.sector_max_fcf_margin_pct
        end as sector_max_fcf_margin_pct,
        case
            when c.sector_peer_count >= {{ peer_threshold }} then m.sector_q1_fcf_margin_pct
        end as sector_q1_fcf_margin_pct,
        case
            when c.sector_peer_count >= {{ peer_threshold }} then m.sector_q3_fcf_margin_pct
        end as sector_q3_fcf_margin_pct,
        case
            when c.sector_peer_count >= {{ peer_threshold }} then m.sector_median_debt_to_equity
        end as sector_median_debt_to_equity,
        case
            when c.sector_peer_count >= {{ peer_threshold }} then m.sector_min_debt_to_equity
        end as sector_min_debt_to_equity,
        case
            when c.sector_peer_count >= {{ peer_threshold }} then m.sector_max_debt_to_equity
        end as sector_max_debt_to_equity,
        case
            when c.sector_peer_count >= {{ peer_threshold }} then m.sector_q1_debt_to_equity
        end as sector_q1_debt_to_equity,
        case
            when c.sector_peer_count >= {{ peer_threshold }} then m.sector_q3_debt_to_equity
        end as sector_q3_debt_to_equity,
        case
            when c.sector_peer_count >= {{ peer_threshold }} then m.sector_median_current_ratio_stmt
        end as sector_median_current_ratio_stmt,
        case
            when c.sector_peer_count >= {{ peer_threshold }} then m.sector_min_current_ratio_stmt
        end as sector_min_current_ratio_stmt,
        case
            when c.sector_peer_count >= {{ peer_threshold }} then m.sector_max_current_ratio_stmt
        end as sector_max_current_ratio_stmt,
        case
            when c.sector_peer_count >= {{ peer_threshold }} then m.sector_q1_current_ratio_stmt
        end as sector_q1_current_ratio_stmt,
        case
            when c.sector_peer_count >= {{ peer_threshold }} then m.sector_q3_current_ratio_stmt
        end as sector_q3_current_ratio_stmt,
        case
            when c.sector_peer_count >= {{ peer_threshold }} then m.sector_median_statement_roe_pct
        end as sector_median_statement_roe_pct,
        case
            when c.sector_peer_count >= {{ peer_threshold }} then m.sector_min_statement_roe_pct
        end as sector_min_statement_roe_pct,
        case
            when c.sector_peer_count >= {{ peer_threshold }} then m.sector_max_statement_roe_pct
        end as sector_max_statement_roe_pct,
        case
            when c.sector_peer_count >= {{ peer_threshold }} then m.sector_q1_statement_roe_pct
        end as sector_q1_statement_roe_pct,
        case
            when c.sector_peer_count >= {{ peer_threshold }} then m.sector_q3_statement_roe_pct
        end as sector_q3_statement_roe_pct,
        case
            when c.sector_peer_count >= {{ peer_threshold }} then m.sector_median_net_margin_pct
        end as sector_median_net_margin_pct,
        case
            when c.sector_peer_count >= {{ peer_threshold }} then m.sector_min_net_margin_pct
        end as sector_min_net_margin_pct,
        case
            when c.sector_peer_count >= {{ peer_threshold }} then m.sector_max_net_margin_pct
        end as sector_max_net_margin_pct,
        case
            when c.sector_peer_count >= {{ peer_threshold }} then m.sector_q1_net_margin_pct
        end as sector_q1_net_margin_pct,
        case
            when c.sector_peer_count >= {{ peer_threshold }} then m.sector_q3_net_margin_pct
        end as sector_q3_net_margin_pct,
        case
            when c.sector_peer_count >= {{ peer_threshold }} then m.sector_median_roa_pct
        end as sector_median_roa_pct,
        case
            when c.sector_peer_count >= {{ peer_threshold }} then m.sector_min_roa_pct
        end as sector_min_roa_pct,
        case
            when c.sector_peer_count >= {{ peer_threshold }} then m.sector_max_roa_pct
        end as sector_max_roa_pct,
        case
            when c.sector_peer_count >= {{ peer_threshold }} then m.sector_q1_roa_pct
        end as sector_q1_roa_pct,
        case
            when c.sector_peer_count >= {{ peer_threshold }} then m.sector_q3_roa_pct
        end as sector_q3_roa_pct
    from sector_counts as c
    inner join sector_medians as m
        on c.market_code = m.market_code
        and c.sector = m.sector
)

select * from combined
