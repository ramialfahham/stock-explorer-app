-- Drop the precision caps on mart_stock_cards. Migration 002 created its numeric columns as
-- numeric(10,4) / numeric(18,6); every column added since is plain numeric. The dbt contract
-- and docs/data_contract.md know no cap, and numeric(10,4) overflows above 999,999.9999, so one
-- Yahoo outlier (revenue_growth_yoy_pct is info_revenue_growth * 100, unbounded) would abort
-- the whole atomic export. The columns are found from the catalogue, not listed by hand.

do $$
declare
    col record;
    remaining integer;
begin
    for col in
        select attname
        from pg_attribute
        where attrelid = 'public.mart_stock_cards'::regclass
          and attnum > 0
          and not attisdropped
          and atttypid = 'numeric'::regtype
          and atttypmod <> -1
    loop
        execute format(
            'alter table public.mart_stock_cards alter column %I type numeric',
            col.attname
        );
    end loop;

    select count(*)
    into remaining
    from pg_attribute
    where attrelid = 'public.mart_stock_cards'::regclass
      and attnum > 0
      and not attisdropped
      and atttypid = 'numeric'::regtype
      and atttypmod <> -1;

    if remaining <> 0 then
        raise exception '019: % numeric column(s) on mart_stock_cards still carry a precision cap',
            remaining;
    end if;
end
$$;
