# Task contract

objective: Add FOUR new metrics as DATA-ONLY (handover step 1, continuing after ROE/#135): the clean
  single-field Yahoo `info` passthroughs — **current ratio, P/B, P/S, EV/EBITDA**. Land the raw fields
  through ingestion → staging → base → core and surface each as a passthrough metric in
  `int_stock__card_metrics` (no `* 100`; they are ratios already). Exactly the proven ROE/#135 pattern.
  **No display surface:** no catalogue row, no metrics.json, no card_copy/UI, no Supabase export, and
  **no change to eligibility** (`is_card_eligible` / `missing_metrics` stay the existing five). These land
  as inert data for the Sector Router (handover step 2) to catalogue, gate, and display per company type.
  Field names verified live on AAPL: currentRatio, priceToBook, priceToSalesTrailing12Months,
  enterpriseToEbitda (all present floats). Approved plan: ~/.claude/plans/linear-yawning-honey.md.

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

review_artifacts (NOT in the reviewed diff — separate artifact-only/gate-exempt commit after the reviewed
  commit, per the dbt-agent-kit two-commit pattern; review.md records the reviewed diff's hash):
  - .claude/task/review.md
  - .claude/active_work.md

decisions_reserved:
  - "Add the new sector-aware metrics" and this metric set are owner-locked (active_work.md). The technical
    field mappings + passthrough computes implement that locked decision (no new §6 call).
  - DEFERRED to the Sector Router / later PRs (NOT decided here): each metric's catalogue row, metrics.json
    entry, display tier/order, per-sector eligibility, and beginner-facing interpretation/applicability
    copy. **No interpretive wording is authored in this PR** (the #135 lesson: authoring metric copy is §6).
  - Also deferred: FCF yield (compute, needs marketCap), cash runway (compute, Router-entangled),
    debt-to-equity + interest coverage (the brittle-net-debt/EBITDA fix).

technical_definition (factual; no beginner copy):
  - current_ratio  = info_current_ratio  (Yahoo currentRatio)                    — passthrough
  - price_to_book  = info_price_to_book  (Yahoo priceToBook)                     — passthrough
  - price_to_sales = info_price_to_sales (Yahoo priceToSalesTrailing12Months)    — passthrough
  - ev_to_ebitda   = info_ev_to_ebitda   (Yahoo enterpriseToEbitda)              — passthrough
  - All ratios already (no ×100); int compute is `s.info_<x> as <metric>`. Nullable; not clipped. NOT in
    is_card_eligible / missing_metrics.

done_when:
  - ingestion: 4 `INFO_FIELDS` entries (info_current_ratio/price_to_book/price_to_sales/ev_to_ebitda).
  - dbt: 4 staging casts; 4 core select columns; 4 passthrough metrics in int_stock__card_metrics' metrics
    CTE; eligibility/missing_metrics CTEs UNCHANGED (still the five).
  - docs (doc gate): the 4 new raw columns documented in _yfinance_staging.yml, _yfinance_base.yml,
    _core.yml; the 4 new metric columns documented in _intermediate.yml.
  - test: T1 unit test extended — 4 `info_*` in `given` → 4 metric values in `expect` (current_ratio 1.5,
    price_to_book 8.0, price_to_sales 5.0, ev_to_ebitda 15.0).
  - CI fixtures: seed_ci_raw_fixtures.py emits the 4 fields (else CI dbt build fails on the new staging
    casts; storage/raw is gitignored, regenerated each run).
  - data_contract.md: 4 ticker.info mapping rows + the 4 metrics listed in the data-only note (factual, no
    caveat).
  - Verify green: dbt parse; regenerate fixtures + dbt build; dbt docs generate + check_dbt_documentation;
    check_layer_contract; check_dbt_sql_structure; sqlfluff; check_eligibility_baseline (stays 25) +
    check_export_health (stays 100%); pytest tests/ (73). Card byte-identical (catalogue/metrics.json untouched).
  - After the reviewed commit (artifact-only commits): record review.md, advance active_work.md; PR to main
    (NOT merged).

impact_map:
  - 4 new raw columns flow ingestion → staging → base(`select *`) → core → int (4 passthrough metrics).
    mart_stock_cards does NOT select them, so the Supabase export shape, export-health, and eligibility
    baseline are unchanged.
  - frontend untouched: card_copy reads metrics.json (unchanged) → ALL_METRICS unchanged → card
    byte-identical; no "—" cells (catalogue not touched).
  - storage/raw is gitignored (no committed parquet). CI regenerates fixtures from seed_ci_raw_fixtures.py.
  - Required reviewers (routing): scope-auditor + analytics-engineer (sql/yml) + data-engineer (ingestion)
    + cto (scripts) + equity-analyst (docs/data_contract.md).

amendments:
  - 2026-06-30 — supersedes the merged ROE contract (#135). Scope = the 4 passthrough metrics, per the
    approved plan (linear-yawning-honey.md) and run through the plan-mode Explore→Plan→Execute spine.
