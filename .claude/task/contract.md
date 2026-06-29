# Task contract

objective: Introduce a metric layer mirroring the football project's pattern — a `metric_catalogue` seed as the single source of truth for the five card metrics (formula spec + format + direction + group/tier/order + copy), with the existing dbt model as the compute-once home, a drift guard test, and the frontend sourcing metric display from it. Phase 1 of 2.

scope_paths:
  - dbt_analytics/seeds/metric_catalogue.csv
  - dbt_analytics/seeds/_seeds.yml
  - scripts/export_metric_definitions_json.py
  - frontend/metrics.json
  - frontend/card_copy.py
  - tests/test_metric_catalogue.py
  - docs/metric_layer.md
  - docs/data_contract.md
  - .claude/**

decisions_reserved:
  - Metric wording (labels, gloss, analogy, learn copy) is owner content (§6). PORT existing strings from card_copy.py / data_contract.md verbatim into the seed — do NOT reword or invent. Phase 1 is a ZERO-text-change port: the seed holds today's exact strings (incl. "Operating margin (TTM)") and card_copy keeps its value-aware overrides; the card renders byte-identically. The "(TTM)/(annual)" dynamic-suffix / label-leak cleanup is DEFERRED to the UI work (it touches metric_school.py and is a UX wording decision).
  - Frontend-bridge choice (generated frontend/metrics.json vs frontend reads the seed CSV directly) — proposing the JSON export to mirror football; flagged for the owner in the plan-back.
  - NO SQL codegen from the seed exprs (mirror football: seed defines, model computes once; numerator/denominator are spec + resolvability-tested, not a code generator).
  - Phase 2 (retire scripts/metric_formulas.py mirror + rework audit_mart_vs_yfinance.py to compare mart vs live yfinance, no Python recompute) — deferred to a separate task.

done_when:
  - metric_catalogue.csv holds the 5 metrics with: metric_id, entity, label, description, base_relation, numerator_expr, denominator_expr, lower_is_better, format, metric_group, importance_tier, group_display_order, direction, interpretation, plus stock columns mart_column / median_column / benchmarkable / basis_column. Values ported, not invented.
  - Seed declared in _seeds.yml with not-null + unique(metric_id, entity) tests.
  - Drift guard in tests/test_metric_catalogue.py (CI pytest): every catalogue metric is computed in int_stock__card_metrics; the regenerated frontend/metrics.json byte-matches the committed file; catalogue values are well-formed. (Football's jinja dbt singular test is incompatible with this repo's §1.1 WITH-first gate — see docs/metric_layer.md.)
  - export_metric_definitions_json.py builds frontend/metrics.json from the seed.
  - card_copy.py sources label/format/direction/tier/gloss/analogy/learn from metrics.json; hardcoded METRIC_* dicts removed; public functions (metric_label, metric_gloss, format_metric_value, BENCHMARK_METRICS, ALL_METRICS, tiers, …) keep their signatures so app.py / card_ui.py / markets.py / metric_school.py / overflow_menu.py are unaffected.
  - data_contract.md references the seed instead of restating the metric tables; docs/metric_layer.md added (adapted from football).
  - dbt build + dbt tests + pytest green; the preview harness renders the card identically (no unintended visual change); review cycle recorded; PR opened to main (not merged).

impact_map: No dbt model output changes — int_stock__card_metrics / mart_stock_cards / the Supabase export are untouched, so no data or runtime change. The card displays identical strings/values; only their SOURCE moves from hardcoded dicts to the seed→metrics.json. New CI surface: seed + two dbt tests + one pytest. `dbt seed` now loads metric_catalogue (cheap, ~5 rows).

amendments:
  - 2026-06-29 — initial contract; Phase 1 of the metric layer, adapted from football-data-pipeline's metric_catalogue pattern (docs/metric_layer.md there). Owner approved building the layer before the UI mock.
  - 2026-06-29 — as-built refinements: (1) the model->catalogue drift guard is a Python test (tests/test_metric_catalogue.py), not a dbt singular test — the repo's §1.1 SQL-structure gate requires WITH-first singular tests, which football's jinja column-introspection style fails. (2) The ebit_margin "(TTM)" dynamic-suffix cleanup is deferred to the UI work to keep Phase 1 zero-text-change. (3) Strict model->catalogue introspection + expr-resolvability deferred to Phase 2.
