# Stock Swipe App

> DURABLE. **Owns:** the map -- what this project is, and which file owns what. Injected into
> every session, so the hard rules a session must not miss are surfaced here as POINTERS.
> **Never:** the substance itself. Where this file summarises, the linked doc wins on conflict.

A card-based stock dashboard. Users are shown stock cards per session and save/skip them.
Pipeline: Python ingestion (yfinance → raw parquet) → dbt transforms on an ephemeral
DuckDB → export marts to Supabase (Postgres) → Streamlit reads the card marts. Markets are
partitioned by `market_code` from [`docs/market_registry.yml`](docs/market_registry.yml).

## Working agreement (read first)

@.claude/working-agreement.md

The essence:

- Every change runs **Explore → Plan → Confirm → Implement → Verify**. Confirm means
  **wait for an explicit "go" before editing or running anything.**
- Never commit or push to `main`. Branch, open an MR, let the user merge.
- The decisions in §6 (product, naming, anything permanent, new mechanisms, cost) are the
  user's — escalate, don't decide.
- **No em-dash or en-dash on any line you add or edit, in any file.** Use `--`. Nothing enforces
  this; it holds at review time only. Full rule and the rest of the prose and comment conventions:
  [`docs/engineering_standards.md`](docs/engineering_standards.md) §1.2 and §1.3.

## Stack

- **Ingestion:** Python + yfinance (`ingestion/`, `scripts/run_ingestion.py`)
- **Transform:** dbt-core + dbt-duckdb, ephemeral DuckDB (`dbt_analytics/`)
- **Warehouse / export:** Supabase (Postgres) — `supabase/migrations/`, `scripts/export_to_supabase.py`
- **Frontend:** Streamlit on Render (`frontend/app.py`)
- **CI:** GitLab CI (`.gitlab-ci.yml`)
- Python 3.11. Run dbt from the repo root: `dbt <cmd> --project-dir dbt_analytics --profiles-dir .`

## Layout

- `dbt_analytics/` — dbt project; layers `models/1_staging → 2_base → 3_core → 4_intermediate → 5_marts`
- `ingestion/` — raw data fetch (yfinance, constituents); raw fields only, no derived metrics
- `scripts/` — pipeline + CI gates (layer contract, registry sync, dbt test/doc checks, export)
- `frontend/` — Streamlit app
- `supabase/` — SQL migrations + export target
- `docs/` — project knowledge (see below)
- dbt layer rules: [`docs/layering.md`](docs/layering.md)

## Project knowledge (authoritative docs)

Substance lives in `docs/` — link to these rather than restating them:

- dbt layering contract: [`docs/layering.md`](docs/layering.md)
- Naming, SQL structure (§1.1), testing, documentation, CI gate: [`docs/engineering_standards.md`](docs/engineering_standards.md)
- Stock-specific extensions (markets, DuckDB, ingestion, Supabase export): [`docs/project_context.md`](docs/project_context.md)
- Card metrics + eligibility data contract: [`docs/data_contract.md`](docs/data_contract.md)
- Branch/PR/CI flow and definition-of-done: [`docs/development_workflow.md`](docs/development_workflow.md)
- **UX PR gate** (required for Streamlit layout / copy / interaction changes): [`docs/working_agreement.md`](docs/working_agreement.md)
- Product behavior (north star): [`docs/north_star.md`](docs/north_star.md); UI component specs: [`docs/ui/`](docs/ui/)

## Guardrails

This repo uses the [`dbt-agent-kit`](https://github.com/ramialfahham/dbt-agent-kit)
plugin: session handover, plan-back gate, pre-push checks, blinded reviewers, and a
blocking review gate. Task contracts live in `.claude/task/`, review routing in
[`.claude/review_routing.json`](.claude/review_routing.json). The session handover is
[`.claude/active_work.md`](.claude/active_work.md) — keep it current so a fresh chat
continues from the documented state.
