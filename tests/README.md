# Tests

The Python suite is split by **domain**, mirroring where the code under test lives. `sys.path` is
set once in [`conftest.py`](conftest.py) (repo root + `frontend/` + `scripts/`), so tests import
without per-file path boilerplate.

| Directory | What it tests | Imports under test | Run |
|-----------|---------------|--------------------|-----|
| `tests/ingestion/` | yfinance extraction logic (balance sheet, quarterly TTM) | `ingestion.yfinance.*` | `pytest tests/ingestion` |
| `tests/frontend/` | Streamlit UI helpers/components (card copy & HTML, nav, filters, disclosure, live quote, saved news, …) | `frontend/*` modules | `pytest tests/frontend` |
| `tests/tooling/` | CI gate scripts + the metric-layer contract (export-health, mart audit, `metric_catalogue` seed↔model↔frontend integrity) | `scripts/*` + the catalogue seed | `pytest tests/tooling` |

## What we test where (project-wide taxonomy)

pytest covers **ingestion, frontend, and tooling**. The **transformation layer is tested in dbt,
not Python** — do not add SQL/metric-logic assertions here.

| Layer | What's verified | Where it lives | Runner |
|-------|-----------------|----------------|--------|
| Ingestion | yfinance extraction — labels, signs, null-safety | `tests/ingestion/` | pytest |
| Transformation — logic | metric formulas & guards, eligibility, company_type | dbt `unit_tests:` in model YAML | `dbt build` |
| Transformation — data | grain/uniqueness, `not_null`, `accepted_values`, business rules | model/seed `data_tests:` | `dbt build` |
| Transformation — cross-model | mart↔card parity, referential integrity | `dbt_analytics/tests/*.sql` (singular) | `dbt build` |
| Project lint / warehouse gates | test & doc coverage, layer contract, eligibility baseline, export fill-rate, mart-vs-yfinance drift | `scripts/check_*.py`, `scripts/audit_*.py` | python (CI) |
| Frontend | Streamlit copy / components | `tests/frontend/` | pytest |

The dbt-test rules live in [`docs/engineering_standards.md` §3](../docs/engineering_standards.md).
