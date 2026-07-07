# Task contract

objective: **Balance-sheet ingestion foundation** — Slice 2 of the Sector/Lifecycle Router, and the
  "do it right" correction. Fetch `ticker.balance_sheet` and land the core **latest-annual
  balance-sheet lines** as DATA-ONLY raw fields — the missing third financial statement. This is the
  foundation for computing statement-based, period-matched metrics (debt-to-equity, current ratio,
  working capital, tangible book / P-TBV, net cash) in a later slice, instead of Yahoo `info` scalar
  shortcuts. **No metric compute, no display, no eligibility change.** Approved plan:
  ~/.claude/plans/noble-forging-beaver.md.

scope_paths:
  - ingestion/yfinance/balance_sheet.py
  - ingestion/yfinance/ingest.py
  - scripts/probe_balance_sheet_labels.py
  - docs/intl-balance-sheet-row-labels.md
  - dbt_analytics/models/1_staging/yfinance/stg_yf__fundamentals.sql
  - dbt_analytics/models/1_staging/yfinance/_yfinance_staging.yml
  - dbt_analytics/models/2_base/yfinance/_yfinance_base.yml
  - dbt_analytics/models/3_core/fct_fundamentals_snapshot.sql
  - dbt_analytics/models/3_core/_core.yml
  - dbt_analytics/models/sources.yml
  - scripts/audit_mart_vs_yfinance.py
  - scripts/seed_ci_raw_fixtures.py
  - tests/test_balance_sheet.py
  - docs/data_contract.md
  - .claude/task/contract.md

review_artifacts (NOT in the reviewed diff — separate artifact-only commit after; review.md records the
  reviewed diff's hash):
  - .claude/task/review.md
  - .claude/active_work.md

decisions_reserved:
  - **"Do it right" (owner directive this session):** compute from period-matched financial statements,
    not `info` scalars; the balance sheet is the missing third statement. This slice lands the raw BS
    lines only.
  - DEFERRED to **Slice 4** (display), owner content: the per-type metric SETS (the matrix), which type
    gets which metric, and the **financials-solvency ceiling** — yfinance lacks CET1/Tier 1/NIM, so
    financials get no sound solvency metric (honest blank vs caveated proxy is the owner's product call).
  - DEFERRED to **Slice 3:** metric COMPUTATION (debt-to-equity, interest coverage, current ratio from
    BS, working capital, tangible book, cash runway, computed FCF = OCF − capex).
  - No interpretive/beginner copy here — `data_contract.md` stays factual (the #135 §6 lesson).

technical_definition (factual; no beginner copy):
  - New module `ingestion/yfinance/balance_sheet.py` (mirrors `quarterly.py`): `land_balance_sheet_fields`
    lands the latest-annual value per line, coalescing over ordered Yahoo row-label fallback tuples
    (mirror of `OPERATING_INCOME_FALLBACK_ROWS`). The balance sheet is point-in-time → latest annual
    column only, **no TTM summing**.
  - Core BS fields (raw `stmt_*`, nullable, not clipped): `stmt_stockholders_equity`, `stmt_total_debt`,
    `stmt_current_assets`, `stmt_current_liabilities`, `stmt_cash_and_equivalents`,
    `stmt_tangible_book_value`.
  - `ingest.py`: fetch `ticker.balance_sheet`; `row.update(land_balance_sheet_fields(ticker))`.
  - Fallback labels are set from **probe evidence** (`scripts/probe_balance_sheet_labels.py` across the
    5 markets), documented in `docs/intl-balance-sheet-row-labels.md`.
  - Propagate staging cast → base (`select *`) → core select; documented at each layer (doc gate). NOT
    in `is_card_eligible`/`missing_metrics`, NOT selected by `mart_stock_cards` (data-only).

done_when:
  - `balance_sheet.py` written; `land_balance_sheet_fields` wired into `_fetch_fundamentals_row`.
  - probe run across markets; labels + coverage recorded in `intl-balance-sheet-row-labels.md`; fallback
    tuples reflect the evidence.
  - 6 staging casts + docs; base docs; 6 core selects + docs.
  - CI fixtures (`seed_ci_raw_fixtures.py`) emit the 6 fields; `data_contract.md` gets a "From the
    balance sheet" raw-mapping subsection.
  - pytest for `land_balance_sheet_fields` (fallback coalesce order + null handling), no live network.
  - Verify green: dbt build; doc/layer/structure/sqlfluff; check_eligibility_baseline (**stays 25**) +
    check_export_health (**stays 100%**); pytest. Card byte-identical (frontend untouched).
  - After the reviewed commit (artifact-only): record review.md, advance active_work.md; PR to main (NOT merged).

impact_map:
  - New raw BS columns flow ingestion → staging (cast) → base (`select *`) → core (passthrough select).
    Two raw-schema **mirrors** are updated in lockstep (precedent: the `qtr_*` fields): `sources.yml`
    (`yf_fundamentals` source declaration) and `scripts/audit_mart_vs_yfinance.py` `FUNDAMENTALS_COLUMNS`
    (whose `.reindex(columns=...)` would otherwise silently drop the new columns when rebuilding the
    audit parquet). Absent from eligibility and from `mart_stock_cards` → export shape/health and the
    eligibility baseline are unchanged. frontend untouched (card byte-identical). `storage/raw` gitignored (CI
    regenerates fixtures). One extra `ticker.balance_sheet` fetch per ticker (a free rider on the
    existing per-ticker loop; no new cadence/fan-out).
  - Required reviewers (per `.claude/review_routing.json`): scope-auditor + analytics-engineer
    (`*.sql`/`dbt_analytics/*.yml`) + data-engineer (`ingestion/*`) + cto (`scripts/*`) + equity-analyst
    (`docs/data_contract.md`).

amendments:
  - 2026-07-06 — supersedes the merged company-type classifier contract (#139). Scope = balance-sheet
    ingestion foundation (Slice 2), per approved plan noble-forging-beaver.md and the owner's "do it
    right" correction (statement-based, not `info` scalars).
