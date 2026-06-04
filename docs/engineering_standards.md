# dbt Engineering Standards

Practical standards for analytics engineering.
Use together with `layering.md` (layer rules and materialisations).

---

## 1. Naming Conventions

Models use lowercase snake_case, prefixed by layer:

| Layer          | Prefix pattern |
|----------------|----------------|
| staging        | `stg_<source>__<entity>` |
| base           | `base_<domain>__<entity>` |
| core dims      | `dim_<entity>` |
| core facts     | `fct_<entity>` |
| intermediate   | `int_<domain>__<purpose>` |
| marts          | `mart_<domain>__<purpose>` |

Column conventions:
- All columns: lowercase snake_case
- Booleans: `is_` or `has_` prefix
- Timestamps: `_at` suffix
- Dates: `_date` suffix
- Surrogate keys: `_sk` suffix
- Natural/source keys: `_id` suffix

---

## 1.1. SQL Structure

- Every model starts with import CTEs — one per `ref()` or `source()` — before any
  transformation logic.
- Use named CTE chains. No inline subqueries (`FROM (SELECT ...)`).
- Each CTE has a single purpose: import, flatten, dedupe/rank, or final projection.
- CTE names are descriptive and stable (not `cte1`, `temp`, `final2`).

```sql
-- Good structure
with
source as (
    select * from {{ ref('stg_example__entity') }}
),
ranked as (
    select
        *,
        row_number() over (partition by id order by updated_at desc) as rn
    from source
),
deduped as (
    select * from ranked where rn = 1
)

select * from deduped
```

---

## 1.2. Comment Policy

Comments convey **why**, not **what**. Well-named identifiers already describe what.

Write a comment when:
- A design decision has a non-obvious reason
- An invariant must hold for downstream code to be correct
- A workaround exists for a specific data quirk or external constraint
- The behaviour would surprise a competent reader unfamiliar with the domain

Do not write a comment when:
- The code reads clearly from its identifiers and structure
- You would only be paraphrasing the next line
- The context belongs in the PR description

One sentence per comment is almost always enough. No multi-line comment blocks.

---

## 2. Documentation Policy

Canonical metric and eligibility definitions live in [`data_contract.md`](data_contract.md).
YAML descriptions summarize for stakeholders; do not fork formulas in prose.

### Required coverage

- Every **model** must have a non-empty `description` in YAML (same PR as the model).
- Every **column** in every model must have a non-empty `description` in YAML.
- Every **source** and source **table** must have a `description` in `sources.yml`.
- Source **columns** must be documented when listed in `sources.yml`.

CI enforces this via `scripts/check_dbt_documentation.py` after `dbt build`.

### Model description anatomy

Use multiline YAML (`description: >`) with labeled sections. Staging may use
`Source:` instead of `What:`.

**Core / intermediate / marts:**

```yaml
description: >
  **What:** One-line business purpose.
  **Grain:** One row per (keys…).
  **Source:** Upstream refs or raw source.
  **Used by:** Consumer (e.g. Supabase export, Streamlit).
```

**Staging / base:**

```yaml
description: >
  **Source:** Raw parquet or upstream staging model.
  **Grain:** One row per (keys…).
  **What:** Typed cleanup / dedup only — no business metrics.
```

Reject grain-only one-liners (e.g. `"Grain: one row per ticker"` with no What/Source).

### Column description anatomy

```yaml
description: >
  Business meaning. Unit or scale (percent 0–100, ratio, ISO currency).
  Null when: missing upstream field or ineligible ticker (see data_contract).
```

Staging columns: map to yfinance/parquet field name; note raw vs derived.

### Shared long text

Use `docs` blocks in `dbt_analytics/models/_docs.md` and `'{{ doc("block_name") }}'`
in YAML for eligibility rules and metric definitions reused across models.

### Style

- Business-focused, factual, concise — no SQL implementation detail.
- Align names and units with [`data_contract.md`](data_contract.md).

---

## 3. Testing Policy

- Every new model requires at least one meaningful test.
- `staging`: `not_null` on required fields + `unique` or composite unique on grain key.
  Do not repeat the same uniqueness assertion downstream if the grain hasn't changed.
- `base`: structural integrity after unions — `not_null` on keys, `unique` on new grains.
- `core` / `intermediate`: relationship tests and business-rule assertions.
- `marts`: consumer-contract tests — required columns, accepted value ranges,
  metric consistency with upstream core definitions.

---

## 4. Model Contracts and Metadata

- Add `meta` fields for ownership on every model:
  - `owner`
  - `domain`
  - `criticality` (`low | medium | high`)
- Use `tags` consistently (e.g. `daily`, `realtime`, `export`).
- Apply model contracts for stable `marts` outputs once schemas stabilise.

---

## 5. Environment and Promotion

- Keep `profiles.yml` out of git.
- Use separate targets for `dev` and `prod`.
- Validate in `dev` before promoting to `prod`.
- Do not introduce breaking mart schema changes without a migration plan.

---

## 6. Change Management

- Prefer additive changes over destructive renames or drops.
- If output schema must change, document: what changes, why, and migration impact
  for downstream consumers.
- Keep marts stable — they are product/API contracts.

---

## 7. Security and Secrets

- Never commit API keys, credentials, or secret env values.
- Use environment variables for all external authentication.
- Load secrets via `python-dotenv` or equivalent — never hardcode.
- Keep service roles least-privileged.

---

## 8. CI Minimum Gate

Every PR should pass before merge:

1. `dbt deps`
2. `dbt parse`
3. `dbt build --select staging`
4. `dbt build --select tag:base tag:core`
5. `dbt docs generate` then `python scripts/check_dbt_documentation.py` (requires `target/catalog.json`)

Before release to prod:

6. `dbt build` (full run)
