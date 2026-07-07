# Review

diff_sha256: 2fd979389a6128f83748b9daa03c17dd80189ab4b1947b9f55e228a70630f7ef

_Statement completion (Slice 2b, DATA-ONLY), branch `feat/statement-completion`. Five blinded reviewers
(cold, read-only, per `.claude/review_routing.json`: scope-auditor always; analytics-engineer for
`.sql`/`.yml`; data-engineer for `ingestion/`; cto for `scripts/`; equity-analyst for `data_contract.md`).
All five PASS on this diff, first round._

## scope-auditor
VERDICT: PASS
risks_checked:
- All diff files in `scope_paths`; both schema mirrors (`sources.yml` + `FUNDAMENTALS_COLUMNS`) updated in
  lockstep. DATA-ONLY verified by grep: the 6 names have 0 occurrences in `int_stock__card_metrics.sql`
  (eligibility/missing_metrics) and 0 in `mart_stock_cards.sql` → baseline 25 / export shape untouched.
- No §6 silent decision: no new mechanism/fetch (reuses the pre-existing `_latest_annual_statement_value`
  on already-fetched income/cashflow frames), no metric computed; the sign-convention note is factual
  sourcing rationale, not a metric assignment; `decisions_reserved` (per-type sets) not entered.

## analytics-engineer-reviewer
VERDICT: PASS
risks_checked:
- Reach traced: `resolved` does `select s.*` but the `metrics` CTE re-projects an explicit list that drops
  all 6; eligibility / `mart_stock_cards` / `int_stock__sector_benchmarks` are downstream of that boundary →
  cannot reach them. Grain unchanged at every layer; baseline 25 holds.
- Layer placement pure (cast in staging, `select *` base, passthrough core); doc gate satisfied — 6 cols
  declared in `sources.yml` + documented at staging/base/core; CI fixture keeps grain/eligibility intact.

## data-engineer-reviewer
VERDICT: PASS
risks_checked:
- No new fetch: `income`/`cashflow` are already fetched; the 4 new `_latest_annual_statement_value` calls
  read the in-memory frames (zero new network calls/cadence/fan-out). Idempotent full-overwrite parquet;
  deterministic fixtures. Absent line → honest null (capex null for some banks).
- Untested inline extraction is a consistent extension of the untested `stmt_operating_*`/`stmt_total_revenue`
  precedent (same unchanged helper, canonical single labels — no new parsing logic). Both mirrors updated
  (the `.reindex` would otherwise drop the columns); code row-label constants match the doc mapping.

## cto-reviewer
VERDICT: PASS
risks_checked:
- No new dependency/service/hook/workflow; `FUNDAMENTALS_COLUMNS` is a plain tuple extension, fixtures a
  constant-dict extension. Re-run safe (deterministic full-overwrite). The `FUNDAMENTALS_COLUMNS` +6 makes
  `.reindex` RETAIN the columns (correct fail-closed direction). No secrets/CI-permission change.
- No cost delta: income/cashflow already fetched; dividend fields ride the existing single `ticker.info`
  call. No CI-minute impact.

## equity-analyst-reviewer
VERDICT: PASS
risks_checked:
- Row-label canonicality verified against vendored yfinance `const.py` + `camel2title` (`NetIncome` →
  `Net Income`, etc.; the "NI" acronym doesn't corrupt the label) — same proven mechanism as the merged
  `Total Revenue` / `Free Cash Flow`. Sign conventions correct: `Capital Expenditure` negative → FCF =
  OCF + capex; `Interest Expense` positive magnitude; the fixture signs (capex -2e9, interest +5e8) match
  the doc (a real correctness check).
- Docs strictly factual (mapping + sign conventions + a scoped "computed FCF = OCF + capex, not computed
  here" note) — no advice/threshold/beginner copy, no per-type "primary metric" claim. Diff limited to RAW
  landing; no metric defined/redefined (§6 untouched).

## Non-blocking items recorded for Slice 3 (not defects here)
- **Interest-expense sign documented but not enforced in code** (no `abs()`): Slice-3 `interest_coverage`
  should compute defensively (`abs(stmt_interest_expense)` or validate the sign).
- **Statement-ROE attribution mismatch:** `stmt_net_income` (Net Income) includes non-controlling interest,
  while the Slice-2 equity lines deliberately exclude it — a naive `net_income / stockholders_equity` mixes
  all-shareholder income over parent-only equity. Slice 3 should use `Net Income Common Stockholders` for
  that ratio, or document the approximation.
