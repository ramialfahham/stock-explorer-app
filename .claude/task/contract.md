# Task contract

objective: **Slice 3a — statement enrichment for correct ROE + ROA (DATA-ONLY).** Add two raw statement
  lines the corrected per-type returns metrics need: `stmt_total_assets` (balance sheet `Total Assets` →
  ROA = net income / total assets, a leverage-neutral returns metric for financials) and
  `stmt_net_income_common` (income `Net Income Common Stockholders` → a correctly-attributed statement
  ROE = common income / common equity, resolving the #141 attribution mismatch). Data-only raw fields —
  no compute, no display, no eligibility change (the metrics are Slice 3b). Approved plan:
  ~/.claude/plans/logical-roaming-brook.md.

scope_paths:
  - ingestion/yfinance/balance_sheet.py
  - ingestion/yfinance/ingest.py
  - dbt_analytics/models/1_staging/yfinance/stg_yf__fundamentals.sql
  - dbt_analytics/models/1_staging/yfinance/_yfinance_staging.yml
  - dbt_analytics/models/2_base/yfinance/_yfinance_base.yml
  - dbt_analytics/models/3_core/fct_fundamentals_snapshot.sql
  - dbt_analytics/models/3_core/_core.yml
  - dbt_analytics/models/sources.yml
  - scripts/audit_mart_vs_yfinance.py
  - scripts/seed_ci_raw_fixtures.py
  - scripts/probe_roa_total_assets.py
  - tests/test_balance_sheet.py
  - docs/data_contract.md
  - docs/intl-balance-sheet-row-labels.md
  - .claude/task/contract.md

review_artifacts (NOT in the reviewed diff — separate artifact-only commit after; review.md records the
  reviewed diff's hash):
  - .claude/task/review.md
  - .claude/active_work.md

decisions_reserved:
  - **Owner decisions locked this session (metric review + external stress-test):** (1) statement ROE
    computed correctly by ingesting `Net Income Common Stockholders` — the methodically-right fix, not a
    documented approximation; (2) ROA adopted into the financial column (the one sourceable, bank-relevant
    metric from the external review), computed from statements (`net income / total assets`) — the yfinance
    `returnOnAssets` scalar is a probe cross-check only, not the source; (3) cash runway = cash / FCF-burn,
    in months (Slice 3b).
  - DEFERRED to **Slice 3b:** computing all metrics (debt-to-equity, interest coverage, current ratio,
    working capital, P/TBV, net margin, ROA, statement ROE, dividend yield, computed FCF, cash runway, burn,
    net-cash-to-EV). DEFERRED to **Slice 4:** per-type metric sets + eligibility rework + display + copy.
  - No interpretive/beginner copy — `data_contract.md` stays factual (the #135 §6 lesson).
  - The exact ROE numerator/denominator pairing (common-income ÷ common-equity vs parent ÷ parent, given
    preferred stock) is finalized with the equity-analyst in Slice 3b — this slice only LANDS the raw line.

technical_definition (factual; no beginner copy):
  - 2 raw fields, annual, nullable, not clipped:
    - `stmt_total_assets` ← balance_sheet `Total Assets` (added to `BALANCE_SHEET_FIELDS`; single canonical
      label — 100% probe coverage incl. non-US `HSBA.L`)
    - `stmt_net_income_common` ← income `Net Income Common Stockholders` (inline extraction; net income
      attributable to common after minority interest + preferred dividends)
  - `balance_sheet.py`: 1 fallback tuple + 1 `BALANCE_SHEET_FIELDS` entry. `ingest.py`: 1 row-label constant
    + 1 inline `_latest_annual_statement_value(...)` on the already-fetched income frame. Canonical yfinance
    labels — no fallback tuples beyond the single label.
  - Propagate staging cast → base (`select *`) → core select; `sources.yml` + `FUNDAMENTALS_COLUMNS` mirrors
    updated in lockstep. NOT in `is_card_eligible`/`missing_metrics`, NOT selected by `mart_stock_cards`.
  - `scripts/probe_roa_total_assets.py`: read-only diagnostic (JPM/BAC/HSBA.L + operating control) — confirms
    label coverage, the ROE attribution gap (2.4–5.3% banks, 0% control), and computed-vs-scalar
    reconciliation. No pipeline effect.

done_when:
  - `balance_sheet.py`: +`stmt_total_assets`. `ingest.py`: +`stmt_net_income_common` (constant + extraction).
  - 2 staging casts + docs; base docs; 2 core selects + docs; `sources.yml` (2); `FUNDAMENTALS_COLUMNS` (2);
    CI fixtures (2); `data_contract.md` (income + balance rows, factual); `intl-balance-sheet-row-labels.md`
    (`Total Assets` fallback row); `test_balance_sheet.py` (field-set + value assertions).
  - Verify green: regenerate fixtures + dbt build; doc/layer/structure/sqlfluff; check_eligibility_baseline
    (**stays 25**) + check_export_health (**stays 100%**); pytest (all pass). Live sanity: probe landed values
    match yfinance for JPM/BAC/HSBA.L/MSFT.
  - After the reviewed commit (artifact-only): record review.md, advance active_work.md; PR to main (NOT merged).

impact_map:
  - 2 raw columns flow ingestion → staging (cast) → base (`select *`) → core (passthrough). The two raw-schema
    mirrors (`sources.yml`, `scripts/audit_mart_vs_yfinance.py` `FUNDAMENTALS_COLUMNS`) updated in lockstep
    (the `.reindex` would otherwise silently drop them). Absent from eligibility and `mart_stock_cards` →
    export shape/health and the eligibility baseline unchanged. **No new statement fetch** (balance sheet +
    income already fetched) → no new cadence/fan-out/cost. frontend untouched.
  - Required reviewers (per `.claude/review_routing.json`): scope-auditor + analytics-engineer
    (`*.sql`/`dbt_analytics/*.yml`) + data-engineer (`ingestion/*`) + cto (`scripts/*`, `tests/*`) +
    equity-analyst (`docs/data_contract.md`).

amendments:
  - 2026-07-07 — supersedes the merged statement-completion contract (#141). Scope = statement enrichment
    (Slice 3a): 2 raw fields for correct ROE + ROA per approved plan logical-roaming-brook.md; data-only.
