# Review

> DISPOSABLE. **Owns:** THIS task's reviewer verdicts and the staged-diff hash they were
> given against.
> **Never:** a rule. Overwritten by the next task.

diff_sha256: 4b677cffc6c385f7e3e7c91598835a415297b091fb2f098ca6a0992f317a6900

Four reviewers, by routing: scope-auditor (`always`), analytics-engineer-reviewer (`*.sql`,
`dbt_analytics/*.yml`), equity-analyst-reviewer (`docs/data_contract.md`), cto-reviewer
(`docs/context_budget.yml`). Three rounds.

## What shipped

`int_stock__card_metrics` scales a raw `dividendYield` below 0.05 by 100; a warn-severity
singular test lists those rows each run; the percent-scale flip guard reads the raw column
for this metric so a wholesale provider flip still fails the build; seven descriptions and
`docs/data_contract.md` state the rule as a fact about the data it was set on, with both
failure modes named; eight stale column-status claims in `_intermediate.yml` corrected.
`docs/data_contract.md`'s byte budget 58,000 to 59,000 (net +601 of contract text; the file
was 210 under at HEAD). 676 tests; dbt build green.

## Round 1

All three: correcting rows inside the model blinded the existing flip guard for yields under
5%, and the contract's guard section still claimed detection. Fixed by re-pointing the guard's
dividend branch at raw `fct_fundamentals_snapshot`; a simulated wholesale flip fails it.
equity-analyst: "no real yield sits below 0.05%" was written as a law; now a dated fact with
its failure modes. scope-auditor: five more "not in the Supabase export" claims stood in the
same file; "passthrough above 0.05" contradicted "0.05 or above".

## Round 2

scope-auditor and analytics-engineer: my rewrite of `statement_roe_pct`'s status was wrong
on every count (it is catalogued, in financial eligibility, and rendered). Fixed. cto passed
the budget raise as contract text at the smallest round step.

## scope-auditor

VERDICT: PASS

## analytics-engineer-reviewer

VERDICT: PASS

## equity-analyst-reviewer

VERDICT: PASS

## cto-reviewer

VERDICT: PASS

## Owner decisions

Correct on read at 0.05, chosen in chat over reject or leave. Recorded and NOT done: a
decimals-based discriminator, which would catch a fraction row at any yield but mis-scale a
genuine four-decimal percent.
