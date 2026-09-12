# Review

> DISPOSABLE. **Owns:** THIS task's reviewer verdicts and the staged-diff hash they were
> given against.
> **Never:** a rule. Overwritten by the next task.

diff_sha256: 4fc6dfadf9f503c64c3dc9b59d136bdd26ad525b64a28f2f8629090dcdc9aca6

Two reviewers, by routing: scope-auditor (`always`), cto-reviewer (`frontend/*`, `tests/*`,
`scripts/*`). Three rounds.

## What shipped

Issue #9 finding B1. The learn panel's playgrounds follow the card face: `playgrounds_for_card`
selects the metrics in `metrics_for_card(card)` that have a playground, in face order; the
panel renders one tab per such metric and nothing when there are none; tab and heading labels
come from `metric_label(metric, card)`; money inputs carry the card's currency through a
public `currency_symbol()` that `_format_currency_compact` now shares. The invariant in
`scripts/audit_mart_vs_yfinance.py` and `docs/metric_audit.md` reworded from "no Python
re-implementation of any formula" (false: this file) to "no Python path produces a stored
metric". 686 tests.

## Round 1

cto: after the change no test executed the render path at all (the e2e fixture cards carry
no metric values, so they now render zero tabs); a typo in the tab dispatch shipped green.
Fixed with an AppTest over `render_metric_playgrounds` for the three company types.
scope-auditor: `docs/backlog/landing_onboarding_rework.md` said the panel "renders
unconditionally"; corrected, path added to scope.

## Round 2

cto: the AppTest checked tab labels and input counts but not that a tab's content belongs to
it; zipping tabs with the registry put the margin playground under the growth tab on a
financial card and passed. Fixed: each tab's first heading is asserted against its metric.

## scope-auditor

VERDICT: PASS

## cto-reviewer

VERDICT: PASS

## Owner decisions

Playgrounds kept, per the owner in chat. Open, UX: tab labels now equal the bold heading
inside each tab (before: "Margin/Growth/Debt/FCF" tabs over full-label headings).
