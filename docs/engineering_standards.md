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

Applies to all SQL under `dbt_analytics/models/` and `dbt_analytics/tests/` (including
singular data tests). dbt only requires one `SELECT` returning failing rows for tests;
this project requires the same CTE structure as models.

- Every file starts with a `WITH` clause and import CTEs — one per `ref()` or `source()`
  — before transformation logic (`from {{ ref('...') }}` inside a CTE body).
- Use named CTE chains. No inline subqueries (`FROM (SELECT ...)`).
- No scalar subqueries in the `SELECT` list (e.g. `(select count(*) from ...)`); use CTEs.
- Each CTE has a single purpose: import, flatten, dedupe/rank, or final projection.
- CTE names are descriptive and stable (not `cte1`, `temp`, `final2`).
- Singular tests: no trailing semicolon; one-line **why** comments allowed (§1.2).

**Enforcement:** SQLFluff ([`.sqlfluff`](../.sqlfluff), `structure.subquery` with
`forbid_subquery_in = both`) plus `scripts/check_dbt_sql_structure.py` for rules
SQLFluff cannot express. Generic dbt examples do not override this section.

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

### Rules

- Singular SQL tests in `dbt_analytics/tests/` follow §1.1 (import CTE per `ref()`,
  named CTE chain, final `select` of failing rows only).
- Every SQL model requires at least one **model-level** test (YAML `data_tests`,
  `unit_tests`, or a singular test that `ref()`s the model).
- Column-level `data_tests` supplement model tests; they do not replace them.
- `staging`: `not_null` on grain keys + `dbt_utils.unique_combination_of_columns` on grain.
- `base`: same grain discipline after unions; do not re-assert the same uniqueness if grain unchanged.
- `core` / `intermediate`: grain tests plus `dbt_utils.expression_is_true` for business rules.
- `marts`: consumer contract — grain, eligibility columns, metric ranges; singular tests for
  cross-model consistency (row counts, referential integrity).

### Examples by layer

**Staging** (`stg_yf__constituents`):

```yaml
data_tests:
  - dbt_utils.unique_combination_of_columns:
      arguments:
        combination_of_columns: [market_code, ticker]
columns:
  - name: market_code
    data_tests: [not_null]
```

**Intermediate** (`int_stock__card_metrics`):

```yaml
data_tests:
  - dbt_utils.unique_combination_of_columns: ...
  - dbt_utils.expression_is_true:
      arguments:
        expression: >-
          is_card_eligible = (forward_pe is not null and ...)
unit_tests:
  - name: card_metrics_eligible_when_all_inputs_present
    model: int_stock__card_metrics
```

**Singular** (`dbt_analytics/tests/`): assert failing rows only; see §1.1.

### CI vs production gates

| Gate | When | What it checks |
|------|------|----------------|
| `check_dbt_tests.py` | Every PR (Tier A, after `dbt parse`) | Each model has ≥1 test; ≥3 singular SQL tests |
| `dbt build` / `dbt test` | PR + Tier C | Tests execute against fixtures or full data |
| `check_pipeline_completeness.py` | Tier C (`data_pipeline.yml`) | Eligible card counts per active market — not SQL style |

### Python tests and gates

The rules above govern **dbt** tests. Python tests live in `tests/`, split by domain
(`ingestion/`, `frontend/`, `tooling/`) with `sys.path` centralized in `tests/conftest.py` — see
[`tests/README.md`](../tests/README.md) for the full "what we test where" taxonomy. In short:
**ingestion, frontend, and tooling** are tested with pytest; **transformation logic stays in dbt**
(unit + data + singular tests); whole-warehouse and project-lint checks are `scripts/check_*.py`.

Generic dbt examples do not override this section.

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

1. `python scripts/check_dbt_sql_structure.py`
2. `sqlfluff lint dbt_analytics/models dbt_analytics/tests` (requires `profiles.yml` from
   `profiles.yml.example` for the dbt templater)
3. `dbt deps`
4. `dbt parse`
5. `python scripts/check_dbt_tests.py`
6. `dbt build --select staging`
7. `dbt build --select tag:base tag:core`
8. `dbt docs generate` then `python scripts/check_dbt_documentation.py` (requires `target/catalog.json`)

Before release to prod:

9. `dbt build` (full run)
