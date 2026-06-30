# Task contract

objective: Add **Return on Equity as DATA ONLY** (handover step 3, first vertical slice). Land the raw
  Yahoo `returnOnEquity` field through ingestion → staging → base → core, and compute `roe_pct`
  (= returnOnEquity × 100) once in `int_stock__card_metrics`. **No display surface:** no catalogue row,
  no metrics.json, no card_copy/card_ui, no Supabase mart/export, and **no change to eligibility**
  (`is_card_eligible` / `missing_metrics` stay the existing five). ROE data becomes available in the dbt
  model, ready for the Sector Router step to catalogue, route, gate, and display per company type.
  Owner chose this depth (over full-vertical / display-gate) because cataloguing currently renders a
  metric, and per-sector display/eligibility is the Router's job.

scope_paths:
  - ingestion/yfinance/ingest.py
  - dbt_analytics/models/1_staging/yfinance/stg_yf__fundamentals.sql
  - dbt_analytics/models/1_staging/yfinance/_yfinance_staging.yml
  - dbt_analytics/models/2_base/yfinance/_yfinance_base.yml
  - dbt_analytics/models/3_core/fct_fundamentals_snapshot.sql
  - dbt_analytics/models/3_core/_core.yml
  - dbt_analytics/models/4_intermediate/int_stock__card_metrics.sql
  - dbt_analytics/models/4_intermediate/_intermediate.yml
  - scripts/seed_ci_raw_fixtures.py
  - docs/data_contract.md
  - .claude/task/contract.md

review_artifacts (NOT in the reviewed diff — separate artifact-only/gate-exempt commits after the
  reviewed commit, per the dbt-agent-kit two-commit pattern; review.md records the reviewed diff's hash):
  - .claude/task/review.md
  - .claude/active_work.md

decisions_reserved:
  - "Use ROE (not ROIC)" and the `returns` perspective are owner-locked in active_work.md this arc, so
    the technical definition below implements a locked decision (not a new §6 call).
  - DEFERRED to the Sector Router / UI step (NOT decided here): ROE's beginner copy
    (label/gloss/analogy/learn), its catalogue row + metrics.json entry, display tier/order, whether and
    how it gates eligibility per sector, and Supabase export. This slice deliberately stops before any of
    that. If the owner wants ROE on the card sooner, that is the "full vertical" option — escalate.

technical_definition (implements the locked "add ROE"; factual, no beginner copy):
  - raw field: info_return_on_equity  <-  Yahoo info `returnOnEquity` (a decimal, e.g. 0.18 = 18%).
  - computed metric: `roe_pct` = `info_return_on_equity * 100.0` in int_stock__card_metrics
    (mirrors revenue_growth_yoy_pct's decimal→percent). Nullable (null when Yahoo omits it); may be
    negative (loss-makers) — no clipping. NOT added to is_card_eligible / missing_metrics.
  - name `roe_pct` chosen for consistency with ebit_margin_pct / revenue_growth_yoy_pct / fcf_margin_pct.

done_when:
  - ingestion: `INFO_FIELDS` in ingestion/yfinance/ingest.py gains `"info_return_on_equity": "returnOnEquity"`.
  - staging: stg_yf__fundamentals.sql adds `cast(s.info_return_on_equity as double) as info_return_on_equity`.
  - core: fct_fundamentals_snapshot.sql adds `info_return_on_equity` to its explicit select.
  - intermediate: int_stock__card_metrics.sql computes `s.info_return_on_equity * 100.0 as roe_pct`
    in the metrics CTE; eligibility/missing_metrics CTEs UNCHANGED (still the five).
  - docs: every new model output column documented (doc gate requires it) — `info_return_on_equity` in
    _yfinance_staging.yml, _yfinance_base.yml, _core.yml; `roe_pct` in _intermediate.yml.
  - test: extend ONE unit test in _intermediate.yml — add `info_return_on_equity` to its `given`
    fct_fundamentals_snapshot row and `roe_pct` to its `expect` (verifies the ×100 compute). Other unit
    tests unaffected (dbt null-fills omitted input columns).
  - CI fixtures: seed_ci_raw_fixtures.py emits `info_return_on_equity` (else CI `dbt build` fails on the
    new staging cast). storage/raw is gitignored — CI regenerates fixtures from this script each run, so
    there is no committed parquet to update; verified locally by regenerating + `dbt build`.
  - data_contract.md: add the raw field to the `ticker.info` mapping table and note the computed
    `roe_pct` as DATA-ONLY (not on the card, not in eligibility, not exported yet).
  - Verify green: `dbt parse`; regenerate fixtures; `dbt build`; `dbt docs generate` +
    check_dbt_documentation.py; check_layer_contract.py; check_dbt_sql_structure.py; sqlfluff lint;
    check_eligibility_baseline.py + check_export_health.py (must be UNCHANGED — ROE not in eligibility/mart);
    `pytest tests/`. Rendered card byte-identical (card_copy/metrics.json untouched).
  - After the reviewed commit (artifact-only commits): record review.md and advance active_work.md;
    open PR to main (NOT merged).

impact_map:
  - New raw column flows ingestion → staging → base(`select *`) → core → int. mart_stock_cards does NOT
    select roe_pct, so the Supabase export shape, export-health, and eligibility baseline are unchanged.
  - frontend untouched: card_copy reads metrics.json (unchanged) → ALL_METRICS unchanged → card
    byte-identical; no "—" ROE cell (catalogue not touched).
  - storage/raw is gitignored (no committed parquet). CI regenerates fixtures from seed_ci_raw_fixtures.py
    each run; updating that generator is what carries info_return_on_equity into CI's dbt build.
  - Required reviewers (routing): scope-auditor + analytics-engineer (sql/yml) + data-engineer-reviewer
    (ingestion) + cto-reviewer (scripts) + equity-analyst (docs/data_contract.md).

amendments:
  - 2026-06-30 — supersedes the merged catalogue-enrichment contract (PR #134). Scope set by two owner
    choices this session: "vertical slice, ROE first", then "data-only (defer display)" after I surfaced
    that cataloguing a metric currently renders it (no Supabase value / redesigned UI yet).
