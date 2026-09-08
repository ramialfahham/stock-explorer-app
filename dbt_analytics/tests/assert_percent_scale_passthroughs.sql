-- Percent-scale guard for three Yahoo passthroughs; bands and rationale in docs/data_contract.md.
with
metrics as (
    select
        market_code,
        'dividend_yield_pct' as metric_name,
        0.5 as min_median_abs,
        50.0 as max_median_abs,
        dividend_yield_pct as metric_value
    from {{ ref('int_stock__card_metrics') }}

    union all

    select
        market_code,
        'revenue_growth_yoy_pct' as metric_name,
        1.0 as min_median_abs,
        100.0 as max_median_abs,
        revenue_growth_yoy_pct as metric_value
    from {{ ref('int_stock__card_metrics') }}

    union all

    select
        market_code,
        'roe_pct' as metric_name,
        1.0 as min_median_abs,
        200.0 as max_median_abs,
        roe_pct as metric_value
    from {{ ref('int_stock__card_metrics') }}
),

populated as (
    select
        market_code,
        metric_name,
        min_median_abs,
        max_median_abs,
        abs(metric_value) as abs_value
    from metrics
    where metric_value is not null
      and metric_value != 0
),

per_market as (
    select
        market_code,
        metric_name,
        min_median_abs,
        max_median_abs,
        count(*) as populated_count,
        median(abs_value) as median_abs
    from populated
    group by market_code, metric_name, min_median_abs, max_median_abs
)

select *
from per_market
where populated_count >= 5
  and (median_abs < min_median_abs or median_abs > max_median_abs)
