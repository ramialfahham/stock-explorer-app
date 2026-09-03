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
        m.company_founded_year,
        m.forward_pe,
        m.ebit_margin_pct,
        m.ebit_margin_basis,
        m.revenue_growth_yoy_pct,
        m.info_ebitda,
        m.net_debt_to_ebitda,
        m.stmt_free_cash_flow,
        m.fcf_margin_pct,
        m.stmt_stockholders_equity,
        m.debt_to_equity,
        m.current_ratio_stmt,
        m.statement_roe_pct,
        m.price_to_tangible_book,
        m.net_margin_pct,
        m.roa_pct,
        m.dividend_yield_pct,
        m.net_cash_to_market_cap,
        m.net_cash,
        m.working_capital,
        m.cash_runway_months,
        m.burn_rate_monthly,
        m.is_card_eligible,
        m.company_type,
        b.sector_peer_count,
        b.sector_median_forward_pe,
        b.sector_min_forward_pe,
        b.sector_max_forward_pe,
        b.sector_median_ebit_margin_pct,
        b.sector_min_ebit_margin_pct,
        b.sector_max_ebit_margin_pct,
        b.sector_q1_ebit_margin_pct,
        b.sector_q3_ebit_margin_pct,
        b.sector_median_revenue_growth_yoy_pct,
        b.sector_min_revenue_growth_yoy_pct,
        b.sector_max_revenue_growth_yoy_pct,
        b.sector_q1_revenue_growth_yoy_pct,
        b.sector_q3_revenue_growth_yoy_pct,
        b.sector_median_net_debt_to_ebitda,
        b.sector_min_net_debt_to_ebitda,
        b.sector_max_net_debt_to_ebitda,
        b.sector_q1_net_debt_to_ebitda,
        b.sector_q3_net_debt_to_ebitda,
        b.sector_median_fcf_margin_pct,
        b.sector_min_fcf_margin_pct,
        b.sector_max_fcf_margin_pct,
        b.sector_q1_fcf_margin_pct,
        b.sector_q3_fcf_margin_pct,
        m.snapshot_date
    from metrics as m
    left join benchmarks as b
        on m.market_code = b.market_code
        and m.sector = b.sector
        -- pre_revenue is excluded from the sector peer set (int_stock__sector_benchmarks), so it must
        -- not inherit that sector's peer_count/medians here — otherwise a pre-revenue card would show a
        -- "(N companies)" headline for a peer group it is not counted in. None of pre_revenue's rendered
        -- metrics are benchmarkable, so leaving the benchmark columns null loses no comparison signal.
        and m.company_type != 'pre_revenue'
    where m.is_card_eligible
)

select * from final
