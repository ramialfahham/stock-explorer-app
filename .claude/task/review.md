# Review

> DISPOSABLE. **Owns:** THIS task's reviewer verdicts and the staged-diff hash they were
> given against.
> **Never:** a rule. Overwritten by the next task.

diff_sha256: 7d333141e76c5ced311424bcae398298a1166b9e189b055e4c6efaa29147f558

Four reviewers, by routing: scope-auditor (`always`), data-engineer-reviewer (`ingestion/*`),
cto-reviewer (`tests/*`), equity-analyst-reviewer (`docs/data_contract.md`). Two rounds.

## What shipped

`_fetch_fundamentals` names its failed tickers. `ingestion/main.py` exits 1 when a market's
fundamentals failures exceed 5% of its requested tickers and continues below that, naming the
failed tickers on stderr. The 5% is the baseline gate's `warn_drop_fraction`, pinned equal by a
test; same number, different denominator. 648 tests.

## Round 1, all four FAIL on the same prose

The gate logic held: cto ran eleven mutants and data-engineer checked the float boundary for
every market size to 5,000. Every finding was a claim I wrote: "nothing marking it stale" was
false because `freshness_line` prints the card's older As-of date, and "one tolerance with one
meaning" overstated a shared number into a shared quantity. Both fixed at every site.

## scope-auditor

VERDICT: PASS

## data-engineer-reviewer

VERDICT: PASS

## cto-reviewer

VERDICT: PASS

## equity-analyst-reviewer

VERDICT: PASS

## Owner decisions

Tolerant gate at 5%, chosen over strict, on the two paths in `contract.md`.
