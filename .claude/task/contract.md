# Task contract

objective: Metric layer Phase 2 — retire the scripts/metric_formulas.py Python formula mirror so the dbt model is the only place card metrics are computed. Rework the audit to validate the mart by re-running dbt on freshly-fetched raw (no second formula), and drop the ingestion-side eligibility counter that mirrored the dbt gate.

scope_paths:
  - scripts/metric_formulas.py
  - scripts/audit_mart_vs_yfinance.py
  - ingestion/yfinance/ingest.py
  - ingestion/main.py
  - tests/test_metric_formulas.py
  - tests/test_audit_mart_vs_yfinance.py
  - docs/metric_audit.md
  - .github/workflows/ci-validate.yml
  - .claude/**

decisions_reserved:
  - (none new) — owner chose: audit re-runs dbt on fresh raw (full fidelity, no Python recompute); drop the ingestion fundamentals_eligible counter.

done_when:
  - scripts/metric_formulas.py is deleted; no module imports it (grep clean across repo, excluding history/docs).
  - ingestion/yfinance/ingest.py no longer computes metrics/eligibility: the fundamentals_eligible counter and its helpers (_is_card_eligible_raw, _has_operating_margin_inputs, _effective_net_debt) are removed. Ingestion still lands raw for every fetched ticker (raw-only contract intact). Ingestion tests pass.
  - audit_mart_vs_yfinance.py validates the mart by re-running dbt on fresh raw: it fetches fresh fundamentals for the sampled tickers, lands them as a temporary raw parquet set (same schema dbt sources expect), builds int_stock__card_metrics into a temp DuckDB via dbt, reads the dbt-computed metrics, and compares them to the mart (drift). No Python re-implementation of any metric formula. Offline mode (the CI smoke) still runs without live fetches or a dbt rebuild.
  - The CI "Metric audit script smoke (offline)" step still passes (adjust the invocation in ci-validate.yml only if needed).
  - tests/test_metric_formulas.py removed; audit behavior covered by tests/test_audit_mart_vs_yfinance.py where feasible (offline path at minimum). Full pytest green.
  - docs/metric_audit.md updated to describe the dbt-rerun method (no live_* Python recompute).
  - Review cycle recorded; PR opened to main (not merged).

impact_map: No dbt model / mart / Supabase change — int_stock__card_metrics and the export are untouched. Ingestion's raw parquet output is unchanged except the removed in-memory eligible counter (no landed-data change). The audit's *method* changes (now invokes dbt on a temp raw set instead of a Python recompute); it remains a QA tool, not part of the pipeline. The CI offline smoke is preserved.

amendments:
  - 2026-06-29 — initial Phase 2 contract. Surfaced during exploration: metric_formulas had a third consumer (ingest.py eligibility counter, observability-only — does not filter landed data); the audit's recompute covered net_debt_to_ebitda (no yahoo-native equivalent), so the owner chose the dbt-rerun approach over a yahoo-native-only audit to keep full fidelity.
  - 2026-06-29 — as-built: added ingestion/main.py to scope (it printed the dropped fundamentals_eligible stat). ci-validate.yml needed no change — the reworked audit keeps the --offline CLI, so the existing offline smoke step still passes. Round-trip mechanism proven, and the shipped _build_fresh_metrics_via_dbt verified end-to-end on synthetic raw.
