# Review

> DISPOSABLE. **Owns:** THIS task's reviewer verdicts and the staged-diff hash they were
> given against.
> **Never:** a rule. Overwritten by the next task.

diff_sha256: 3b3f24166996a667a74091a421f3ec4f9e88cec60d7aa8d17792f6719f20cb53

Four reviewers, by routing: scope-auditor (`always`), analytics-engineer-reviewer
(`dbt_analytics/*.yml`), cto-reviewer (`tests/*`), equity-analyst-reviewer
(`docs/data_contract.md`). Two rounds.

## What shipped

A dbt unit test on `fct_fundamentals_snapshot` feeds two dates for one ticker and expects only
the later. Deleting the `qualify` fails it; the pre-existing `(market_code, ticker)` data test
passes that same mutant on stored data, because every raw file carries one date. The grain
tests on `int_stock__card_metrics`, `mart_stock_cards` and `mart_stock_eligibility_gaps` are
tightened from three columns to `(market_code, ticker)`, the grain those models have. No SQL
changed. Local `dbt build` of the four models: 56 PASS.

## Round 1

scope-auditor and analytics-engineer converged: the new Grain lines claimed one `snapshot_date`
per build, which a per-market re-run makes false (markets can sit on different dates; the
grain is per ticker, not per build); `docs/data_contract.md` and a `test_export_to_supabase.py`
docstring still described the old three-column declaration; the contract named a model that
does not exist. All fixed; the two swept files were added to `scope_paths`.

## scope-auditor

VERDICT: PASS

## analytics-engineer-reviewer

Traced every join: `dim_stock` and constituents unique per ticker, benchmarks per
`(market_code, sector)`, so nothing fans out a ticker. Killed the `qualify` mutant with the
unit test and confirmed the old test passes it.

VERDICT: PASS

## cto-reviewer

VERDICT: PASS

## equity-analyst-reviewer

VERDICT: PASS

## Owner decisions

None. The Postgres table's grain in `docs/data_contract.md` stays three-column; it accumulates.
