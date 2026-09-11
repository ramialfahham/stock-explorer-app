# Review

> DISPOSABLE. **Owns:** THIS task's reviewer verdicts and the staged-diff hash they were
> given against.
> **Never:** a rule. Overwritten by the next task.

diff_sha256: 31d743ba7ed7e378300c302558e987598190554f6410075a895b62db3087bac5

Four reviewers, by routing: scope-auditor (`always`), analytics-engineer-reviewer (`*.sql`),
cto-reviewer (`tests/*`), equity-analyst-reviewer (`docs/data_contract.md`). Three rounds.

## What shipped

A singular dbt test over `mart_stock_cards` joined to the `metric_catalogue` seed: for each
`(market_code, company_type, metric)` the catalogue says applies, fewer than half of the
eligible cards carrying a value fails the build; groups under five rows are skipped. Owner-set
floor. A Python test renders the singular test and executes it against an in-memory DuckDB with
the real catalogue, nine cases. 659 tests.

## Round 1

cto: the Python pin parsed source lines; three plausible edits escaped it and the constant
pin was theatre. Rewritten to execute the rendered SQL, as prescribed. scope-auditor and
analytics-engineer: the contract claimed CI fixtures exercise every type; they are 5/1/1 per
market, so CI reaches the floor for operating metrics only. Stated in contract and doc; the
Python test covers the other two types. analytics-engineer: `applies_to` tokens now trimmed.

## Round 2

cto: two boundary escapes, the eligibility filter and exactly-half. Two cases added; the first
fixture attempt landed exactly at 50% and did not catch the mutant, so it uses six ineligible
rows. scope-auditor: the contract said the fixture-count question was "recorded in the
handover" before the handover commit existed; now future tense.

## scope-auditor

VERDICT: PASS

## analytics-engineer-reviewer

VERDICT: PASS

## cto-reviewer

VERDICT: PASS

## equity-analyst-reviewer

Confirmed that eligibility-gating metrics are non-null on every eligible row by construction,
so the floor protects exactly the displayed-but-not-required ones. Flagged for the handover:
`cash_runway_months` and `burn_rate_monthly` are legitimately null for pre-revenue companies
not burning cash, a latent false positive if a market ever holds five such cards.

VERDICT: PASS

## Owner decisions

The 50% floor, five-row sample skip: set in chat on the measured production fill.
