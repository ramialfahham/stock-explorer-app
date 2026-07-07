# Task contract

objective: **Slice 2b — complete the three financial statements (DATA-ONLY).** Add the cash-flow
  (`Operating Cash Flow`, `Capital Expenditure`) and income (`Interest Expense`, `Net Income`) lines the
  per-type metric matrix needs, plus the dividend `info` fields (`dividendYield`, `payoutRatio`), as
  data-only raw fields — so a later slice computes correct per-type metrics from statements (a computed
  FCF = OCF + Capex; interest coverage; statement-based ROE / net margin; dividend yield). The lighter
  companion to #140: income + cash-flow statements are already fetched, labels are canonical (camel2title
  of a fixed key set), so **no new module / probe / fallback tuples.** No compute, no display, no
  eligibility change. Approved plan: ~/.claude/plans/noble-forging-beaver.md.

scope_paths:
  - ingestion/yfinance/ingest.py
  - dbt_analytics/models/1_staging/yfinance/stg_yf__fundamentals.sql
  - dbt_analytics/models/1_staging/yfinance/_yfinance_staging.yml
  - dbt_analytics/models/2_base/yfinance/_yfinance_base.yml
  - dbt_analytics/models/3_core/fct_fundamentals_snapshot.sql
  - dbt_analytics/models/3_core/_core.yml
  - dbt_analytics/models/sources.yml
  - scripts/audit_mart_vs_yfinance.py
  - scripts/seed_ci_raw_fixtures.py
  - docs/data_contract.md
  - .claude/task/contract.md

review_artifacts (NOT in the reviewed diff — separate artifact-only commit after; review.md records the
  reviewed diff's hash):
  - .claude/task/review.md
  - .claude/active_work.md

decisions_reserved:
  - **"Do it right" (owner):** compute from period-matched statements, not `info` scalars — Slice 2b lands
    the statement inputs. Sign conventions are documented **factually** (`Capital Expenditure` is NEGATIVE
    = outflow → computed FCF = OCF + Capex; `Interest Expense` is POSITIVE magnitude); the metrics that use
    them are Slice 3.
  - DEFERRED to **Slice 3:** computing the metrics (FCF = OCF + Capex; `interest_coverage`; statement ROE /
    net margin; `cash_runway` from OCF burn; `dividend_yield`). DEFERRED to **Slice 4:** per-type metric
    sets + display + copy.
  - No interpretive/beginner copy — `data_contract.md` stays factual (the #135 §6 lesson).

technical_definition (factual; no beginner copy):
  - 6 raw fields, annual, nullable, not clipped:
    - `stmt_operating_cash_flow` ← cashflow `Operating Cash Flow`
    - `stmt_capital_expenditure` ← cashflow `Capital Expenditure` (NEGATIVE = cash outflow)
    - `stmt_interest_expense` ← income `Interest Expense` (POSITIVE magnitude)
    - `stmt_net_income` ← income `Net Income`
    - `info_dividend_yield` ← `dividendYield`; `info_payout_ratio` ← `payoutRatio`
  - `ingest.py`: 4 inline `_latest_annual_statement_value(...)` calls on the already-fetched
    income/cashflow frames + 2 `INFO_FIELDS` entries. Canonical yfinance labels — no fallback tuples, no
    new module.
  - Propagate staging cast → base (`select *`) → core select; `sources.yml` + `FUNDAMENTALS_COLUMNS`
    mirrors updated in lockstep. NOT in `is_card_eligible`/`missing_metrics`, NOT selected by
    `mart_stock_cards` (data-only).

done_when:
  - `ingest.py`: 4 extractions + 2 `INFO_FIELDS`.
  - 6 staging casts + docs; base docs; 6 core selects + docs; `sources.yml` (6); `FUNDAMENTALS_COLUMNS`
    (6); CI fixtures (6); `data_contract.md` (info + "From financial statements" rows + a factual
    sign-convention note; state computed FCF = OCF + Capex is a distinct FCF source from the existing
    `stmt_free_cash_flow` row).
  - Verify green: regenerate fixtures + dbt build; doc/layer/structure/sqlfluff; check_eligibility_baseline
    (**stays 25**) + check_export_health (**stays 100%**); pytest (unchanged count). Live sanity: landed
    values match the probe for a couple of tickers.
  - After the reviewed commit (artifact-only): record review.md, advance active_work.md; PR to main (NOT merged).

impact_map:
  - 6 raw columns flow ingestion → staging (cast) → base (`select *`) → core (passthrough). The two
    raw-schema mirrors (`sources.yml`, `scripts/audit_mart_vs_yfinance.py` `FUNDAMENTALS_COLUMNS`) are
    updated in lockstep (the `.reindex` would otherwise silently drop them). Absent from eligibility and
    `mart_stock_cards` → export shape/health and the eligibility baseline are unchanged. **No new statement
    fetch** (income/cashflow already fetched) → no new cadence/fan-out/cost. frontend untouched.
  - Required reviewers (per `.claude/review_routing.json`): scope-auditor + analytics-engineer
    (`*.sql`/`dbt_analytics/*.yml`) + data-engineer (`ingestion/*`) + cto (`scripts/*`) + equity-analyst
    (`docs/data_contract.md`).

amendments:
  - 2026-07-07 — supersedes the merged balance-sheet contract (#140). Scope = statement completion
    (Slice 2b) per approved plan noble-forging-beaver.md; data-only, canonical labels, no new module.
