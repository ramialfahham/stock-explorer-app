# Task contract

objective: **Sector/Lifecycle Router — Slice 4b: the financial / bank card.** 4a (merged #145) built the
  per-type render mechanism + grew the operating card but left eligibility untouched, so banks (which lack
  `net_debt_to_ebitda`) never appear. 4b delivers the bank card: catalogue 4 bank metrics (`price_to_tangible_book`,
  `net_margin_pct`, `roa_pct`, `dividend_yield_pct`), narrow the operating-only metrics off banks, and **rework
  eligibility into a per-type `CASE company_type`** — the first slice to change the eligible pool. Bank card = the
  7 (P/TBV, P/E, net margin, revenue growth, ROE, ROA, dividend yield); solvency/liquidity/cash honestly blank
  (the render rule omits them). A synthetic bank fixture makes it locally verifiable.
  Approved plan: ~/.claude/plans/dynamic-snuggling-truffle.md.

scope_paths:
  - dbt_analytics/models/4_intermediate/int_stock__card_metrics.sql   # per-type eligibility + missing_metrics CASE
  - dbt_analytics/models/4_intermediate/_intermediate.yml             # int per-type eligibility test + financial/scale unit tests + stale LLOY/HSBA fixes
  - dbt_analytics/tests/assert_eligible_mart_rows_have_all_metrics.sql # per-type required-metric assertion (was hardcoded 5)
  - dbt_analytics/models/5_marts/mart_stock_cards.sql                 # + 4 financial metric values in SELECT
  - dbt_analytics/models/5_marts/_marts.yml                           # per-type eligibility test; doc 4 columns
  - dbt_analytics/seeds/metric_catalogue.csv                          # +4 financial rows; narrow applies_to
  - scripts/export_metric_definitions_json.py                         # (no change expected; regenerate output)
  - frontend/card_copy.py                                             # metrics_for_card lens-sort (per-card lens grouping; operating parity)
  - frontend/metrics.json                                             # regenerated from the seed
  - scripts/export_to_supabase.py                                     # EXPORT_COLUMNS += 4 financial metrics
  - supabase/migrations/008_financial_card_metrics.sql               # new: add the 4 numeric columns
  - docs/data_contract.md                                            # export table += 4 metrics (factual)
  - scripts/seed_ci_raw_fixtures.py                                  # add a Financial Services bank row per market
  - scripts/eligibility_baseline.ci.json                             # 25 -> 30 (recalibrated)
  - tests/tooling/test_metric_catalogue.py                           # (auto-covers the 4 new rows)
  - tests/frontend/test_card_copy.py                                 # metrics_for_card(financial) = the 7
  - tests/frontend/test_card_ui.py                                   # financial build_card_html render
  - tests/ingestion/                                                 # dividend-scale passthrough guard (if placed here)
  - .claude/task/contract.md

review_artifacts (separate artifact-only commit after; review.md records the reviewed diff's hash):
  - .claude/task/review.md
  - .claude/active_work.md

decisions_reserved (owner-approved this session; §6):
  - **Bank card = the 7:** valuation (P/TBV, forward_pe), profitability (net_margin_pct), growth
    (revenue_growth_yoy_pct), returns (statement_roe_pct, roa_pct, dividend_yield_pct). Solvency/liquidity/cash omitted.
  - **Bank eligibility = core three:** forward_pe + statement_roe_pct + net_margin_pct required; the other four
    render when present.
  - **Add a synthetic bank fixture** for local verifiability (recalibrate the CI fixture baseline 25 -> 30).
  - **Beginner copy** for the 4 new metrics is owner-signed (plan-approved); ROA copy surfaces the ROA/ROE
    numerator asymmetry (carry-in b) + period-end basis. `data_contract.md` stays strictly factual.

technical_definition:
  - **Per-type eligibility:** `int_stock__card_metrics.sql` `eligibility` CTE -> `CASE company_type`:
    `financial` = `forward_pe is not null AND statement_roe_pct is not null AND net_margin_pct is not null`;
    else (operating + pre_revenue) = today's five-metric AND (unchanged). `missing_metrics` becomes a matching
    per-type `CASE`. The **five eligibility-assumption sites** are all updated to the per-type expression: the
    `_marts.yml` and `_intermediate.yml` `expression_is_true` tests, the singular
    `assert_eligible_mart_rows_have_all_metrics.sql`, and two pre-existing bank unit tests (LLOY, HSBA) whose
    `is_card_eligible: true` (valid under the old 5-AND) became `false` under the financial core-three. The
    `assert_mart_row_count_matches_card_metrics.sql` is symmetric (`is_card_eligible` both sides) — no change.
  - **Catalogue:** +4 rows `applies_to = financial`, `benchmarkable = false` (already computed in the model, #143).
    Narrow: `statement_roe_pct` `operating` -> `operating|financial`; drop `financial` from `ebit_margin_pct` /
    `net_debt_to_ebitda` / `fcf_margin_pct` (-> `operating|pre_revenue`). `forward_pe` / `revenue_growth_yoy_pct`
    keep `financial`. Bank card renders exactly the 7.
  - **Mart carry:** the 4 new metric VALUES must reach the frontend -> `mart_stock_cards.sql` SELECT += them;
    `_marts.yml` docs; `EXPORT_COLUMNS` += them; `008_financial_card_metrics.sql` adds the 4 nullable columns;
    `data_contract.md` export table += them.
  - **Bank fixture:** one `info_sector: 'Financial Services'` row per active market in `seed_ci_raw_fixtures.py`
    (null current assets/liabilities; present forward_pe, net_income_common+equity, net_income+revenue, total_assets,
    tangible_book+market_cap, dividend_yield in percent) -> `company_type=financial`, core three present -> eligible.
    CI baseline 25 -> 30.
  - **dividendYield scale guard:** dbt unit test `card_metrics_dividend_yield_pct_percent_passthrough` asserting
    `dividend_yield_pct == info_dividend_yield` (1:1 passthrough, percent) — pins the transform; live yfinance
    scale drift stays covered by `audit_mart_vs_yfinance.py` (dividend_yield_pct is now a mart metric it compares).

done_when:
  - `dbt build --project-dir dbt_analytics --profiles-dir . --no-partial-parse --full-refresh` green incl. the
    per-type eligibility test + the financial-eligibility unit test; the bank fixture is `financial` + eligible.
  - `python scripts/export_metric_definitions_json.py` -> `metrics.json` regenerated & committed.
  - Gates green: layer / SQL-structure / doc / sqlfluff; `check_eligibility_baseline.py --baseline-path
    scripts/eligibility_baseline.ci.json` -> **30**; export-health OK.
  - `pytest tests/` -> current + new financial tests + the scale guard.
  - Bank-card smoke: a card from the financial fixture mart row renders the 7 (no `—`), omits solvency/liquidity/cash;
    operating fixture card unchanged (its 8).
  - Full blinded review cycle recorded in `review.md`; reviewed commit + separate artifact commit; PR to main (NOT merged).

impact_map:
  - **Eligible pool changes** (first time): banks with the core three now appear. CI baseline 25 -> 30 (fixture);
    full-pipeline baseline (843) rises -> `check_eligibility_baseline.py` passes (only fails on drops) -> refresh
    via `--write-baseline` on the next weekly pipeline (owner; not local).
  - Operating + pre-revenue cards unchanged (operating eligibility + its 8 metrics identical; pre_revenue still on
    the 5-AND). New Supabase columns additive/nullable.
  - Required reviewers (per `.claude/review_routing.json`): **scope-auditor** (always) · **analytics-engineer**
    (`*.sql`, `*.csv`, `_marts.yml`) · **cto** (`scripts/*`, `tests/*`, `frontend/*`) · **data-engineer**
    (`supabase/*`) · **equity-analyst** (`metric_catalogue.csv`, `data_contract.md` — the bank copy + ROA/ROE
    asymmetry). No `ingestion/` source change (the scale-guard test is under `tests/`).

amendments:
  - 2026-07-08 — supersedes the merged Slice 4a contract (#145). Scope = Sector Router Slice 4b (financial/bank
    card + per-type eligibility rework) per approved plan dynamic-snuggling-truffle.md.
  - 2026-07-08 (review cycle 1) — 5 blinded reviewers: scope-auditor / analytics-engineer / cto / data-engineer
    PASS; equity-analyst ESCALATE (2 owner-judgment items), both resolved. (Q2) reworded `price_to_tangible_book`
    applicability — "meaningless or negative" -> "not shown" (the model guards tangible book > 0, so it is omitted,
    not rendered negative). (Q1) **owner kept the P/E-based core three** (declined the P/E -> P/TBV swap) via
    AskUserQuestion. Fixed the analytics-engineer non-blocking nit (stale "five-metric" prose in the
    `mart_stock_eligibility_gaps` description). **Owner §6 copy sign-off obtained this session**: the 4 bank-metric
    copy was presented via AskUserQuestion and the owner selected "Approve — ship as-is" (2026-07-08).
