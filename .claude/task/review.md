# Review

> DISPOSABLE. **Owns:** THIS task's reviewer verdicts and the staged-diff hash they were
> given against.
> **Never:** a rule. Overwritten by the next task.

diff_sha256: 3a4f7aa06418da7d38e82a762cda6eea133a6c0927d5c548f652f6f66dce1b55

Two reviewers, by routing: scope-auditor (`always`), cto-reviewer (`frontend/*`, `tests/*`).
Three rounds.

## What shipped

Owner-set mobile type scale in `frontend/styles.py`: body 14px on a new `--ss-body` token,
captions 13px, chips and small labels 12px as the floor, row titles 15px, card title 17px.
Every `font-size` is a size token except the wordmark and the icon glyph. Three tests guard it:
every size is one of the six size tokens or a named exception, no size token under 0.75rem
and all in rem, four named body-copy rules on the body token. Docs updated. 662 tests.

Measured live at 375px: Discover 125 of 167 text elements under 14px before, 65 after, none
under 12; card 59 of 87 before with six at 10.9px, 36 after, none under 12; Saved minimum
13px; no horizontal scroll. The first metric on a long card sits 64px below the fold at
480x812 (20px above before); owner chose to ship and take header compaction next.

## Round 1

scope-auditor: the contract's site counts were grep-line counts, not declarations; a history
comment in the test; range-mark width claims measured at the old axis size. cto: the same
counts; `font-size :` and the `font:` shorthand escaped the guard; an unreachable assert.

## Round 2

cto: any `var(--ss-*)` passed the size test while only six names were floored, so a spacing
token or a new small token escaped. Fixed by requiring the token name to be a size token.
The author's first fix in round 1 had written `\b` as a literal backspace byte, which made the
regex vacuous; the mutants exposed it before the reviewers saw it.

## scope-auditor

VERDICT: PASS

## cto-reviewer

VERDICT: PASS

## Owner decisions

The scale, set in chat. Shipping with the first-metric fold check failing on long cards at
480px, recorded in `contract.md` with the numbers.
