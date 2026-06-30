# Review

diff_sha256: c0c7cd0a5727b0ba2c34c7c6037add5fca4cc737654ea2c01a402ef876f0e9c4

_ROE data-only slice, branch `feat/roe-metric-data`. Five blinded reviewers (cold, read-only, per
`.claude/review_routing.json`) against the staged diff. The data_contract `roe_pct` note is the plain
factual data-only note (no interpretive caveat); ROE's applicability/interpretation wording is DEFERRED
to the Sector Router step per the owner (see the equity-analyst CPO ANSWER below)._

## scope-auditor
VERDICT: PASS
risks_checked:
- Eligibility/export silent-leak: roe_pct (int_stock__card_metrics.sql) is computed but absent from the
  eligibility CTE (still exactly the five metrics in both missing_metrics and is_card_eligible) and from
  mart_stock_cards' explicit column list — so is_card_eligible, the Supabase export shape, and the
  eligibility baseline are genuinely unchanged, matching the data-only intent.
- Deferred-decision leak: none of decisions_reserved (ROE beginner copy, catalogue row, metrics.json
  entry, display tier/order, per-sector gating, Supabase export) appears in the diff; the only definition
  is the technical roe_pct = info_return_on_equity * 100, implementing the owner-locked "use ROE" decision.
- Doc-sync: data_contract.md is updated in the same branch (raw-field mapping row + data-only note); every
  new model output column is documented in its yml (info_return_on_equity in staging/base/core, roe_pct in
  intermediate). The ux_principles "do not swap to ROE" line stays true because this slice adds no display.

## analytics-engineer-reviewer
VERDICT: PASS
risks_checked:
- Layer placement + raw propagation: roe_pct = s.info_return_on_equity * 100.0 lives in 4_intermediate
  (mirroring revenue_growth_yoy_pct), not in staging/base/core; the raw field rides the canonical path
  staging (cast) → base (select *) → core (explicit select) with no business logic in the wrong layer.
- Downstream reach / output invariance: the eligibility CTE still lists exactly the five metrics; both
  marts project explicitly and omit roe_pct (export shape unchanged), and sector_benchmarks never
  aggregates it; the new output column is covered by the extended T1 unit test (info_return_on_equity:
  0.18 → roe_pct: 18.0); every new output column is documented (doc gate satisfied). dbt build PASS=90.

## data-engineer-reviewer
VERDICT: PASS
risks_checked:
- Idempotency / write-mode + transitional reach: ingest writes full-overwrite parquet (to_parquet,
  index=False) unchanged; the new field is a pure info.get passthrough (no parsing/merge change). Prod
  data_pipeline.yml ingests before dbt build (and CI seeds fixtures before build), so the new staging cast
  never faces a parquet lacking the column.
- Completeness honesty + reach containment: missing returnOnEquity lands as honest null (info.get → None →
  null cast → null roe_pct), loss-maker negatives not clipped; roe_pct is excluded from
  missing_metrics/is_card_eligible and every mart, so the export shape is verifiably unchanged; the raw
  column is documented same-branch and covered by the CI fixture. No cost/cadence/fan-out knob touched.

## cto-reviewer
VERDICT: PASS
risks_checked:
- Guard integrity / fail-closed: the new staging cast cast(s.info_return_on_equity as double) would turn
  CI's dbt build RED if the fixture omitted the column, so adding "info_return_on_equity": 0.18 to
  seed_ci_raw_fixtures.py is the minimal edit that keeps the gate green without weakening it (still fails
  closed for a genuine omission). No .github/workflows, hook, dependency, or plugin-config change.
- Re-run/idempotency + plausibility: _write_market_fixtures is a deterministic full-overwrite (mkdir
  exist_ok + to_parquet), idempotent on re-run; 0.18 is a plausible decimal ROE fixtured like the sibling
  decimal info_revenue_growth: 0.08, yielding roe_pct = 18.0 to match the unit test. No secrets; no CI cost
  change.

## equity-analyst-reviewer
VERDICT: ESCALATE
questions:
- ROE's most dangerous distortion (negative shareholder equity → spuriously POSITIVE ROE; leverage
  inflation per DuPont) is not in the shipped data_contract caveat, which states only "nullable; may be
  negative (loss-makers); not clipped." The value is arithmetically correct and currently INERT (verified:
  roe_pct is in no catalogue row, frontend/metrics.json, Supabase mart_stock_cards, or the eligibility CTE
  — nothing renders it), and the contract DEFERS ROE's interpretation/applicability copy to the Sector
  Router. Should the owner: (a) accept landing ROE as inert data now with the applicability caveat deferred
  wholesale to the Router step that first displays it; or (b) require a one-line negative-equity/leverage
  caveat in the data_contract roe_pct note in THIS slice?

CPO ANSWER: (a) Defer. Owner decided this session to ship roe_pct as inert data-only and defer ROE's full
applicability/interpretation wording (negative-equity sign trap, leverage/DuPont, breaks-for-financials)
to the Sector Router step that first displays it — keeping all ROE wording decisions in one place with
owner sign-off there. roe_pct remains not carded, not catalogued, not in eligibility, and not exported in
this slice, so nothing surfaces the un-caveated value to a user until the Router lands. (A one-line caveat
was briefly added then reverted per this decision; the reviewed diff is the plain factual data-only note.)
