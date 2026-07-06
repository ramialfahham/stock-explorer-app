# Review

diff_sha256: 0db6330bd7c17535128d8c228e39f6a70f191e8ae4d699be078d6146a81bad21

_Company-type classifier (data-only, Slice 1 of the Sector/Lifecycle Router), branch
`feat/company-type-classifier`. Three blinded reviewers (cold, read-only, per
`.claude/review_routing.json`: scope-auditor always; analytics-engineer for the `.sql`/`.yml`;
equity-analyst for `data_contract.md`) against the staged diff. The diff was amended once after a
first PASS round to add the `FIN0` precedence unit-test row; all three reviewers re-ran against
this final staged diff and the hash above matches it._

## scope-auditor
VERDICT: PASS
risks_checked:
- Eligibility/export leak: `int_stock__card_metrics` chains `select *` through resolved/metrics, so
  a downstream `select *` could have leaked `company_type` to the export. Read both marts —
  `mart_stock_cards.sql` (10-31) and `mart_stock_eligibility_gaps.sql` (6-13) use explicit column
  lists excluding `company_type`, and the `eligibility` CTE (156-177) still gates on exactly the
  five metrics. "Not exported / baseline 25 unchanged / card byte-identical" holds.
- Owner authority + doc-sync: the three-type taxonomy, REITs→operating, and the `<= 0` / null-is-a-
  data-gap rule are §6 owner calls — all recorded in `decisions_reserved` and corroborated by the
  approved plan (`noble-forging-beaver.md`) and `active_work.md` (lines 43, 51). `data_contract.md`
  is updated in-branch, factual, matching the SQL exactly; nothing reserved was decided silently;
  deferred items (per-type sets, eligibility rework, catalogue/display, bank metrics, copy) stay out.

## analytics-engineer-reviewer
VERDICT: PASS
risks_checked:
- Downstream reach (traced, not asserted): `company_type` is added only to the `metrics` CTE
  (142-149); `eligibility`/`missing_metrics` (156-177) are unchanged (five metrics); both consumers
  select explicit lists omitting `company_type`; no join was added (the `left join dim_stock`
  pre-existed) → no grain/row-count change. Eligibility baseline + export shape/health structurally
  unchanged.
- Layer placement + tests: a derived closed-enum label correctly sits in 4_intermediate (refs only
  core, never a mart); `s.info_sector` and `s.stmt_total_revenue` both resolve on the snapshot; the
  literal `'Financial Services'` is the source sector label (not an opaque category id), owner-
  approved in the contract, with no `dim_sector` to reference. The unit test exercises every branch
  incl. `FIN0` (financial + 0 revenue → financial precedence) and `NUL` (null → operating);
  `not_null` + `accepted_values` present.

## equity-analyst-reviewer
VERDICT: PASS
risks_checked:
- Financial precedence for zero/missing-revenue financials: the `financial` branch is evaluated
  before `pre_revenue` (SQL 142-149), so a bank/insurer with `stmt_total_revenue` = 0, negative, or
  null is classified `financial` and never leaks into `pre_revenue` — financially correct (Yahoo's
  "Total Revenue" row is unreliable/absent for financials, whose income is net interest + fees).
  Locked by the `FIN0` unit-test row so a regression fails CI.
- Applicability / advice-line integrity: `data_contract.md` (141-152) and the yml description are
  strictly mechanical rule statements (three values, first-match order, "null revenue = data gap →
  operating"); no interpretive/threshold-as-fact claim, no direction, no good/bad or buy/sell/advice,
  and no `metric_catalogue`/`metrics.json`/beginner copy. Interpretive copy is correctly deferred per
  the contract, and the owner decisions are recorded in `contract.md` — §6 satisfied for a data-only
  classifier.
