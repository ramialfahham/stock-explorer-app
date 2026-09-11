# Review

> DISPOSABLE. **Owns:** THIS task's reviewer verdicts and the staged-diff hash they were
> given against.
> **Never:** a rule. Overwritten by the next task.

diff_sha256: c72fed95fcc3b045048a04646ce502510a0d71b31edb3fd23b9e9faa445d3a8c

Two reviewers, by routing: scope-auditor (`always`), cto-reviewer (`scripts/*`, `tests/*`,
`.gitlab-ci.yml`, `.claude/review_routing.json`). Five rounds.

## What shipped

`docs/context_budget.yml` holds one byte budget per governed context file.
`scripts/check_context_budget.py` fails on over budget, governed-but-unbudgeted, or
budgeted-but-missing, measuring with CRLF collapsed to LF. It runs first in `validate:full` and
as an `always_run` pre-commit hook. Raising a budget routes to cto-reviewer. 17 tests, 642 in
the suite. The tree passes at 31 files.

## scope-auditor

Round 1: the flat 8,000 budget for `contract.md` and `review.md` was decided without being
written into `decisions_reserved`; the contract's headroom claim was false on a CRLF checkout.
Round 2: `docs/development_workflow.md` enumerated the pre-commit hooks and CI steps and was
not updated. Round 3: a count and peak in the review-budget rationale matched no reading of
`git log`. Round 4: the replacement §8 sentence claimed Tier A lists every `validate:full`
step; it omits nine.

Each fix was applied as named; the numbers were deleted rather than corrected.

VERDICT: PASS

## cto-reviewer

Round 1: `stat().st_size` on a `core.autocrlf=true` checkout gave CI up to 1,895 bytes of
unapproved headroom on the archives and made `over by N` non-reproducible between pre-commit
and CI. Fixed by normalising CRLF before counting, with a test, and regenerating seven budgets
from LF sizes. Round 2: the review-budget rationale cited a figure no committed review matched;
cto's own replacement figure was also wrong (round 3), so both were deleted in favour of the
command that produces them. Rounds 4 and 5: PASS.

VERDICT: PASS

## Owner decisions

The mechanism: yes. The 8,000 budget for `contract.md` and `review.md`: kept, on the corrected
evidence that several recent committed reviews exceeded it.
