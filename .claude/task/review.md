# Review

diff_sha256: bf1bd0f0fe592b285b253ea40ce3ff4a211c3e1ef9e94729dad47a306d61c720

_Per-type metric compute (Slice 3b, DATA-ONLY), branch `feat/statement-metric-compute`. Blinded reviewers
(cold, read-only, per `.claude/review_routing.json`): scope-auditor always; analytics-engineer for `.sql`/`.yml`;
equity-analyst for `data_contract.md` (+ scrutinised the SQL formulas). No ingestion/scripts/tests touched →
data-engineer + cto not required. All three PASS on this diff, first round. Adds 13 computed data-only columns
to `int_stock__card_metrics`; corrects the yfinance dividendYield percent-scale docs._

## scope-auditor
VERDICT: PASS
risks_checked:
- DATA-ONLY leak: grepped all 13 new column names across `5_marts/` + `int_stock__sector_benchmarks.sql` — zero
  matches. The `eligibility` CTE gates on only the original 5 metrics and is untouched by the diff; both marts
  (`mart_stock_cards`, `mart_stock_eligibility_gaps`) `select *` card_metrics into a CTE then project explicitly,
  excluding the 13. Export shape + baseline provably unchanged.
- dividendYield correction is descriptions-only: the sole `info_dividend_yield` cast (`stg_yf__fundamentals.sql`)
  is NOT staged; `dividend_yield_pct` is a bare passthrough (no ×100). All 5 edits are prose; the percent-scale
  finding + metric definitions are recorded as owner-locked in the contract's `decisions_reserved` (authority on
  record, not reviewer-inferred).
- Scope + routing: all 8 staged files in `scope_paths`; no ingestion/scripts/tests/frontend/supabase touched →
  the 3-reviewer routing is correct (data-engineer/cto correctly absent). §6 items (per-type sets, eligibility
  rework, mart carry, display, catalogue) all documented DEFERRED to Slice 4; none in the diff.

## analytics-engineer-reviewer
VERDICT: PASS
risks_checked:
- Re-projection boundary: traced all three consumers. `eligibility`'s `missing_metrics`/`is_card_eligible`
  reference only the original 5 metrics and are untouched. The 13 columns pass through `eligibility` `select *`
  but terminate at every downstream explicit projection — `mart_stock_cards` (5-metric projection,
  `where is_card_eligible` unchanged), `int_stock__sector_benchmarks` (never projected past
  `sector_medians`/`combined`), `mart_stock_eligibility_gaps` (identity-only). Export shape + baseline unchanged.
- Compute + layer: 13 CASE expressions use the existing null-input + non-zero-denominator guard idiom;
  `computed_fcf` resolves from the `resolved` CTE alias (not a self-alias); all source inputs exist in
  `fct_fundamentals_snapshot`. Logic sits in the intermediate `metrics` CTE — not pushed to marts or down to core.
- SQL structure + doc gate: max line 93 < 120; no inline/scalar subqueries; WITH/import-CTE rules hold; sqlfluff
  clean. 1:1 reconciliation of the new SQL aliases ↔ yml docs — all 13 documented, no orphans.
- Unit tests: hand-computed all 4 against the SQL (values match); they genuinely isolate distinct ROA (6000) vs
  ROE (5000) numerators, the abs()-interest sign (−500 → +16.0), runway-only-when-burning, and null-on-
  zero/negative denominator. Prior data_tests + 11 unit tests retained; §3 ≥1-test rule satisfied, none deleted.

## equity-analyst-reviewer
VERDICT: PASS
risks_checked:
- ROA-vs-ROE numerator asymmetry (highest-risk soundness question): `roa_pct` = total `stmt_net_income` /
  `stmt_total_assets`; `statement_roe_pct` = `stmt_net_income_common` / `stmt_stockholders_equity`. Each
  internally consistent — total assets financed by all capital providers (total-entity return on top), common
  equity matched to common income. `net_margin_pct` correctly uses total bottom-line NI. Distinct numerators
  exercised by the SM1 unit test. Financially sound.
- interest_coverage: numerator `eff_stmt_op` (EBIT-like operating income), denominator `abs(stmt_interest_expense)`
  — textbook EBIT/interest; interest landed positive, abs() defends sign variance; `!= 0` guard yields null (not
  infinity) at zero interest. Proven by the −500 → 16.0 test.
- dividendYield "already percent, no ×100": internally consistent + matches known yfinance 1.x behaviour; the
  cross-checks that `payoutRatio` (0.21) and `returnOnEquity` (0.165) stay fractions are the right evidence; cited
  yields realistic. `roe_pct = returnOnEquity × 100` correctly kept; "(decimal)"→"(percent)" applied in lockstep
  across all 5 touchpoints.
- EV / net_cash_to_ev: EV = market_cap + total_debt − cash; `net_cash_to_ev` = (cash − debt)/EV = −(net debt)/EV;
  guarded on zero EV. Standard + internally consistent.
- Guards + units: `price_to_tangible_book` strict `tbv > 0`; runway/burn only when `computed_fcf < 0`;
  `computed_fcf = OCF + capex` matches the negative-capex sign; all ratio denominators guarded `!= 0`; the ZERO
  row confirms nulls. Units consistent (percent, ratio, months, currency).
- Docs factuality: strictly formulaic — no advice/threshold/"good-bad"/beginner copy, no per-type "primary metric"
  claim (§6 reserved); lens labels are applicability, not advice. Each row repeats "not in eligibility, the metric
  catalogue, or the export yet."

## Non-blocking items recorded for Slice 4 (not defects here)
- **dividendYield scale is a live-probe fact, not a persisted invariant (equity-analyst):** a future yfinance
  version silently reverting `dividendYield` to a fraction would ship a 100× error. Add a lightweight persisted
  assertion or fixture spot-check that catches a scale regression.
- **ROA/ROE numerator asymmetry (equity-analyst):** ROA uses total NI, statement ROE uses common NI — surface in
  the catalogue copy so a beginner isn't confused that two "return" metrics use different income lines.
- **Point-in-time vs period-end vs Yahoo-averaged denominators (equity-analyst):** `price_to_tangible_book` /
  `net_cash_to_ev` / `debt_to_equity` pair point-in-time market cap / period-end balance-sheet stocks against
  period-end statement denominators, and `statement_roe_pct`/`roa_pct` use period-end (not average) balances — so
  they differ slightly from Yahoo's own scalars by design. Add an applicability caveat when catalogued.
