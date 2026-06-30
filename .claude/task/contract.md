# Task contract

objective: Add **FCF yield as DATA-ONLY** (handover step 1, after ROE/#135 and the four ratios/#136).
  FCF yield = free cash flow ÷ market value × 100 (a cash-return-on-price). **Owner decision on the
  numerator:** Yahoo's trailing `freeCashflow` over Yahoo's current `marketCap`, so cash and price are the
  same period (the latest annual-statement FCF over today's market cap would be a stale mismatch for a
  yield). Land the two raw fields through ingestion → staging → base → core and compute `fcf_yield_pct` in
  `int_stock__card_metrics` with a guarded division (same shape as `net_debt_to_ebitda`). **No display
  surface:** no catalogue row, metrics.json, card_copy/UI, Supabase export, or eligibility change. Approved
  plan: ~/.claude/plans/linear-yawning-honey.md. Keys verified live (AAPL has both; banks→null FCF→null yield).

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
  commit; review.md records the reviewed diff's hash):
  - .claude/task/review.md
  - .claude/active_work.md

decisions_reserved:
  - The metric "FCF yield" is owner-locked (active_work.md); the FCF-source choice (Yahoo trailing
    freeCashflow vs annual stmt FCF) was an open §6/definition fork — **owner chose Yahoo trailing
    freeCashflow** this session.
  - DEFERRED to the Sector Router (NOT decided here): fcf_yield_pct's catalogue row, metrics.json entry,
    display, per-sector eligibility, and beginner-facing applicability copy. No interpretive copy authored
    in this PR (data_contract stays factual — the #135 §6 lesson).
  - Also deferred: cash runway (Router); debt-to-equity + interest coverage (brittle-metric fix).

technical_definition (factual; no beginner copy):
  - raw: info_free_cashflow ← Yahoo freeCashflow (trailing); info_market_cap ← Yahoo marketCap (current).
  - compute: `case when info_market_cap is not null and info_market_cap != 0 then info_free_cashflow /
    info_market_cap * 100.0 end as fcf_yield_pct`. Nullable (null for financials/missing); not clipped.
    NOT in is_card_eligible / missing_metrics.
  - Introduces a second FCF figure (distinct from stmt_free_cash_flow used by fcf_margin_pct); documented
    factually in data_contract.md (margin = annual statement; yield = trailing FCF vs current market cap).

done_when:
  - ingestion: 2 INFO_FIELDS entries (info_free_cashflow, info_market_cap).
  - dbt: 2 staging casts; 2 core select columns; the guarded fcf_yield_pct compute in int_stock__card_metrics;
    eligibility/missing_metrics CTEs UNCHANGED (still the five).
  - docs (doc gate): the 2 new raw columns documented in _yfinance_staging.yml/_yfinance_base.yml/_core.yml;
    fcf_yield_pct documented in _intermediate.yml.
  - test: T1 unit test extended — info_free_cashflow 50.0 + info_market_cap 1000.0 in `given` →
    fcf_yield_pct 5.0 in `expect` (exercises the division ×100 + guard).
  - CI fixtures: seed_ci_raw_fixtures.py emits the 2 fields (free_cashflow 5e9, market_cap 1e11 → 5.0).
  - data_contract.md: 2 ticker.info rows + fcf_yield_pct in the data-only note, with the factual
    trailing-vs-annual-FCF rationale.
  - Verify green: dbt parse; regenerate fixtures + dbt build; dbt docs generate + check_dbt_documentation;
    check_layer_contract; check_dbt_sql_structure; sqlfluff; check_eligibility_baseline (stays 25) +
    check_export_health (stays 100%); pytest tests/ (73); duckdb spot-check fcf_yield_pct computes (null
    where freeCashflow null). Card byte-identical.
  - After the reviewed commit (artifact-only): record review.md, advance active_work.md; PR to main (NOT merged).

impact_map:
  - 2 new raw columns flow ingestion → staging → base(`select *`) → core → int (1 guarded compute).
    mart_stock_cards does NOT select fcf_yield_pct, so export shape, export-health, and eligibility baseline
    are unchanged. frontend untouched (card byte-identical). storage/raw gitignored (CI regenerates fixtures).
  - Required reviewers: scope-auditor + analytics-engineer (sql/yml) + data-engineer (ingestion) + cto
    (scripts) + equity-analyst (docs/data_contract.md — checks the FCF-source choice + factual note).

amendments:
  - 2026-06-30 — supersedes the merged ratio-metrics contract (#136). Scope = FCF yield data-only, per the
    approved plan and the owner's trailing-freeCashflow numerator choice; run through the plan-mode spine.
