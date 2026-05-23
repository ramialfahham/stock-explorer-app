# dbt Layering Rules

This document defines what is allowed in each dbt layer.
Use it together with `engineering_standards.md`.

---

## Layer Cheat Sheet

| Layer            | Folder            | Materialisation | Purpose |
|------------------|-------------------|-----------------|---------|
| `1_staging`      | `models/1_staging/`    | view   | Source-near cleanup |
| `2_base`         | `models/2_base/`       | view   | Cross-source union and dedup |
| `3_core`         | `models/3_core/`       | table  | Canonical dims and facts |
| `4_intermediate` | `models/4_intermediate/` | table | Complex logic for marts |
| `5_marts`        | `models/5_marts/`      | table or view | Consumption layer |

---

## 1_staging

Purpose: source-near cleanup with minimal transformation.

Allowed:
- 1:1 mapping from a single raw source table.
- Column renaming to snake_case.
- Safe type casting and light normalisation.
- JSON extraction and flattening to expose typed columns.
- Model-level tests: grain documented in description, `not_null` on required fields,
  `unique` or composite unique on grain keys.

Not allowed:
- Unions across sources or entities.
- Business rules or derived metrics.
- Cross-source joins.
- Helper models that are not direct source mappings.

---

## 2_base

Purpose: entity resolution and alignment across sources, preparation for core.

Allowed:
- Unions across staging models where the same real-world entity appears in multiple sources.
- Standardised keys and attributes downstream layers can rely on.
- Structural tests on grains and keys defined here.

Not allowed:
- Declaring the authoritative business fact or dimension (that belongs in core).
- Presentation or delivery logic aimed at a specific consumer.

---

## 3_core

Purpose: system of record. Canonical dimensions and facts with stable grains and
vetted definitions that other layers treat as the single source of truth.

Allowed:
- Dimensions and facts shared across multiple use cases.
- Relationship logic and conformed attributes that marts should reuse rather than re-derive.

Not allowed:
- Wide, consumer-specific projections (those belong in marts).

### Dimension qualification rules

A table earns `dim_` status only when all three conditions hold:

1. **Entity.** It represents a real-world thing the business talks about by name.
2. **Reuse.** Its attributes are shared across more than one fact or mart.
3. **Conformance.** The vocabulary is one the whole warehouse agrees on.

Patterns that look like dimensions but are not:
- **Degenerate dimension.** A natural key with no independent attributes: keep it on the fact.
- **Closed enum.** A small, stable vocabulary: enforce with `accepted_values`; a dim adds
  maintenance without adding information.
- **Attribute masquerading as entity.** Promote to a dim only when a rollup or hierarchy
  is actually needed, not before.

### Fact qualification rules

A table earns `fct_` status only when all three conditions hold:

1. **Event or measurement.** It captures something that happened or a state at a point in time.
2. **Dimensional context.** It joins to one or more dims via foreign keys.
3. **Measures or atomic grain.** It carries additive/semi-additive measures, or it is the
   atomic grain that downstream models aggregate.

Patterns that look like facts but are not:
- **Derived metric table.** Rankings or aggregates over a fact belong in `intermediate` or
  `marts`, not `core`.
- **Consumer-specific denormalisation.** A wide per-entity summary shaped for one app is a
  mart, not a core fact.

---

## 4_intermediate

Purpose: complex logic, multi-step calculations, and cross-table joins that would make
marts too heavy or repetitive if written inline.

Allowed:
- Reusable logic blocks shared by multiple mart models.
- Windowed or multi-stage calculations.
- Joins and reshaping internal to the warehouse graph.

Not allowed:
- End-user-facing table design (that is a marts concern).
- `ref('mart_*')` — intermediate feeds marts, never the reverse.

---

## 5_marts

Purpose: consumption layer. Flattened, query-efficient datasets shaped for known consumers
(applications, exports, BI tools) without requiring consumers to navigate the full graph.

Allowed:
- Models shaped for a specific consumer with clear grains and documented columns.
- Denormalisation and pre-aggregation where they improve latency or usability.

Not allowed:
- Redefining core business truth already centralised in `core`. Marts select and present;
  they do not fork definitions silently.

---

## Testing Guidance by Layer

| Layer          | Focus |
|----------------|-------|
| `1_staging`    | Grain documentation, not_null, unique on grain keys |
| `2_base`       | Key integrity after union, structural assertions |
| `3_core`       | Relationship tests, business-rule assertions |
| `4_intermediate` | Logic correctness, expected ranges |
| `5_marts`      | Consumer-contract tests: required columns, accepted values, metric consistency |

Every new model requires at least one meaningful test.
