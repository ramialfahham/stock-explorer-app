# Review

> DISPOSABLE. **Owns:** THIS task's reviewer verdicts and the staged-diff hash they were
> given against.
> **Never:** a rule. Overwritten by the next task.

diff_sha256: a0f105b105a21159557fb45d3533646fcda76658c1497b1b8fb6338bce71630f

Two reviewers, by routing: scope-auditor (`always`), cto-reviewer (`frontend/*`, `tests/*`).
Three rounds.

## What shipped

`import yfinance` moves from the top of `frontend/saved_news.py` into `_fetch_news`, the only
user; importing `app` no longer loads yfinance, pandas or numpy (subprocess test, fails
against HEAD). Measured here, best of five: 6.72 s and 2,097 modules before, 5.26 s and
1,572 after; cto reproduced 6.72 / 5.19 and the module counts. 712 tests.

## Rounds 1 and 2

scope-auditor: the comment stated a Render number measured only here; number removed. cto:
with the import moved, deleting it would be a NameError swallowed by `fetch_saved_news`'s
except and no test ran that body; a unit test now calls `_fetch_news` against a fake
yfinance in `sys.modules`, mutation-proven.

## scope-auditor

VERDICT: PASS

## cto-reviewer

VERDICT: PASS

## Owner decisions

A over B (lazy import before a faster host), in chat.
