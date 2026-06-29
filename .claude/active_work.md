# Active work — handover

_The next session is handed exactly this file. Keep it current._

## Current task

**Project evaluation → improvement.** The owner is unhappy with the project's state; the lead, concrete
complaint is the **UI: inconsistent design/formatting, cluttered**. We agreed to fix foundations first,
then the UI. In flight: **metric layer Phase 1** — PR #131 (branch `feat/metric-layer`).

## Status

**Metric layer Phase 1 — PR open, awaiting CI + owner merge:** https://github.com/ramialfahham/stock-swipe-app/pull/131
- Adds `dbt_analytics/seeds/metric_catalogue.csv` (SSoT for the 5 metrics), `_seeds.yml`,
  `scripts/export_metric_definitions_json.py` → `frontend/metrics.json`, refactors `frontend/card_copy.py`
  to source from the JSON, `tests/test_metric_catalogue.py`, `docs/metric_layer.md`, and points
  `data_contract.md` at the seed. Mirrors the football-data-pipeline metric_catalogue pattern.
- Compute unchanged (`int_stock__card_metrics`); card renders BYTE-IDENTICAL. Verified locally: dbt
  parse/seed/13 schema tests, 77 pytest, SQL-structure + doc gates all green.

## Next concrete action

Owner reviews + merges #131 (do NOT self-merge). After merge, the planned sequence:
1. **Metric layer Phase 2** (separate task): retire `scripts/metric_formulas.py` (the Python formula
   mirror football proves you don't need) and rework `audit_mart_vs_yfinance.py` to compare the mart
   vs live yfinance. Optional: strict model→catalogue introspection guard.
2. **UI redesign** — build a redesigned-card MOCK first (one cohesive surface, one disclosure pattern,
   consistent labels incl. the deferred (TTM) dynamic-suffix, real spacing/type scale, words-not-arrows
   benchmarks), iterate, then implement in Streamlit consuming `metrics.json`. The UI mock was the
   originally-agreed next step before the owner asked for the metric layer first.

## Decisions locked this session

- Metric layer = a dbt-seed `metric_catalogue` (football pattern), built BEFORE the UI mock so the mock
  consumes a single source. See [[no-duplicate-sources]].
- Phase 1 is a ZERO-text-change port; the (TTM) label-leak fix is deferred to the UI work (touches
  metric_school.py — a UX wording change).
- Drift guard is a Python test, not a dbt singular test — repo's §1.1 SQL-structure gate (WITH-first)
  is incompatible with football's jinja introspection style.

## Do NOT

- Do not commit/push to `main`; do not `gh pr merge`. Agent commits need `gitleaks` on PATH (the
  pre-commit hook); export it from the WinGet Packages dir if a commit hook fails to find it.
- Do not reword metric copy (labels/gloss/analogy/learn) — owner content (§6); port verbatim.
- Do not enable ruff-format or broaden the dbt MCP beyond read-only without asking.

## Context / open items

- **Backend fragility (track B):** the deployed app at https://stock-explorer.streamlit.app/ runs on a
  **free-tier Supabase** that pauses after ~7 days idle (DNS drops → the app shows repeated "Could not
  load cards" errors, and renders that error 4× — a real bug: `_ensure_all_cards` is called repeatedly
  per render). It was restored this session (857 eligible cards, healthy coverage). Will recur — decide
  keep-alive vs paid tier vs accept manual restore.
- A separate branch `docs/refresh-june-2026` holds unrelated in-flight docs work (other chat); leave it.
- Throwaway render harness lives in the session scratchpad (`card_preview.py`); not in the repo.
