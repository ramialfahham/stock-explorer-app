# Review

diff_sha256: 61a1277d24fb11e2c0bbd24371e15fe9bcb9b4dfc37cb00b6b5fa554fbdf9a60

_FCF yield (data-only), branch `feat/fcf-yield-data`. Five blinded reviewers (cold, read-only, per
`.claude/review_routing.json`) against the staged diff._

## scope-auditor
VERDICT: PASS
risks_checked:
- FCF numerator fork (trailing freeCashflow vs annual stmt_free_cash_flow): verified in contract
  decisions_reserved it is recorded as an explicit OWNER decision this session, not a silent builder pick;
  data_contract.md states only the factual period-matching rationale (no beginner/interpretive caveat),
  so the #135 §6 copy-authoring trap is avoided.
- Eligibility + display boundary: read int_stock__card_metrics.sql directly — missing_metrics and
  is_card_eligible still list exactly the original five; fcf_yield_pct is computed but excluded from both;
  metric_catalogue.csv, metrics.json, card_copy, and mart_stock_cards untouched. All 11 staged files in
  scope_paths (review.md correctly the unstaged artifact).

## analytics-engineer-reviewer
VERDICT: PASS
risks_checked:
- Divide-by-zero / null honesty: the case guards `info_market_cap is not null and != 0` before dividing
  (CASE short-circuits → no divide on zero/null denominator); a null numerator (banks) propagates to null
  as intended. Shape is identical to the already-tested net_debt_to_ebitda / fcf_margin_pct guards.
- Layer placement: raw fields propagate staging (cast) → base (select *) → core (passthrough select), and
  the guarded ratio sits in 4_intermediate alongside the other card ratios — no compute leaked into
  staging/core, per layering.md.
- Eligibility / grain containment + second-FCF risk: missing_metrics/is_card_eligible still enumerate the
  five; the new nullable column adds no rows; marts build without it. The distinct trailing-FCF figure
  (vs annual stmt FCF) is an owner-resolved choice, documented factually in data_contract + _intermediate.yml,
  feeding separate metrics with no cross-use.

## data-engineer-reviewer
VERDICT: PASS
risks_checked:
- Parsing-vs-passthrough: the two INFO_FIELDS entries ride the existing info.get(key) passthrough (no new
  parsing/merge), so no offline payload fixtures owed; the CI fixture carries both new fields.
- Idempotency + completeness honesty: parquet write unchanged (full-overwrite, same grain) so re-run can't
  duplicate/truncate; missing freeCashflow (banks) → honest null, row still written, guarded denominator
  yields null fcf_yield_pct.
- Cost/scope + reach: no LOOKBACK/BATCH/cadence/fan-out change (free riders on the existing ticker.info
  call); raw columns documented same-branch; fcf_yield_pct absent from the five-metric eligibility set and
  the mart_stock_cards export columns — export shape + baseline unchanged.

## cto-reviewer
VERDICT: PASS
risks_checked:
- (territory: scripts/seed_ci_raw_fixtures.py) Re-run/fail-closed integrity: the two added dict literals
  ride the deterministic full-overwrite fixture generator (idempotent); they are required so the new
  staging casts have source columns — omitting them would fail CI's dbt build (fails CLOSED). No
  workflow/hook/dependency/secret/cadence change; minimal edit.
- Value plausibility / test independence: FCF 5e9 / market cap 1e11 → 5% is a plausible yield; the fixture
  is not load-bearing for the unit test (which mocks fct_fundamentals_snapshot directly with 50.0/1000.0 →
  5.0); eligibility baseline + export-health unaffected (fcf_yield_pct not in the mart).

## equity-analyst-reviewer
VERDICT: PASS
risks_checked:
- Formula + source soundness: `freeCashflow / marketCap × 100` is the textbook FCF yield; ×100 correctly
  renders the dimensionless ratio as a percent (unit test 50/1000×100=5.0, fixture 5e9/1e11×100=5.0). Both
  inputs are company-level, same-currency fields from the same ticker.info dict → dimensionally sound, no
  FX/grain mismatch (this vindicates the owner's trailing-source choice). The data_contract "trailing vs
  annual stmt_free_cash_flow" distinction is genuinely accurate (ticker.info vs ticker.cashflow), neutral,
  no advice/threshold language.
- Negative-numerator behavior (FLAG for the Router, not a defect here): info_free_cashflow is routinely
  negative for cash-burners, so fcf_yield_pct can be negative — arithmetically correct, honestly
  signed/null (never a misleading 0), and NOT displayed/interpreted in this data-only slice. The Router's
  deferred applicability copy MUST state "negative for cash-burners" (the data_contract note omits a
  negativity caveat, unlike the sibling roe_pct line). Recorded in active_work.md for the Router step.
