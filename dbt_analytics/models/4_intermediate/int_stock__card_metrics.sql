with snapshot as (
    select * from {{ ref('fct_fundamentals_snapshot') }}
),

stocks as (
    select * from {{ ref('dim_stock') }}
),

resolved as (
    select
        s.*,
        coalesce(
            s.qtr_operating_income_0,
            case
                when s.qtr_operating_revenue_0 is not null
                    and s.qtr_operating_expense_0 is not null
                    then s.qtr_operating_revenue_0 - s.qtr_operating_expense_0
            end
        ) as eff_qtr_op_0,
        coalesce(
            s.qtr_operating_income_1,
            case
                when s.qtr_operating_revenue_1 is not null
                    and s.qtr_operating_expense_1 is not null
                    then s.qtr_operating_revenue_1 - s.qtr_operating_expense_1
            end
        ) as eff_qtr_op_1,
        coalesce(
            s.qtr_operating_income_2,
            case
                when s.qtr_operating_revenue_2 is not null
                    and s.qtr_operating_expense_2 is not null
                    then s.qtr_operating_revenue_2 - s.qtr_operating_expense_2
            end
        ) as eff_qtr_op_2,
        coalesce(
            s.qtr_operating_income_3,
            case
                when s.qtr_operating_revenue_3 is not null
                    and s.qtr_operating_expense_3 is not null
                    then s.qtr_operating_revenue_3 - s.qtr_operating_expense_3
            end
        ) as eff_qtr_op_3,
        coalesce(
            s.stmt_operating_income,
            case
                when s.stmt_operating_revenue is not null
                    and s.stmt_operating_expense is not null
                    then s.stmt_operating_revenue - s.stmt_operating_expense
            end
        ) as eff_stmt_op
    from snapshot as s
),

metrics as (
    select
        s.market_code,
        s.ticker,
        s.snapshot_date,
        st.company_name,
        coalesce(s.info_sector, st.sector) as sector,
        coalesce(s.info_currency, st.currency) as currency,
        s.info_business_summary as business_summary,
        s.info_founded_year as company_founded_year,
        s.info_forward_pe as forward_pe,
        case
            when s.eff_qtr_op_0 is not null
                and s.eff_qtr_op_1 is not null
                and s.eff_qtr_op_2 is not null
                and s.eff_qtr_op_3 is not null
                and s.qtr_total_revenue_0 is not null
                and s.qtr_total_revenue_1 is not null
                and s.qtr_total_revenue_2 is not null
                and s.qtr_total_revenue_3 is not null
                and (
                    s.qtr_total_revenue_0
                    + s.qtr_total_revenue_1
                    + s.qtr_total_revenue_2
                    + s.qtr_total_revenue_3
                ) != 0
                then (
                    s.eff_qtr_op_0
                    + s.eff_qtr_op_1
                    + s.eff_qtr_op_2
                    + s.eff_qtr_op_3
                ) / (
                    s.qtr_total_revenue_0
                    + s.qtr_total_revenue_1
                    + s.qtr_total_revenue_2
                    + s.qtr_total_revenue_3
                ) * 100.0
            when s.eff_stmt_op is not null
                and s.stmt_total_revenue is not null
                and s.stmt_total_revenue != 0
                then s.eff_stmt_op / s.stmt_total_revenue * 100.0
        end as ebit_margin_pct,
        case
            when s.eff_qtr_op_0 is not null
                and s.eff_qtr_op_1 is not null
                and s.eff_qtr_op_2 is not null
                and s.eff_qtr_op_3 is not null
                and s.qtr_total_revenue_0 is not null
                and s.qtr_total_revenue_1 is not null
                and s.qtr_total_revenue_2 is not null
                and s.qtr_total_revenue_3 is not null
                and (
                    s.qtr_total_revenue_0
                    + s.qtr_total_revenue_1
                    + s.qtr_total_revenue_2
                    + s.qtr_total_revenue_3
                ) != 0
                then 'ttm_quarterly'
            when s.eff_stmt_op is not null
                and s.stmt_total_revenue is not null
                and s.stmt_total_revenue != 0
                then 'annual_latest'
        end as ebit_margin_basis,
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
        end as fcf_margin_pct,
        s.info_return_on_equity * 100.0 as roe_pct
    from resolved as s
    left join stocks as st
        on s.market_code = st.market_code
        and s.ticker = st.ticker
),

eligibility as (
    select
        *,
        list_filter(
            list_value(
                if(forward_pe is null, 'forward_pe', null),
                if(ebit_margin_pct is null, 'ebit_margin_pct', null),
                if(revenue_growth_yoy_pct is null, 'revenue_growth_yoy_pct', null),
                if(net_debt_to_ebitda is null, 'net_debt_to_ebitda', null),
                if(fcf_margin_pct is null, 'fcf_margin_pct', null)
            ),
            metric -> metric is not null
        ) as missing_metrics,
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
