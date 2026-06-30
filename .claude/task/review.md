# Review

diff_sha256: a54b58f66a05ebf10011ef75fea7051f78091fcd3f9d52b547839fc0e88508f7

_Data-only ratio metrics (current ratio, P/B, P/S, EV/EBITDA), branch `feat/ratio-metrics-data`. Five
blinded reviewers (cold, read-only, per `.claude/review_routing.json`) against the staged diff._

## scope-auditor
VERDICT: PASS
risks_checked:
- Eligibility drift: the eligibility CTE (int_stock__card_metrics.sql) still enumerates exactly the
  original five metrics in both missing_metrics and is_card_eligible; the four new passthroughs are not
  referenced, so the 25-ticker baseline and export shape are structurally unchanged.
- Silent §6 metric-copy authoring (the #135 lesson): every new description in _intermediate.yml and
  data_contract.md is a factual field/formula mapping ("metric = Yahoo key", "passthrough", "data-only");
  no label/gloss/analogy/applicability wording was authored. The lone evaluative phrase ("may be
  negative") is on roe_pct, unchanged from the merged baseline.
- Reserved display-surface decisions: grep of metric_catalogue.csv, frontend/metrics.json, and both marts
  found zero occurrences of the four new names — catalogue/metrics.json/card/export left to the Router.
- Scope containment: all 11 reviewed-diff files are in scope_paths; review.md/active_work.md correctly
  handled as the post-commit artifact step.

## analytics-engineer-reviewer
VERDICT: PASS
risks_checked:
- Reach / consumption-shape unchanged: mart_stock_cards uses an explicit column list that omits the four
  new columns (not select *); mart_stock_eligibility_gaps references none; repo-wide grep finds the four
  names only in the 11 in-scope files (absent from the catalogue seed, frontend, export script). The
  columns die at the intermediate layer — export-health/eligibility-baseline cannot move.
- Layer placement + eligibility-invariance + test coverage: staging casts only; base propagates via
  select *; core adds explicit selects; intermediate adds four passthroughs with NO ×100 (correct — these
  are ratios, unlike the decimal×100 roe_pct/revenue_growth); the eligibility CTE still gates on exactly
  the five; the extended T1 unit test feeds the four info_* inputs and asserts the four equal-valued
  outputs (a ×100 slip or wrong source column would fail it). Doc gate satisfied (every new column documented).

## data-engineer-reviewer
VERDICT: PASS
risks_checked:
- Idempotency / write-mode: ingest still does full-overwrite to_parquet(index=False); the four new fields
  are additive columns on the same write path — a re-run cannot duplicate/truncate.
- Completeness honesty + parsing safety: the four entries ride the existing dict-key passthrough
  row[col] = info.get(key) (not new parsing/merge logic, so no offline-payload fixtures owed); a missing
  Yahoo key yields an honest None; the per-ticker try/except still fails loudly. Keys verified live on AAPL.
- Reach stated with evidence: schema doc updated same-branch (data_contract raw mappings + computed-metric
  list); flow lands as four passthroughs in int_stock__card_metrics; eligibility CTE references only the
  five; grep of 5_marts/ and export_to_supabase.py for the four names → no matches (data-only); CI fixtures
  feed the new staging casts offline. Cost/scope knobs (LOOKBACK_DAYS, BATCH_SIZE, cadence, the single
  ticker.info call) untouched.

## cto-reviewer
VERDICT: PASS
risks_checked:
- Re-run/interruption + fail-closed integrity: _write_market_fixtures uses mkdir(exist_ok=True) +
  to_parquet full-overwrite (no append) — idempotent; the four added dict literals don't alter that. The
  script feeds dbt build and fails CLOSED (omitting the columns would error the build — the exact failure
  the change prevents); no .github/workflows/hook/dependency/secret/CI-cadence change; minimal edit.
- Guard-gate non-regression + value/test consistency: the four columns flow to int but mart_stock_cards
  does not select them, so check_eligibility_baseline (5/market) and check_export_health (100%) stay green;
  values (1.5, 8.0, 5.0, 15.0) are plausible positive floats fixtured like the existing decimal
  info_return_on_equity, not load-bearing for the unit test (which mocks fct_fundamentals_snapshot
  directly), and passthrough-no-×100 matches the int SQL.

## equity-analyst-reviewer
VERDICT: PASS
risks_checked:
- Missing ×100 scaling (highest-value defect for this slice): verified each field is genuinely a
  ratio/multiple in Yahoo's API, NOT a decimal fraction like returnOnEquity — currentRatio (~1.5x),
  priceToBook, priceToSalesTrailing12Months, enterpriseToEbitda — so the passthrough with no ×100 is
  arithmetically correct; the unit-test expectations equal their inputs, confirming a true passthrough.
- Field→name accuracy: each mapping is financially correct — currentRatio = current assets/current
  liabilities; priceToBook = price/book per share; priceToSalesTrailing12Months = price/sales TTM
  (correctly market-cap-based, not EV/sales); enterpriseToEbitda = EV/EBITDA. No mismatched description.
- Advice / threshold leakage: zero buy/sell/hold, "higher/lower is better," or invented thresholds in the
  routed data_contract.md or the .yml descriptions — purely neutral/technical, consistent with deferring
  interpretation copy to the Router; no fabricated numbers (fixtures are explicit synthetic mocks).
- Inert-data safety: confirmed the four metrics render NOTHING — absent from metric_catalogue.csv,
  frontend/metrics.json, the eligibility CTE, and mart_stock_cards (explicit select) — so a beginner sees
  none of this copy; the factual mapping is safe to land.
