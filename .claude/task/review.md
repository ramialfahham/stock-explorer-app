# Review

> DISPOSABLE. **Owns:** THIS task's reviewer verdicts and the staged-diff hash they were
> given against.
> **Never:** a rule. Overwritten by the next task.

diff_sha256: 4d42d2ccbc94505c002c50a0f3deb503832a0b1ec057777b78d7e4e2d8353c1d

Four reviewers, by routing: scope-auditor (`always`), analytics-engineer-reviewer, cto-reviewer,
equity-analyst-reviewer (`docs/data_contract.md`). Six rounds.

## What shipped

Fifteen Markdown files. Each context file opens with a DURABLE or DISPOSABLE header stating
what it owns and what it must never hold. The em/en-dash rule and the no-dates-in-comments rule
move from the disposable handover into `docs/engineering_standards.md` §1.2 and §1.3, with a
pointer from `CLAUDE.md`. `.claude/active_work.md` loses its "Standing decisions" section (each
entry checked against a durable twin before deletion) and gains the open items a future session
must act on, each with a runnable command. No executable line changed; `pytest tests/ -q` 625
passed.

## Measured

Net +1,222 bytes across the branch: disposable files shrink by 4,667, durable files grow by
5,889, of which roughly 1,083 is header-only in seven files. `active_work.md` is 28,392 bytes
against the enforced 32,000 cap, headroom up from 1,320 to 3,608.

## scope-auditor

Failed rounds 1 to 5, each on a claim contradicted by the file it sat in or by a second site:
a header on `docs/data_contract.md` false three times running, an "eleven first-party sites"
count that was wrong, `contract.md` holding `NOT DONE HERE, NEXT` items under a header
forbidding content that outlives the task, and a recorded grep that returned 33,563 hits.

Final round: 15 staged paths equal `scope_paths`; the ownership headers are true of the files
as staged; the date-sweep grep runs as written and returns 10. Noted, not blocking, that the
grep's blind spot is wider than item (c) states: five dated sites sit in docstrings and one
`COMMENT ON` literal that a comment-anchored pattern never touches.

VERDICT: PASS

## cto-reviewer

Failed round 1 on a standards paragraph asserting "the convention already used throughout the
repo" and a check "on the ADDED lines of a staged diff" that does not exist. Measured the branch
rather than accepting the author's framing and judged it net-positive on placement, not on
volume. Recommended that the next context task be a per-doc size budget in CI, because a budget
stops recurrence where a sweep removes text once.

Final round: hash confirmed, zero non-Markdown files staged, 625 tests green, three prior
findings verified closed.

VERDICT: PASS

## analytics-engineer-reviewer

Passed at three consecutive hashes. Confirmed the four `see .claude/task/contract.md` pointers
in `int_stock__card_metrics.sql` are dead: each comment states its reasoning inline before the
trailing clause, and the rewritten contract does not reference those columns. Noted that the
recorded pointer grep walks `.venv` and times out; `git grep -n "task/contract.md" -- '*.py'
'*.sql'` returns the same 7 hits in under a second.

VERDICT: PASS

## equity-analyst-reviewer

Checked the two verdict paragraphs moved from the handover into `docs/data_contract.md` against
the code. `burn_rate_monthly` sits in `INPUT_FIELDS_BY_TYPE` because that table is the full
displayed set, but `_verdict_pre_revenue` bands only `cash_runway_months`, `net_cash` and
`working_capital`, so the prose describes what the verdict reads. The double-counting reasoning
is arithmetically exact: catalogue runway is cash divided by burn. `assessment_rules.py` holds no
sector or percentile reference, so the ranking rejection describes the code as shipped.

VERDICT: PASS

## Owner decisions

The DURABLE/DISPOSABLE convention itself, recorded in `contract.md` as asked and answered.
Nothing else: no metric, label, format or shipped number changed.
