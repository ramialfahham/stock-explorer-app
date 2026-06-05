with snapshot as (
    select * from {{ ref('fct_fundamentals_snapshot') }}
),

stocks as (
    select * from {{ ref('dim_stock') }}
),

metrics as (
    select
        s.market_code,
        s.ticker,
        s.snapshot_date,
        st.company_name,
        coalesce(s.info_sector, st.sector) as sector,
        coalesce(s.info_currency, st.currency) as currency,
        s.info_forward_pe as forward_pe,
        s.info_operating_margins * 100.0 as ebit_margin_pct,
        s.info_revenue_growth * 100.0 as revenue_growth_yoy_pct,
        case
            when coalesce(s.info_net_debt, s.info_total_debt - s.info_total_cash) is not null
                and s.info_ebitda is not null
                and s.info_ebitda != 0
                then coalesce(s.info_net_debt, s.info_total_debt - s.info_total_cash)
                    / s.info_ebitda
        end as net_debt_to_ebitda,
        case
            when s.stmt_free_cash_flow is not null
                and s.stmt_total_revenue is not null
                and s.stmt_total_revenue != 0
                then s.stmt_free_cash_flow / s.stmt_total_revenue * 100.0
        end as fcf_margin_pct
    from snapshot as s
    left join stocks as st
        on s.market_code = st.market_code
        and s.ticker = st.ticker
),

eligibility as (
    select
        *,
        (
            forward_pe is not null
            and ebit_margin_pct is not null
            and revenue_growth_yoy_pct is not null
            and net_debt_to_ebitda is not null
            and fcf_margin_pct is not null
        ) as is_card_eligible
    from metrics
)

select * from eligibility
