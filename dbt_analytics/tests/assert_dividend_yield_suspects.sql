-- Rows whose raw dividendYield arrived fraction-scale (issue #10). int_stock__card_metrics
-- scales these to percent; this lists them so every run counts them instead of guessing.
with
fundamentals as (
    select * from {{ ref('fct_fundamentals_snapshot') }}
),

suspects as (
    select
        market_code,
        ticker,
        snapshot_date,
        info_dividend_yield
    from fundamentals
    where info_dividend_yield < 0.05
)

select * from suspects
