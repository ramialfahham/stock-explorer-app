# Review

> DISPOSABLE. **Owns:** THIS task's reviewer verdicts and the staged-diff hash they were
> given against.
> **Never:** a rule. Overwritten by the next task.

diff_sha256: 013eae288ef8e2c6309f0fcbf12d803b39923aea006f957140d8fff7b4898fe9

Four reviewers, by routing: scope-auditor (`always`), analytics-engineer-reviewer
(`dbt_analytics/*.yml`), equity-analyst-reviewer (`docs/data_contract.md`), cto-reviewer
(`docs/context_budget.yml`). Five review rounds -- three real findings, two mechanical
contract-wording fixes.

## What shipped

`dbt_utils.accepted_range` (`severity: warn`, non-blocking) added to eight card metrics prone
to near-zero-denominator explosion in `dbt_analytics/models/5_marts/_marts.yml`:
`ebit_margin_pct`, `revenue_growth_yoy_pct`, `net_debt_to_ebitda`, `fcf_margin_pct`,
`debt_to_equity`, `statement_roe_pct`, `net_margin_pct`, `cash_runway_months`. Bounds measured
against a full paginated export of the production `mart_stock_cards` table (5,726 rows,
2026-09-15). Four excluded candidates (`roa_pct`, `current_ratio_stmt`,
`price_to_tangible_book`, `net_cash_to_market_cap`) checked against the same export and
documented, not silently dropped. `docs/data_contract.md` documents all of it;
`docs/context_budget.yml`'s budget for that file raised 60000 -> 64000 across the task's
review rounds; `.claude/active_work.md` item 4 closed, including two stale "no accepted_range
tests" mentions elsewhere in the file reconciled.

735 tests pass throughout (no new Python tests needed -- this is dbt test config, not
application logic). `dbt build --project-dir dbt_analytics --profiles-dir . --select
mart_stock_cards --full-refresh`: PASS=22 WARN=0 ERROR=0 on the final state. Every one of the
eight guards was mutation-tested individually during implementation (temporarily narrowed
until real fixture data tripped `WARN`, then restored) -- not just present, proven to fire.

## Round 1

scope-auditor: PASS. cto-reviewer: PASS (budget bump 60000->61000, correctly measured and
proportionate).

equity-analyst-reviewer: PASS on `docs/data_contract.md`'s content, but flagged an
out-of-scope observation: `.claude/active_work.md` still had two stale spots claiming "there
are no `accepted_range` tests" even though the file's own new entry said otherwise. Fixed
(both spots reconciled) before round 2.

analytics-engineer-reviewer: FAIL. `net_margin_pct` was missing from the six guarded metrics
despite sharing `fcf_margin_pct`'s exact revenue denominator and catalogue caveat
("breaks for pre-revenue firms, revenue ~ 0"), and gating financial-card eligibility. The
original selection method -- grepping the metric catalogue's `applicability` field for
explosion language -- missed it because that field's wording for `net_margin_pct` doesn't use
the word "explode." Verified independently against `metric_catalogue.csv` and `_marts.yml`'s
`is_card_eligible` expression before fixing. Added the same guard (bounds -150000/150000,
matching `fcf_margin_pct`'s denominator class), measured its real range against production
(-66,685.5% DYL to 203.9% PNI), documented it as a seventh metric, and checked two secondary
candidates (`roa_pct`, `current_ratio_stmt`) against production, excluding both with
documented reasoning.

## Round 2

scope-auditor, equity-analyst-reviewer, cto-reviewer: PASS on the round-1 fix.

analytics-engineer-reviewer: FAIL, a second real gap. `cash_runway_months` divides cash by
unfloored monthly burn (`-computed_fcf`, only gated `> 0`, never bounded away from zero) in
`int_stock__card_metrics.sql` -- the same explosion class, invisible to a catalogue-text grep
because the risk lives in the model SQL, not in prose. Not theoretical: measured 1093.1
months for LLOY. Verified independently against production before fixing. Added the guard
(bound 0/100000, floor of 0 justified by the metric's structural non-negativity), documented
it as an eighth metric, and checked+excluded two more candidates
(`price_to_tangible_book`, `net_cash_to_market_cap`, both documented dead columns).

## Round 3

analytics-engineer-reviewer, cto-reviewer: PASS on the round-2 fix.

scope-auditor: FAIL -- `.claude/task/contract.md`'s `impact_map` said the budget was "raised
60000 -> 61000" when the staged diff showed 60000 -> 63000 (three raises, not one). Fixed
(wording only, no code/doc change).

equity-analyst-reviewer: FAIL, a real accuracy defect. The `cash_runway_months` paragraph
claimed its measured extremes came from "599 pre-revenue rows" -- but LLOY (the max) is
`company_type = financial` and SRE (the min) is `operating`; only 11 of the 599 non-null rows
are actually `pre_revenue`, ranging 1.50-41.31 months. Verified independently against
production (queried `company_type` alongside the metric, which the original measurement
hadn't) before fixing: rewrote the paragraph to correctly describe the full 599-row
all-company-types population versus the 11-row pre-revenue-rendered subset, both ranges
stated accurately. Budget bumped 63000 -> 64000 to fit (rounded up for real headroom per
cto-reviewer's round-3 feedback, not re-measured to the exact byte).

## Round 4

scope-auditor, equity-analyst-reviewer, cto-reviewer: PASS on the round-3 fixes.
cto-reviewer's round-3 feedback (this should be the last budget raise; round headroom up, not
to the byte) confirmed correctly applied.

analytics-engineer-reviewer: PASS on the `cash_runway_months` fix, plus an exhaustive division
audit of every exported column in `int_stock__card_metrics.sql` -- no remaining
unguarded/undocumented near-zero-denominator division found. Noted one non-blocking wording
nit: the exclusion paragraph implied both `price_to_tangible_book` and
`net_cash_to_market_cap` carry the literal phrase "no card renders it" in `_marts.yml`, but
only the former does (the latter says "superseded by `net_cash`"). Fixed for precision (no
fact changed, wording only).

## Round 5 (equity-analyst-reviewer only, narrow re-check)

equity-analyst-reviewer: PASS. Confirmed the round-4 wording fix quotes each column's actual
`_marts.yml` description accurately, doesn't imply false equivalence between the two
exclusion reasons, and is wording-only (no number or claim changed elsewhere).

## scope-auditor

VERDICT: PASS

## analytics-engineer-reviewer

VERDICT: PASS

## equity-analyst-reviewer

VERDICT: PASS

## cto-reviewer

VERDICT: PASS

## Owner decisions

Wide sanity guard (`severity: warn`) over a definitional hard-null bound -- owner's call, in
chat, 2026-09-15, made before this task started (recorded in `.claude/active_work.md`'s prior
entry). Everything else in this task -- which metrics to guard, what bounds, which candidates
to exclude and why -- is engineering judgment backed by measurement, not a new owner
decision, per the task contract's `decisions_reserved`.
