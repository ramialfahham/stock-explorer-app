# Review

> DISPOSABLE. **Owns:** THIS task's reviewer verdicts and the staged-diff hash they were
> given against.
> **Never:** a rule. Overwritten by the next task.

diff_sha256: a25efe3d653166e81645c800572925551c7bb1c6ce48e1136530565583e1640b

Four reviewers, by routing: scope-auditor (`always`), cto-reviewer (`scripts/*`, `tests/*`),
equity-analyst-reviewer (`docs/data_contract.md`, `docs/metric_layer.md`),
analytics-engineer-reviewer (`*.sql`, two comment lines in the model). Three rounds.

## What shipped

`docs/data_contract.md`'s card-metrics table is generated from `metric_catalogue.csv` by
`scripts/render_metric_table.py` between two markers; `test_data_contract_metric_table_matches_seed`
fails on a stale block. The 13 data-only intermediates are listed by name, the model their
only definition, guarded by a test that each name is a model column and none is catalogued.
Two "why" notes that had lived only in the deleted prose sit beside their formulas in
`int_stock__card_metrics.sql`. 697 tests.

## Round 1

scope-auditor: dropping the data-only formulas went beyond the owner's "generate the table";
put to the owner as a two-way question, owner chose drop. equity-analyst: two definitional
notes (`fcf_yield_pct`'s trailing FCF; `interest_coverage`'s `abs()`) lost their only home;
moved into the model. cto: `read_text` strips CRs, so the script's line-ending sniff was dead
code and a Windows checkout would have been rewritten to LF; fixed with `open(newline="")`
and a unit test over CRLF and LF temp docs, mutation-proven; the `|` escape got a unit test.

## Round 2 and 3

All PASS; round 3 a one-character escape-sequence fix (cto nit).

## scope-auditor

VERDICT: PASS

## cto-reviewer

VERDICT: PASS

## equity-analyst-reviewer

VERDICT: PASS

## analytics-engineer-reviewer

VERDICT: PASS

## Owner decisions

Generate over delete (A); drop the data-only formulas rather than keep them as prose (A). Both
in chat, recorded in the contract.
