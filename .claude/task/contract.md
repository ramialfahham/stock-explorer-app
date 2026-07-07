# Task contract

objective: **Slice 3b — compute the per-type metrics from the statements (DATA-ONLY).** Turn the landed
  statement lines (#140/#141/#142) into 13 computed columns in `int_stock__card_metrics` — the correct
  per-type metrics the Sector/Lifecycle Router will display. Data-only: computed in the intermediate
  `metrics` CTE like the existing `roe_pct`/ratios; NOT in `is_card_eligible`, `mart_stock_cards`, the metric
  catalogue, or the export. Coexist with the existing info-scalar versions (`current_ratio`, `roe_pct`,
  `fcf_*`); Slice 4 owns per-type gating/display. Approved plan: ~/.claude/plans/logical-roaming-brook.md.

scope_paths:
  - dbt_analytics/models/4_intermediate/int_stock__card_metrics.sql
  - dbt_analytics/models/4_intermediate/_intermediate.yml
  - dbt_analytics/models/sources.yml
  - dbt_analytics/models/3_core/_core.yml
  - dbt_analytics/models/2_base/yfinance/_yfinance_base.yml
  - dbt_analytics/models/1_staging/yfinance/_yfinance_staging.yml
  - docs/data_contract.md
  - .claude/task/contract.md

review_artifacts (NOT in the reviewed diff — separate artifact-only commit after; review.md records the
  reviewed diff's hash):
  - .claude/task/review.md
  - .claude/active_work.md

decisions_reserved:
  - Owner metric definitions locked (this session): statement ROE = common income ÷ common equity; ROA =
    total net income ÷ total assets; cash_runway = cash ÷ FCF-burn in months; coexist (don't replace) the
    info-scalar versions.
  - **Discovered + corrected here:** yfinance 1.3.0 returns `dividendYield` **already in percent** (verified
    live: MSFT 0.94 = 0.94%, JPM 1.78, KO 2.56, O 5.15), NOT a fraction — so `dividend_yield_pct =
    info_dividend_yield` (no ×100), and the stale "(decimal)" descriptions on `info_dividend_yield` are
    corrected to "(percent)". `payoutRatio` IS a fraction (verified: MSFT 0.21) — left as-is. The existing
    `roe_pct = info_return_on_equity * 100` stays correct (returnOnEquity is a fraction: JPM 0.165).
  - DEFERRED to **Slice 4:** per-type metric SETS (the matrix), eligibility rework, `mart_stock_cards` carry,
    per-type display/copy, catalogue rows. The ROA/ROE numerator asymmetry (total vs common) and
    period-end-vs-Yahoo-averaged denominators are documented; final catalogue copy is §6.
  - No interpretive/beginner copy — `data_contract.md` + yml stay factual.

technical_definition (factual; no beginner copy):
  - `int_stock__card_metrics.sql`: `computed_fcf` (= OCF + Capex, capex negative) added in the `resolved`
    CTE; 13 computed columns added in the `metrics` CTE using the existing
    `CASE WHEN <inputs not null> AND <denom> != 0 THEN … END` guard idiom:
    - solvency (operating): `debt_to_equity`, `interest_coverage` (= eff_stmt_op / abs(interest))
    - liquidity (operating): `current_ratio_stmt`, `working_capital`
    - valuation (financial): `price_to_tangible_book` (= market_cap / tangible_book, guard tbv > 0)
    - profitability: `net_margin_pct`
    - returns: `roa_pct` (NI / total_assets), `statement_roe_pct` (NI_common / equity), `dividend_yield_pct`
      (= info_dividend_yield, already percent)
    - cash: `computed_fcf`; `cash_runway_months` + `burn_rate_monthly` (only when computed_fcf < 0)
    - valuation (pre-rev): `net_cash_to_ev` (= (cash − debt) / EV, EV = market_cap + debt − cash)
  - `_intermediate.yml`: 13 column docs + 4 unit tests (computed values incl. distinct ROA/ROE numerators;
    interest-coverage abs() sign; runway/burn only when burning; null on zero/negative denominator).
  - `data_contract.md`: 13 data-only metric formulas (factual) + the dividendYield percent correction. The 4
    raw-field yml `dividendYield` "(decimal)" descriptions corrected to "(percent)" in lockstep.
  - NOT added to `is_card_eligible`/`missing_metrics`; the `metrics` CTE explicit projection is the boundary
    the new columns terminate at (they do NOT reach `mart_stock_cards`/`int_stock__sector_benchmarks`).

done_when:
  - 13 computed columns + computed_fcf; 13 yml docs; 4 unit tests; 13 data_contract formulas; dividendYield
    percent correction (data_contract + 4 raw-field ymls).
  - Verify green: dbt build (**PASS incl. 15 unit tests**) + doc/layer/structure/sqlfluff + eligibility-
    baseline (**stays 25**) + export-health (**stays 100%**) + pytest (unchanged). Values spot-checked.
  - After the reviewed commit (artifact-only): record review.md, advance active_work.md; PR to main (NOT merged).

impact_map:
  - 13 additive computed columns on `int_stock__card_metrics` (existing grain). They pass through the
    `eligibility` `select *` but are excluded from `missing_metrics`/`is_card_eligible` and from
    `mart_stock_cards`'s explicit select → export shape/health + eligibility baseline unchanged. No raw
    fields, no ingestion, no new fetch/cost. `int_stock__sector_benchmarks` untouched.
  - dividendYield percent correction touches only descriptions (data_contract + 4 yml) — no data/logic change
    to `info_dividend_yield` itself.
  - Required reviewers (per `.claude/review_routing.json`): scope-auditor + analytics-engineer
    (`*.sql`/`dbt_analytics/*.yml`) + equity-analyst (`docs/data_contract.md`; also scrutinises the SQL
    formulas). No ingestion/scripts/tests changes → no data-engineer / cto.

amendments:
  - 2026-07-07 — supersedes the merged statement-enrichment contract (#142). Scope = per-type metric compute
    (Slice 3b): 13 data-only computed columns + the dividendYield percent-scale correction.
