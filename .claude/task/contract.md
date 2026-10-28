# Task contract
> DISPOSABLE. **Owner:** THIS task's objective, `scope_paths`, reserved decisions and
> `done_when`.
> **Never:** anything that outlives the task. Overwritten by the next task.

objective: Works #83 (DOC-3 defect 29, DOC-1 defect 30, DOC-2 defects 34 to 37 of the second quality-baseline audit
  re-run). One rule: a durable doc states the current rule or fact, once, and is not a log, a count that is stated several
  ways, or a to-do; every copy of a changed claim is fixed, in docs, code comments and tests alike.

scope_paths:
  - docs/operations_guide.md
  - docs/data_contract.md
  - docs/supabase_setup.md
  - docs/development_workflow.md
  - docs/working_agreement.md
  - docs/ui/card_metric_cell.md
  - supabase/migrations/017_sector_benchmark_financial_operating.sql
  - tests/tooling/test_export_to_supabase.py
  - .claude/active_work.md
  - .claude/task/contract.md
  - .claude/task/review.md

decisions_reserved: Answered 2026-10-28. Defect 36 (the open "worth a skill" to-do in `docs/development_workflow.md`):
  answer A, delete it, no new issue. The other five need no owner choice: the written rule (`docs/engineering_standards.md`
  section 1.2, `.claude/working-agreement.md` section 2) already says current state only.

changes:
  - `docs/operations_guide.md`: the diagram no longer lists "refresh constituents" under the scheduled CI run (it is a
    manual step, section "Refresh constituents"); the monitor paragraph drops the "check interval was not captured"
    setup history; the key paragraph drops the rejected-argument sentence ("NOT acceptable on the grounds that..."); the
    `/auth/v1/health` sentence states the current fact (the monitor uses the database URL, that endpoint needs a key), not the order tried.
  - `docs/data_contract.md`, `docs/ui/card_metric_cell.md`, the comment in migration 017 and the comment in
    `tests/tooling/test_export_to_supabase.py`: the pre-revenue company count (3 in four places, 11 and 15 rows in two
    more) is dropped; the rule stays: too few pre-revenue companies to clear the 8-peer threshold. No SQL line changes.
  - `docs/supabase_setup.md` section 3c: the measurement log (nine markets, 3.9 MB, 2.87s, 4.21s, 2.8x) is dropped; the
    rule stays: one RPC, the margin to the 8s bound shrinks with every market added.
  - `docs/development_workflow.md`: the "Still uncovered, worth a skill" paragraph is deleted.
  - `docs/working_agreement.md`: the "as of the card-metric-cell redesign" parenthetical is deleted; the links stay.

done_when:
  - `git grep -n -i -E "only 3 pre|exist app-wide|11 rows the pre_revenue|15 .pre_revenue|tried first to avoid|interval was not captured|worth a skill when|as of the card-metric-cell|Measured at nine|2\.87s|2\.8x" -- . ':!.claude/task' ':!tests/fixtures'` finds nothing (the one hit that stays, `frontend/styles.py` "tried first" about a layout, is not matched by `tried first to avoid`).
  - `git grep -n "refresh constituents" -- docs` finds only the section heading `### Refresh constituents`.
  - `pytest tests -q` passes; `check_context_budget.py` and `check_docs_indexed.py` pass.

known_limits:
  - The measured ranges kept in `docs/data_contract.md` (599 and 5,726 rows, min and max values) are other point-in-time
    figures; they are data-contract evidence for a bound, not part of these six defects.
  - No re-measurement of the pre-revenue population: the local database has no marts schema.

regression_checklist:
  - The 8-peer threshold wording in "Peer threshold" and the benchmark text is unchanged.
  - Migration 017 changes in comment lines only.
  - Every doc linked from `CLAUDE.md` is still linked.
