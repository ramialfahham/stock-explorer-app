# Development workflow — Stock Swipe App

How to change this repo safely. Agent behavior: [`working_agreement.md`](working_agreement.md).

---

## Branch and PR flow

1. `git checkout -b feature/short-description` from latest `main`
2. Implement; keep scope to the agreed task
3. Push and open PR; wait for **ci-validate** and review
4. Merge to `main`; scheduled pipeline picks up on next run

Never commit directly to `main`.

---

## CI tiers (economic)

See [`.github/workflows/ci-validate.yml`](../.github/workflows/ci-validate.yml).

### Tier A — every PR (~2–5 min)

Always runs:

- `scripts/check_layer_contract.py`
- `scripts/check_registry_var_sync.py`
- `dbt deps` + `dbt parse`
- After Tier B dbt build: `dbt docs generate`, then `scripts/check_dbt_documentation.py`

### Tier B — path-triggered

| Change area | Extra steps |
|-------------|-------------|
| `dbt_analytics/**` | `dbt build --select tag:staging`, `dbt build --select tag:base tag:core`, `check_dbt_documentation.py` |
| `ingestion/**`, `scripts/run_ingestion.py`, `storage/seeds/**` | Python import smoke test |
| `docs/market_registry.yml` | Registry sync (Tier A already covers) |

Doc-only PRs (`docs/**` excluding registry) skip Tier B dbt builds.

### Tier C — production (`data_pipeline.yml`)

Weekly / scheduled full run:

1. Ingest all active markets
2. `dbt build` (full)
3. `check_pipeline_completeness.py` (fail if gates not met)
4. `export_to_supabase.py`

Label `full-ci` on a PR or `workflow_dispatch` can trigger extended checks later if needed.

---

## Adding a market

1. Edit [`market_registry.yml`](market_registry.yml) — start with `ingest_active: false`
2. Add [`constituent_sources.yml`](constituent_sources.yml) entry
3. `python scripts/sync_dbt_vars.py`
4. Refresh seed: `python scripts/refresh_constituents.py --market <code>`
5. Run coverage audit on sample tickers (all five metrics via yfinance)
6. Flip `ingest_active: true`, sync vars, update Supabase `markets` row
7. Document in [`operations_guide.md`](operations_guide.md)

---

## Local setup

```bash
pip install -r requirements.txt
cp profiles.yml.example profiles.yml   # DuckDB path
cp .env.example .env                   # Supabase keys for export check
dbt deps --project-dir dbt_analytics --profiles-dir .
python scripts/check_supabase_connection.py
```

---

## Definition of done (features)

| Change type | Done when |
|-------------|-----------|
| Registry / market | Vars synced, seed exists, CI green |
| Ingestion | Raw parquet matches `data_contract.md` grain; no derived metrics in Python |
| dbt model | Layer folder correct, model + all column descriptions (anatomy in engineering_standards §2), tests, `dbt build` + `check_dbt_documentation.py` pass |
| Export | Upsert to Supabase documented; RLS unchanged for anon read |
| Docs | `north_star` / `data_contract` updated if behavior or schema changed |

---

## Ingestion skill (future)

When fundamentals ingestion stabilizes, add `.cursor/skills/stock-swipe-ingestion/SKILL.md`
pointing agents at registry, raw-only rule, parquet paths, and market activation checklist.
Do not derive metrics in Python.
