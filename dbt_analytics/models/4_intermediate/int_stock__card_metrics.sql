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
        ) as eff_stmt_op,
        case
            when s.stmt_operating_cash_flow is not null
                and s.stmt_capital_expenditure is not null
                then s.stmt_operating_cash_flow + s.stmt_capital_expenditure
        end as computed_fcf
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
        s.info_return_on_equity * 100.0 as roe_pct,
        s.info_current_ratio as current_ratio,
        s.info_price_to_book as price_to_book,
        s.info_price_to_sales as price_to_sales,
        s.info_ev_to_ebitda as ev_to_ebitda,
        case
            when s.info_market_cap is not null
                and s.info_market_cap != 0
                then s.info_free_cashflow / s.info_market_cap * 100.0
        end as fcf_yield_pct,
        case
            when s.stmt_total_debt is not null
                and s.stmt_stockholders_equity is not null
                and s.stmt_stockholders_equity != 0
                then s.stmt_total_debt / s.stmt_stockholders_equity
        end as debt_to_equity,
        case
            when s.eff_stmt_op is not null
                and s.stmt_interest_expense is not null
                and s.stmt_interest_expense != 0
                then s.eff_stmt_op / abs(s.stmt_interest_expense)
        end as interest_coverage,
        case
            when s.stmt_current_assets is not null
                and s.stmt_current_liabilities is not null
                and s.stmt_current_liabilities != 0
                then s.stmt_current_assets / s.stmt_current_liabilities
        end as current_ratio_stmt,
        case
            when s.stmt_current_assets is not null
                and s.stmt_current_liabilities is not null
                then s.stmt_current_assets - s.stmt_current_liabilities
        end as working_capital,
        case
            when s.info_market_cap is not null
                and s.stmt_tangible_book_value is not null
                and s.stmt_tangible_book_value > 0
                then s.info_market_cap / s.stmt_tangible_book_value
        end as price_to_tangible_book,
        case
            when s.stmt_net_income is not null
                and s.stmt_total_revenue is not null
                and s.stmt_total_revenue != 0
                then s.stmt_net_income / s.stmt_total_revenue * 100.0
        end as net_margin_pct,
        case
            when s.stmt_net_income is not null
                and s.stmt_total_assets is not null
                and s.stmt_total_assets != 0
                then s.stmt_net_income / s.stmt_total_assets * 100.0
        end as roa_pct,
        case
            when s.stmt_net_income_common is not null
                and s.stmt_stockholders_equity is not null
                and s.stmt_stockholders_equity != 0
                then s.stmt_net_income_common / s.stmt_stockholders_equity * 100.0
        end as statement_roe_pct,
        s.info_dividend_yield as dividend_yield_pct,
        s.computed_fcf,
        case
            when s.computed_fcf is not null
                and s.computed_fcf < 0
                and s.stmt_cash_and_equivalents is not null
                then s.stmt_cash_and_equivalents / (-s.computed_fcf) * 12.0
        end as cash_runway_months,
        case
            when s.computed_fcf is not null
                and s.computed_fcf < 0
                then -s.computed_fcf / 12.0
        end as burn_rate_monthly,
        case
            when s.info_market_cap is not null
                and s.stmt_total_debt is not null
                and s.stmt_cash_and_equivalents is not null
                and (
                    s.info_market_cap + s.stmt_total_debt - s.stmt_cash_and_equivalents
                ) != 0
                then (s.stmt_cash_and_equivalents - s.stmt_total_debt)
                    / (s.info_market_cap + s.stmt_total_debt - s.stmt_cash_and_equivalents)
        end as net_cash_to_ev,
        case
            when s.info_market_cap is not null
                and s.stmt_cash_and_equivalents is not null
                and s.stmt_total_debt is not null
                and s.info_market_cap != 0
                then (s.stmt_cash_and_equivalents - s.stmt_total_debt) / s.info_market_cap
        end as net_cash_to_market_cap,
        -- Net cash as a money amount: the same numerator as net_cash_to_market_cap above,
        -- without the market-cap denominator. It replaces that ratio on the pre-revenue
        -- card because the ratio moves with the share price, and this pipeline refreshes
        -- twice a month -- a price-derived figure goes stale in a way the statement-derived
        -- ones do not. net_cash_to_market_cap itself is KEPT in the warehouse (it is simply
        -- no longer catalogued, so no card renders it); see .claude/task/contract.md.
        case
            when s.stmt_cash_and_equivalents is not null
                and s.stmt_total_debt is not null
                then s.stmt_cash_and_equivalents - s.stmt_total_debt
        end as net_cash,
        case
            when coalesce(s.info_sector, st.sector) = 'Financial Services'
                then 'financial'
            when s.stmt_total_revenue is not null
                and s.stmt_total_revenue <= 0
                then 'pre_revenue'
            -- Revenue technically positive but negligible relative to how the market values the
            -- company (< 0.1% of market cap) -- a development-stage company the strict <= 0 test
            -- misses by a hair. Real example: Deep Yellow (ASX: DYL), a uranium developer with
            -- $15,949 revenue against a $1.7B market cap (~0.001%) -- computing fcf_margin_pct/
            -- ebit_margin_pct on that denominator produced a -129,810%/-90,334% outlier that swamped
            -- its whole sector's range mark. Ratio, not an absolute currency floor: this app spans 6
            -- currencies (AUD/USD/GBP/EUR/JPY/CHF) with no FX normalization anywhere in the pipeline, so
            -- a flat dollar threshold would be unfair across markets. Requires market cap present and
            -- positive; a missing market cap leaves the company operating (a data gap, not a signal).
            when s.stmt_total_revenue is not null
                and s.stmt_total_revenue > 0
                and s.info_market_cap is not null
                and s.info_market_cap > 0
                and s.stmt_total_revenue / s.info_market_cap < 0.001
                then 'pre_revenue'
            else 'operating'
        end as company_type
    from resolved as s
    left join stocks as st
        on s.market_code = st.market_code
        and s.ticker = st.ticker
),

