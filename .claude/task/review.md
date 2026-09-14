# Review

> DISPOSABLE. **Owns:** THIS task's reviewer verdicts and the staged-diff hash they were
> given against.
> **Never:** a rule. Overwritten by the next task.

diff_sha256: 2457bb4ad52c9bc7c89e08987d7dfa70eb4b8efa8d16f3052ac494d0609cd9e3

Four reviewers, by routing: scope-auditor (`always`), analytics-engineer-reviewer (`*.sql`,
`dbt_analytics/*.yml`), cto-reviewer (`frontend/*`, `scripts/*`, `tests/*`,
`docs/context_budget.yml`), equity-analyst-reviewer (`docs/data_contract.md`,
`docs/metric_layer.md`). Two rounds.

## What shipped

Context debt. The handover's `## Do NOT` rules each have a durable home and the section is an
index (spend and owner-only ops, plain questions: working agreement §6, §8; metric rules:
`docs/data_contract.md`; `applies_to` from the first row: `docs/metric_layer.md`; the
snapshot gate: `attach_assessments` docstring; performance and `DECK_COLUMNS`:
`docs/operations_guide.md`; checks before push: `docs/development_workflow.md`). Seven dead
`task/contract.md` pointers deleted; dates stripped from code comments, comments kept;
`sources.yml` names the `data-pipeline` job. Issue #10 closed on GitLab. Comments and docs
only; 693 tests; `dbt parse` and `sqlfluff` clean.

## Round 1

equity-analyst: my compression of the metric rules overstated three things: "never the info
scalar" while `net_debt_to_ebitda`'s numerator does exactly that (now named as a shipped
exception, owner's call); "ROIC and multi-year series not sourceable" when both are scope
choices (now "deliberately not built"); a failure mode the code cannot produce ("or on every
card"; an empty `applies_to` excludes every type). cto: "about 1.2 MB" for Streamlit's bundle
was an unverifiable number; deleted. cto recommended naming the cheap pre-push checks instead
of all of Tier A; done. The fixes put `docs/data_contract.md` 30 bytes over its budget; raised
59000 to 59500, recorded in the contract.

## scope-auditor

VERDICT: PASS

## analytics-engineer-reviewer

VERDICT: PASS

## cto-reviewer

VERDICT: PASS

## equity-analyst-reviewer

VERDICT: PASS

## Owner decisions

None taken. Surfaced: `net_debt_to_ebitda`'s numerator reads `info_total_debt` /
`info_total_cash` where `stmt_total_debt` / `stmt_cash_and_equivalents` are landed; moving it
changes a shipped number. Options given to the owner in chat: leave and record as a decision;
switch; measure the difference on production data first (recommended).
