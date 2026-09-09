-- Atomic card export. Rationale, guarantees and known limits: docs/data_contract.md,
-- "Stale export policy". Replaces the batched upsert that could leave two snapshots mixed.

create or replace function public.replace_cards_snapshot(payload jsonb)
returns integer
language plpgsql
as $$
declare
    payload_keys text[];
    unknown_keys text;
    column_list text;
    inserted_count integer;
begin
    if payload is null or jsonb_typeof(payload) <> 'array' then
        raise exception 'replace_cards_snapshot: payload must be a JSON array';
    end if;

    -- An empty payload would delete nothing and insert nothing, but a caller that reaches
    -- here with one has lost its rows somewhere upstream and should hear about it.
    if jsonb_array_length(payload) = 0 then
        raise exception 'replace_cards_snapshot: payload is empty, refusing to write nothing';
    end if;

    if exists (
        select 1
        from jsonb_array_elements(payload) as elem
        where nullif(elem ->> 'snapshot_date', '') is null
           or nullif(elem ->> 'market_code', '') is null
    ) then
        raise exception
            'replace_cards_snapshot: every row must carry a market_code and a snapshot_date';
    end if;

    select array_agg(distinct key)
    into payload_keys
    from jsonb_array_elements(payload) as elem, jsonb_object_keys(elem) as key;

    -- PostgREST rejected a payload naming a column the table lacks; jsonb_populate_recordset
    -- silently drops it instead, which would report a clean export while losing that column.
    select string_agg(quote_ident(key), ', ')
    into unknown_keys
    from unnest(payload_keys) as key
    where not exists (
        select 1
        from pg_attribute
        where attrelid = 'public.mart_stock_cards'::regclass
          and attnum > 0
          and not attisdropped
          and attidentity = ''
          and attgenerated = ''
          and attname = key
    );

    if unknown_keys is not null then
        raise exception
            'replace_cards_snapshot: payload names columns that cannot be inserted: %',
            unknown_keys;
    end if;

    -- Only the columns the payload carries. Listing every table column instead would force an
    -- explicit NULL into any column the export does not send, overriding its DEFAULT. The keys
    -- are unioned across all elements, so a column keeps its DEFAULT only when EVERY element
    -- omits it; a column one element omits is listed and takes NULL from the null-rowtype base.
    -- Both DEFAULT columns here are also NOT NULL, so that aborts rather than writing wrong
    -- values, and the only caller sends an identical key set on every element.
    -- attidentity/attgenerated exclude generated columns by definition rather than by name.
    -- Derived from the catalog rather than written out: a literal column list would be a
    -- fourth hand-maintained copy of this schema, alongside the dbt contract, EXPORT_COLUMNS
    -- and the migrations, of which only the dbt contract is machine-checked.
    select string_agg(quote_ident(attname), ', ' order by attnum)
    into column_list
    from pg_attribute
    where attrelid = 'public.mart_stock_cards'::regclass
      and attnum > 0
      and not attisdropped
      and attidentity = ''
      and attgenerated = ''
      and attname = any(payload_keys);

    if column_list is null then
        raise exception 'replace_cards_snapshot: payload carries no insertable columns';
    end if;

    -- Scoped to the (market, date) pairs the payload actually covers. Deleting by date
    -- alone would wipe every other market's rows at that date without restoring them, and a
    -- partial payload is the normal output of the per-market re-run this design exists to
    -- support. Every date the payload carries is replaced, not just one.
    delete from public.mart_stock_cards as target
    using (
        select distinct
            elem ->> 'market_code' as market_code,
            (elem ->> 'snapshot_date')::date as snapshot_date
        from jsonb_array_elements(payload) as elem
    ) as covered
    where target.market_code = covered.market_code
      and target.snapshot_date = covered.snapshot_date;

    execute format(
        'insert into public.mart_stock_cards (%s) '
        'select %s from jsonb_populate_recordset(null::public.mart_stock_cards, $1)',
        column_list, column_list
    ) using payload;

    get diagnostics inserted_count = row_count;
    return inserted_count;
end;
$$;

-- 011_grant_roles.sql granted service_role select/insert/update but not delete, which this
-- function needs. Granted rather than making the function SECURITY DEFINER: a definer body
-- that is wholly dynamic SQL would need search_path hardening and owner pinning for less
-- benefit, and service_role already has update on every row of this table.
grant delete on public.mart_stock_cards to service_role;

revoke all on function public.replace_cards_snapshot(jsonb) from public;
grant execute on function public.replace_cards_snapshot(jsonb) to service_role;