eligibility as (
    -- Per-type required sets (Sector/Lifecycle Router): financials qualify on a bank-appropriate
    -- pair, since the operating solvency/cash metrics are unsourceable for them; pre_revenue
    -- qualifies on net_cash alone (its survival card); operating keeps a four-metric AND.
    -- forward_pe was dropped from BOTH the financial and operating sets: a card
    -- must not be gated on a metric it does not display, and forward_pe is no longer
    -- catalogued (owner's call -- it carries the share price, which this twice-monthly
    -- pipeline cannot keep current). This ADMITS companies Yahoo has no forward P/E for, so
    -- expect the eligible-card count to rise; that is the intended effect, not a regression.
    select
        *,
        case company_type
            when 'financial' then list_filter(
                list_value(
                    if(statement_roe_pct is null, 'statement_roe_pct', null),
                    if(net_margin_pct is null, 'net_margin_pct', null)
                ),
                metric -> metric is not null
            )
            when 'pre_revenue' then list_filter(
                list_value(
                    if(net_cash is null, 'net_cash', null)
                ),
                metric -> metric is not null
            )
            else list_filter(
                list_value(
                    if(ebit_margin_pct is null, 'ebit_margin_pct', null),
                    if(revenue_growth_yoy_pct is null, 'revenue_growth_yoy_pct', null),
                    if(net_debt_to_ebitda is null, 'net_debt_to_ebitda', null),
                    if(fcf_margin_pct is null, 'fcf_margin_pct', null)
                ),
                metric -> metric is not null
            )
        end as missing_metrics,
        case company_type
            when 'financial' then (
                statement_roe_pct is not null
                and net_margin_pct is not null
            )
            when 'pre_revenue' then (
                net_cash is not null
            )
            else (
                ebit_margin_pct is not null
                and revenue_growth_yoy_pct is not null
                and net_debt_to_ebitda is not null
                and fcf_margin_pct is not null
            )
        end as is_card_eligible
    from metrics
)

select * from eligibility
