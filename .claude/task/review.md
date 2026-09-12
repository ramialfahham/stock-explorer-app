# Review

> DISPOSABLE. **Owns:** THIS task's reviewer verdicts and the staged-diff hash they were
> given against.
> **Never:** a rule. Overwritten by the next task.

diff_sha256: 96263f2fbb2c6b5821aaf1e6975bb1116ee8f52762a34a9c840e1217873f1b5d

Four reviewers, by routing: scope-auditor (`always`), analytics-engineer-reviewer
(`*.sql`, seeds), equity-analyst-reviewer (`*metric_catalogue.csv`), cto-reviewer
(`tests/*`, `frontend/*`). Six rounds, five of them the cto against one test.

## What shipped

Issue #12. Three catalogue `applicability` sentences said "banks" for rules that withhold a
metric from the whole `financial` type; replaced with the owner's wording (quoted in the
contract), only the "banks" sentence of each string touched, CSV rewritten through the csv
module. `frontend/metrics.json` regenerated. Two tests: rows whose `applies_to` excludes
`financial` may not mention banks, except the owner's pinned `current_ratio_stmt` sentence;
the three reworded rows are pinned to the owner's text. 678 tests.

## Rounds 1 to 5

cto: the guard began as a regex for "not shown/defined for banks" and each round a paraphrase
escaped it ("not presented", "not broken out", "Excluded", "Absent", then "banking sector").
Widening the word list three times did not end it; the cto's own proposal did: key the guard
off `applies_to` and forbid the word stem "bank" on withheld rows, exempting only the owner's
sentence verbatim. Mutants on `statement_roe_pct` pass by design: that row is shown for
banks, so a withholding sentence there would be false, not shorthand. scope-auditor passed
twice (contract bullet re-checked against the redesigned test).

## scope-auditor

VERDICT: PASS

## analytics-engineer-reviewer

VERDICT: PASS

## equity-analyst-reviewer

VERDICT: PASS

## cto-reviewer

VERDICT: PASS

## Owner decisions

The three sentences are the owner's. Recorded and NOT done, for the owner: `statement_roe_pct`
still ends "Means something different for banks" (content-free caveat; say how, or drop);
`working_capital` says "no turnover" where the classifier admits negligible revenue and every
other row says "revenue".
