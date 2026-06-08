select
    market_code,
    ticker,
    snapshot_date,
    company_name,
    sector,
    missing_metrics,
    is_card_eligible
from {{ ref('int_stock__card_metrics') }}
where not is_card_eligible
