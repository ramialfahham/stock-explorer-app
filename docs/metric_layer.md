# Metric layer

> DURABLE. **Owns:** where metric definitions live, and what earns a catalogue row.
> **Never:** the definitions themselves. The `metric_catalogue.csv` seed owns those.

> How Stock Explorer keeps its card metrics consistent. Adapted from the football-data-pipeline
> metric-catalogue pattern. Short by design.

## Where each thing lives (read this first)

**`dbt_analytics/seeds/metric_catalogue.csv` is the single source of truth for every card metric** —
`metric_id`, formula spec (`base_relation` / `numerator_expr` / `denominator_expr`), `description`,
the analytical definition (`calculation` / `interpretation` / `applicability`), display `format`,
the display taxonomy (`perspective`, `importance_tier`, `display_order`, `direction`), the
`benchmarkable` flag, the `basis_column`, and the plain-language copy (`gloss` / `analogy` / `learn`).
No prose document defines a metric; docs *reference* the seed.

| You need… | Go to |
|---|---|
| a metric's definition / formula / format / copy | **the `metric_catalogue.csv` seed** (the SSoT) |
| where a metric is **computed** | `dbt_analytics/models/4_intermediate/int_stock__card_metrics.sql` (once) |
| the card-level data contract (grain, eligibility, export shape, freshness) | [`data_contract.md`](data_contract.md) |
| how the card consumes metrics | the frontend reads `frontend/metrics.json` (generated from the seed) |

## What earns a catalogue row

A metric can be computed and data-only. Cataloguing it is what RENDERS it: the seed feeds
`frontend/metrics.json`, which feeds `card_copy`, which feeds `card_ui`, uniformly. Adding a row
therefore puts the metric on the card.

Which company types see it is the seed's `applies_to` column. A metric whose `applies_to`
excludes a card's `company_type` is omitted from that card entirely -- no heading, no empty slot,
never a dash placeholder (`frontend/card_copy.py`, `frontend/card_ui.py`, pinned by
`tests/frontend/test_card_ui.py`).

## The three parts

1. **Each metric is computed in exactly one place.** `int_stock__card_metrics` computes every
   catalogued metric once; the marts and the Supabase export carry them downstream. The seed
   *defines*; the model *computes*.
2. **The catalogue is the registry + glossary.** The seed is the single list of every metric and its
   display/copy metadata. `scripts/export_metric_definitions_json.py` builds `frontend/metrics.json`
   from it; `frontend/card_copy.py` reads that JSON (no hardcoded metric dicts). It documents; it does
   not compute.
3. **Tests verify and guard.**
   - `dbt_analytics/seeds/_seeds.yml` — `not_null` / `unique` / `accepted_values` on the catalogue.
   - `tests/test_metric_catalogue.py` — every catalogue metric is computed in the model; the
     regenerated `metrics.json` matches the committed file (the frontend-bridge no-drift lock); the
     card-metrics table in `data_contract.md` matches a fresh render from the seed
     (`scripts/render_metric_table.py`, the docs no-drift lock); values are well-formed.

## What it is NOT

There is no bespoke "metric engine" and no SQL codegen: the `numerator_expr` / `denominator_expr`
columns are the definition/spec, not a generator — the model computes the metric by hand, once.

## Why the drift guard is in Python (not a dbt singular test)

The football project guards model→catalogue drift with a jinja column-introspection dbt test. This
repo's §1.1 SQL-structure gate (`scripts/check_dbt_sql_structure.py`) requires every `tests/*.sql` to
start with `WITH`, which that jinja style can't satisfy — so the equivalent guard lives in
`tests/test_metric_catalogue.py` (CI runs pytest). Same intent.

## Adding a metric

1. Add the computation to `int_stock__card_metrics` (one place).
2. Add the `metric_catalogue` row (id, label, formula spec, `calculation` / `interpretation` /
   `applicability`, format, `perspective`/tier/order, direction, copy, `applies_to`). The row
   is what renders the metric, so it must carry its per-type `applies_to` from the start; a
   row without one puts the metric on no card (an empty `applies_to` excludes every type),
   which is not a decision anyone made.
3. Regenerate the JSON and the contract table: `python scripts/export_metric_definitions_json.py`
   and `python scripts/render_metric_table.py`.
4. `dbt build` + `pytest tests/test_metric_catalogue.py` pass once all exist.

## Scope / follow-ups

- Phase 1 (this layer): catalogue SSoT + compute-once + JSON bridge + the guards above.
- Phase 2: retire the `scripts/metric_formulas.py` Python formula mirror and rework
  `audit_mart_vs_yfinance.py` to compare the mart against live yfinance (no second formula). Also
  candidate: a strict model→catalogue introspection guard, and folding the value-aware label/gloss
  variants (net-cash, annual-basis) into the catalogue.
