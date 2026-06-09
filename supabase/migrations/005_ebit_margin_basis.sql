-- Operating margin period basis for honest card labels (TTM vs annual fallback)

alter table public.mart_stock_cards
add column if not exists ebit_margin_basis text;
