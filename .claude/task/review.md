# Review

> DISPOSABLE. **Owns:** THIS task's reviewer verdicts and the staged-diff hash they were
> given against.
> **Never:** a rule. Overwritten by the next task.

diff_sha256: f9e3f4afd9653f67207d4fc370920cc672d54cb30cb880db82c67c6882caf638

Two reviewers, by routing: scope-auditor (`always`), cto-reviewer (`frontend/*`, `tests/*`).
Two rounds.

## What shipped

`?timing=1` prints the page's own stage clock: entry-script start, main start, css, header,
cookies, deck, page, run total, process age. One caption, only with the flag. 710 tests.

## Round 1

cto: the marks were module globals shared by every session's thread, so a concurrent visitor
could corrupt the reading; moved into `st.session_state`, the entry mark consumed by the run
that follows it. Two tests added.

## scope-auditor

VERDICT: PASS

## cto-reviewer

VERDICT: PASS

## Owner decisions

The switch was proposed and approved in chat; keep or remove after the measurement is the
owner's call.
