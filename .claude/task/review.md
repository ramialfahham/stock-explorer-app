# Review

> DISPOSABLE. **Owns:** THIS task's reviewer verdicts and the staged-diff hash they were
> given against.
> **Never:** a rule. Overwritten by the next task.

diff_sha256: 8b82403a9c54e733fe0432e4362b1d73873aa76804dd1e266b2007e630292b90

Two reviewers, by routing: scope-auditor (`always`), cto-reviewer (`frontend/*`, `tests/*`).
One round.

## What shipped

The min/median/max range bar never named its own population -- "sector" only appeared once,
higher up the card, or in the fallback "No sector comparison for this metric." line.
`metric_gloss()` (`frontend/card_copy.py`) now takes `benchmarked: bool = False`; when True,
inserts ", vs sector" before the direction cue. `_metric_cell_html` (`frontend/card_ui.py`)
passes it only when `_metric_range_html()` actually rendered a mark for that metric on that
card -- the peer-count gate is per-card, not a property of the metric in the abstract. The two
value-aware early-return branches (net cash, negative equity) are untouched, same as the
existing universal direction cue. `docs/ui/card_metric_cell.md` documents the addition.

721 tests (was 718; net +3).

## Round 1

scope-auditor: PASS. No findings.

cto-reviewer: PASS. No findings -- independently verified the early-return branches stay
untouched, the neutral-direction case degrades safely (dead in practice, no catalogued metric
is neutral today), the mutation test genuinely proves per-card gating (not
`metric in BENCHMARK_METRICS`), full suite and context-budget checks green, no em-dash on any
added line, no stale contradicting doc prose.

## scope-auditor

VERDICT: PASS

## cto-reviewer

VERDICT: PASS

## Owner decisions

Fold "vs sector" into the gloss line rather than add a new word-labels row (already tight on
space) -- owner's call, in chat.
