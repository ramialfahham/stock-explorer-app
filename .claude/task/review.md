# Review

> DISPOSABLE. **Owns:** THIS task's reviewer verdicts and the staged-diff hash they were
> given against.
> **Never:** a rule. Overwritten by the next task.

diff_sha256: d63af2224350388a0c163f68fd540d8b3c373c93eb40a4d25ff9bd703a310649

Five reviewers, by routing: scope-auditor (`always`), cto-reviewer (`scripts/*`, `tests/*`,
`frontend/*`, `.gitlab-ci.yml`), analytics-engineer-reviewer (`*.sql`), equity-analyst-reviewer
(`docs/data_contract.md`), data-engineer-reviewer (`supabase/*`, added round 2). Two rounds.

## What shipped

Owner feedback (in chat): documents and code comments had accumulated date-stamped,
decision-history narrative -- the same fact restated 3-5 times across code comments,
docstrings, tests, and docs (the upsert-clobbering root cause, the MR #22 benchmark expansion,
a 2026-09-14 UI decision). Direct violation of `engineering_standards.md` §1.2/§1.3, a rule
that already existed but had no enforcement.

Fixed every found instance by stating the durable technical fact and dropping the
date/MR-reference/owner-decision wording. Built `scripts/check_no_narrative_dates.py`
(AST-based Python docstring detection, quote-aware SQL comment scanning, DURABLE-header-gated
Markdown scanning) wired into both pre-commit and CI, matching `check_context_budget.py`'s
existing precedent for how a written rule becomes an enforced one.

735 pre-existing tests plus 16 new guard tests, all green.

## Round 1

equity-analyst-reviewer: PASS -- confirmed the three date-stamps removed from
`docs/data_contract.md` carried no factual/numeric change, only narrative-anchoring language.

analytics-engineer-reviewer: PASS on the two dbt SQL model fixes and the checker's SQL-scanning
logic, but flagged (not blocking that round's scope) that `docs/ui/card_metric_cell.md` still
carried the exact violation pattern, invisible to the checker because that directory uses a
`**Scope:**`/`**Authority:**` header instead of `> DURABLE.`.

scope-auditor: FAIL, a real finding. `frontend/app.py`'s `_DECK_TTL_SECONDS` comment fix had
deleted a genuine technical constraint (a 15-60 minute acceptable band) along with the
date-stamp/owner-approval wording that was the actual violation -- pure information loss, not
cleanup.

cto-reviewer: FAIL, a real and more serious finding. The checker's `supabase/migrations/`
exemption was justified by a claim ("numbered, append-only... never edited again") disproved
by this repo's own git log -- `018_atomic_card_export.sql` was edited by a later commit after
its initial merge. The excluded directory already held two live, unflagged violations of the
exact pattern the tool exists to catch (`013_net_cash.sql`, `017_sector_benchmark_financial_operating.sql`).

## Fixes between rounds

- `frontend/app.py`: restored the 15-60 minute band, kept the date/owner-approval wording gone.
- `scripts/check_no_narrative_dates.py`: removed the `supabase/migrations/` exemption entirely
  (migrations are scanned like any other SQL now); fixed the two real violations it had been
  hiding; corrected the module docstring's inaccurate claim that the allow-marker "exempts
  that one line" (it exempts the whole enclosing docstring/block comment for multi-line units,
  per-line only for `#`/`--` comments and Markdown).
- Extended the Markdown scan to always include `docs/ui/*.md` (matching
  `check_context_budget.py`'s existing governance of that directory at the same tier),
  regardless of header convention -- surfaced and fixed 4 more real violations:
  `docs/ui/card_metric_cell.md` (an MR !87 verification-history digression, and a "was 4
  before... was 5 before..." historical tangent removed entirely as redundant with the doc's
  own already-stated current metric count), `docs/ui/design_system.md`, `docs/ui/discover_list.md`
  (two spots).
- Test suite updated: the old test asserting migrations were exempt replaced with one proving
  they're scanned and one proving a SQL `comment on column` string literal (real persisted
  database metadata, not a code comment) is still correctly left alone.

## Round 2

scope-auditor: PASS. Confirmed the `frontend/app.py` fix restores the constraint, confirmed
the `card_metric_cell.md` deletions don't orphan any fact not independently stated elsewhere
in the same file or in `docs/data_contract.md`.

cto-reviewer: PASS. Independently re-verified the `018_atomic_card_export.sql` post-merge-edit
claim via `git log`, confirmed the exemption is genuinely removed (not just re-scoped),
confirmed the docstring's allow-marker description now matches actual per-unit behavior.

analytics-engineer-reviewer: PASS. Confirmed both migration files' DDL/DML statements are
byte-identical except comment text; confirmed the one sub-fact with no current-state
restatement anywhere ("the bank card lost 3 of its 7 metrics") is itself historical-delta
narrative, correctly removed rather than an oversight.

data-engineer-reviewer: PASS (new this round, routed in by the migration files). Gave an
independent judgment that un-exempting `supabase/migrations/` is the right call -- the rule
targets prose narrative, not a migration's own time-ordering, which git and the filename
already carry. Flagged, out of scope, that migration 018 being edited post-merge instead of
superseded by a new migration is itself worth a separate look -- not folded into this task.

## scope-auditor

VERDICT: PASS

## cto-reviewer

VERDICT: PASS

## analytics-engineer-reviewer

VERDICT: PASS

## equity-analyst-reviewer

VERDICT: PASS

## data-engineer-reviewer

VERDICT: PASS

## Owner decisions

None new -- the mechanism itself (a pre-commit + CI check for this already-written rule) was
scoped and approved in plan-mode review before this branch existed.
