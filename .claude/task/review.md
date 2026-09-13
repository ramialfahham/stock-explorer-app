# Review

> DISPOSABLE. **Owns:** THIS task's reviewer verdicts and the staged-diff hash they were
> given against.
> **Never:** a rule. Overwritten by the next task.

diff_sha256: 9cc179d3dd98002261628873e1489eaa6c03b2964de68552bc68636457eac3ab

Three reviewers, by routing: scope-auditor (`always`), cto-reviewer (`frontend/*`,
`tests/*`), equity-analyst-reviewer (`docs/data_contract.md`, staged from round 2). Two
rounds.

## What shipped

Issue #11, owner chose A. `FINANCIAL_CAPITAL_ADEQUACY_CAVEAT` renders once under the metric
stack of every financial-type card (`_financial_caveat_html`), in every state of the health
block including its absence; the block no longer emits it. CSS rule rescoped; the caption
treatment reused. Tests over `build_card_html` in four states, plus a styles test pinning
the selector. `docs/ui/card_metric_cell.md` specifies the line; `docs/ui/disclosure_pattern.md`
and `docs/data_contract.md` no longer place it in the block. 693 tests.

## Round 1

cto and scope-auditor: `docs/data_contract.md` still said the caveat "rides with the health
block" and recorded issue #11 as an accepted gap, in two paragraphs. Rewritten. cto: no test
noticed a revert of the CSS selector (caveat present, unstyled); added one, mutant fails.

## scope-auditor

VERDICT: PASS

## cto-reviewer

VERDICT: PASS

## equity-analyst-reviewer

VERDICT: PASS

## Owner decisions

Placement A, chosen in chat over B. Wording unchanged. equity-analyst confirmed "these
numbers" scopes to the whole metric grid (the caveat is a sibling of the grid, not inside
the last cell) and stays true on a card with no verdict.
