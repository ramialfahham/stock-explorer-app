# Review

> DISPOSABLE. **Owns:** THIS task's reviewer verdicts and the staged-diff hash they were
> given against.
> **Never:** a rule. Overwritten by the next task.

diff_sha256: 2346ec0c980a4b95ab553dd700bde0404d9d7dfe85bc6d330c211f6e8783c778

Four reviewers, by routing: scope-auditor (`always`), analytics-engineer-reviewer (`*.csv`),
equity-analyst-reviewer (`*metric_catalogue.csv`), cto-reviewer (`frontend/*` --
`frontend/metrics.json`, missed in the initial routing pass, caught by the commit gate).
Two rounds.

## What shipped

`revenue_growth_yoy_pct`'s catalogue copy (`interpretation` and `learn` fields) told readers
"one quarter can be noisy, so look for a pattern over time" -- contradicting the app's own
verdict rule (`GROWTH_DECLINE_THRESHOLD_PCT = 0.0`, no tolerance band), which reacts to ANY
single-quarter year-over-year decline by deliberate owner decision (a -5% tolerance proposed
on exactly this argument was already rejected). The copy told readers to discount the very
signal the verdict treats as real. Reworded to state the genuine, verdict-consistent caveats
instead: selling off part of the business, currency swings, or a big contract landing in a
different quarter, not just softer demand -- in plain language, no unglossed jargon.
`frontend/metrics.json` regenerated from the seed. `.claude/active_work.md`'s item 2 closed.

735 tests, all pre-existing (copy-only change; the catalogue/JSON no-drift lock and
`dbt parse` both confirm consistency, no new tests needed).

## Round 1

scope-auditor: PASS. analytics-engineer-reviewer: PASS -- verified CSV field-count integrity
row by row, regenerated `metrics.json` independently and diffed byte-for-byte against the
committed file, confirmed `dbt parse` succeeds.

equity-analyst-reviewer: FAIL. The new caveat list ("divestment", "FX translation"/"FX
swings", "contract timing") introduced unglossed jargon into beginner-facing copy, against
this app's own "assume no finance vocabulary, gloss every term" standard
(`docs/north_star.md`, `scripts/assessment_rules.py`'s `READ_SYSTEM_PROMPT`). Fixed: jargon
replaced with plain phrasing directly ("selling off part of the business", "currency swings",
"a big contract landing in a different quarter") rather than jargon-plus-gloss.

## Round 2

scope-auditor: FAIL on a process-timing note (`review.md` still held the prior task's
verdicts, since this file -- the final step before commit -- had not been written yet).
Resolved by writing this file now, the same point in the cycle every prior task in this
session reached it at.

analytics-engineer-reviewer: not re-dispatched (its round-1 findings were mechanical/CSV-
integrity checks unaffected by a copy-only jargon fix).

equity-analyst-reviewer: PASS -- confirmed no jargon term remains unglossed anywhere in the
row, confirmed the plain-language substitutions are still accurate restatements of the same
four owner-approved causes, confirmed the copy reads naturally, full suite and em-dash scan
green.

## Round 3 (cto-reviewer, caught by the commit gate)

cto-reviewer: PASS -- independently regenerated `frontend/metrics.json` from the current
seed and diffed byte-for-byte against the committed file, confirmed only the two fields for
`revenue_growth_yoy_pct` changed, full suite and em-dash scan green.

## scope-auditor

VERDICT: PASS

## analytics-engineer-reviewer

VERDICT: PASS

## equity-analyst-reviewer

VERDICT: PASS

## cto-reviewer

VERDICT: PASS

## Owner decisions

Soften/remove the "noisy... look for a pattern" framing, replacing it with the real
verdict-consistent caveats -- owner's call, in chat, 2026-09-15.
