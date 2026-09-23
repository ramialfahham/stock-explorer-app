-- The deck reads this view: each company's newest row, minus any company 28+ days behind its
-- market's newest snapshot, so a card that stopped refreshing leaves instead of showing old numbers.
create view public.current_cards
with (security_invoker = true)
as
with latest as (
    select distinct on (market_code, ticker) *
    from public.mart_stock_cards
    order by market_code, ticker, snapshot_date desc
),

market_newest as (
    select
        market_code,
        max(snapshot_date) as newest_snapshot_date
    from public.mart_stock_cards
    group by market_code
)

-- The column list is fixed at creation: a migration altering mart_stock_cards must recreate this view.
select latest.*
from latest
inner join market_newest
    on latest.market_code = market_newest.market_code
where latest.snapshot_date > market_newest.newest_snapshot_date - 28;

grant select on public.current_cards to anon, authenticated, service_role;
