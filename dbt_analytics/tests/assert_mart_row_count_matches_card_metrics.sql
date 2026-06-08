-- Mart is eligible-only; row count must match eligible card metrics (no fanout).
with
mart as (
    select * from {{ ref('mart_stock_cards') }}
),

eligible_metrics as (
    select * from {{ ref('int_stock__card_metrics') }}
    where is_card_eligible
),

mart_count as (
    select count(*) as row_count
    from mart
),

metrics_count as (
    select count(*) as row_count
    from eligible_metrics
),

comparison as (
    select
        mart_count.row_count as mart_count,
        metrics_count.row_count as metrics_count
    from mart_count
    cross join metrics_count
)

select *
from comparison
where mart_count != metrics_count
