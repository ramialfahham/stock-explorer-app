-- Catches a provider dropping a field: each shown metric must fill half of a type's eligible
-- cards per market (docs/data_contract.md, "Fill floor").
{% set operating = ['ebit_margin_pct', 'revenue_growth_yoy_pct', 'net_debt_to_ebitda', 'fcf_margin_pct'] %}
{% set statement = ['debt_to_equity', 'current_ratio_stmt', 'statement_roe_pct', 'net_margin_pct', 'roa_pct'] %}
{% set pre_revenue = ['net_cash', 'working_capital', 'cash_runway_months', 'burn_rate_monthly'] %}
{% set metric_ids = operating + statement + pre_revenue %}
with
cards as (
    select * from {{ ref('mart_stock_cards') }}
),

catalogue as (
    select * from {{ ref('metric_catalogue') }}
),

unpivoted as (
    {% for metric_id in metric_ids %}
    select
        market_code,
        company_type,
        '{{ metric_id }}' as metric_id,
        {{ metric_id }} is not null as is_filled
    from cards
    where is_card_eligible
    {% if not loop.last %}
    union all
    {% endif %}
    {% endfor %}
),

applicable as (
    select
        unpivoted.market_code,
        unpivoted.company_type,
        unpivoted.metric_id,
        unpivoted.is_filled
    from unpivoted
    inner join catalogue
        on unpivoted.metric_id = catalogue.metric_id
        and list_contains(
            list_transform(string_split(catalogue.applies_to, '|'), x -> trim(x)),
            unpivoted.company_type
        )
),

fill_rates as (
    select
        market_code,
        company_type,
        metric_id,
        count(*) as eligible_rows,
        avg(case when is_filled then 1.0 else 0.0 end) as fill_rate
    from applicable
    group by market_code, company_type, metric_id
)

select *
from fill_rates
where eligible_rows >= 5
  and fill_rate < 0.5
