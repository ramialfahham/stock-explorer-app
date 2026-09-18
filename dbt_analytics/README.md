# dbt_analytics

dbt project for the Stock Explorer transform layer.

## Docs (authoritative)

- [`docs/layering.md`](../docs/layering.md)
- [`docs/engineering_standards.md`](../docs/engineering_standards.md)
- [`docs/working_agreement.md`](../docs/working_agreement.md)
- [`docs/project_context.md`](../docs/project_context.md) — DuckDB layout, yfinance naming, export

## Layout

```
models/
  1_staging/<source>/   # stg_<source>__<entity>
  2_base/               # base_<domain>__<entity>
  3_core/               # dim_*, fct_*
  4_intermediate/       # int_<domain>__<purpose>
  5_marts/              # mart_<domain>__<purpose>
```

## Commands (from repo root)

```bash
dbt debug   --project-dir dbt_analytics --profiles-dir .
dbt deps    --project-dir dbt_analytics --profiles-dir .
dbt parse   --project-dir dbt_analytics --profiles-dir .
dbt build   --project-dir dbt_analytics --profiles-dir .
```

After changing `docs/market_registry.yml`:

```bash
python scripts/sync_dbt_vars.py
```
