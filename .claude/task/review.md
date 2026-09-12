# Review

> DISPOSABLE. **Owns:** THIS task's reviewer verdicts and the staged-diff hash they were
> given against.
> **Never:** a rule. Overwritten by the next task.

diff_sha256: 9279d1bec473f93292936353a82b8c18cd8f3a671dcf27d8f29626ade0ff62a7

Three reviewers, by routing: scope-auditor (`always`), cto-reviewer (`scripts/*`, `tests/*`),
equity-analyst-reviewer (`docs/data_contract.md`). Three rounds.

## What shipped

The AI read's facts block names every metric the way the card face does on that row and
renders every value with the same string the card renders. Four labels and the runway
rendering changed. Operating margin is per row: "(annual)" when the mart fell back to the
latest annual statement, so the loader now carries `ebit_margin_basis`. Three guards: brief
labels equal the catalogue's; the read's renderer equals `card_copy.format_metric_value` for
every metric in four currencies; the basis survives from DuckDB through the prompt and the
validator. 676 tests. `INPUT_HASH_VERSION` not bumped, the owner's spend call.

## Rounds

Round 1: the card's operating-margin label is not fixed text, which I had missed; the read
would have said "(TTM)" beside a card saying "(annual)" (scope-auditor, cto). The tool
schema's example label was the old wording (all three). Round 2: dropping the basis column
from the loader escaped every test (cto); the doc sentence still said "the catalogue's label"
(all three); the contract asserted a convergence rate nothing measures (scope-auditor). All
fixed; the rate is now stated as unmeasured with the check in the handover.

## scope-auditor

VERDICT: PASS

## cto-reviewer

VERDICT: PASS

## equity-analyst-reviewer

Confirmed the "(annual)" label is honest on those rows: the number is the latest annual
operating margin. Noted the four card labels carry abbreviations the gloss beside each still
explains in plain words, so the read stays beginner-readable; owner's choice.

VERDICT: PASS

## Owner decisions

The card's wording wins, per row. No hash bump: reads converge as their inputs move.
