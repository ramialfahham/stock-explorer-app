# Task contract
> DISPOSABLE. **Owner:** THIS task's objective, `scope_paths`, reserved decisions and
> `done_when`.
> **Never:** anything that outlives the task. Overwritten by the next task.

objective: Works #84 (HYG-1 defect 58, HYG-3 defects 59 and 60 of the second quality-baseline audit re-run). A dbt
  selectors file nothing uses, and two pairs of copied logic with no lock between them. Same rules as #76: a file nothing
  runs is deleted, and one piece of logic has one definition. The handover also records the owner's answer A of
  2026-10-26: the milestone closes on the list of 34 findings, not on a clean re-run.

scope_paths:
  - dbt_analytics/selectors.yml
  - scripts/export_to_supabase.py
  - scripts/generate_assessments.py
  - scripts/check_docs_indexed.py
  - scripts/check_context_budget.py
  - scripts/governed_files.py
  - tests/tooling/test_governed_files.py
  - tests/tooling/test_export_coerce_cell.py
  - tests/tooling/test_check_docs_indexed.py
  - tests/tooling/test_check_context_budget.py
  - .claude/active_work.md
  - .claude/task/contract.md
  - .claude/task/review.md

decisions_reserved: None open. The owner's answer A (2026-10-26) sets the order of work and the milestone exit; the
  delete-what-nothing-uses rule is the one answered for #76. No behaviour, metric, copy or schema change.

changes:
  - Delete `dbt_analytics/selectors.yml` (three selectors, no `--selector` use anywhere).
  - `scripts/export_to_supabase.py`: the inline per-cell coercion becomes the public `coerce_cell`;
    `scripts/generate_assessments.py` imports it and its own `_coerce` copy is deleted. Same branches, same results.
  - New `scripts/governed_files.py` with `files_matching(root, patterns)`; `check_docs_indexed.py` and
    `check_context_budget.py` call it, and their two identical walks (`governed_docs`, `governed_files`) are deleted.
    The two tests that called those functions call `files_matching(root, GOVERNED_GLOBS)`.
  - New tests: `coerce_cell` (missing values, dates, numpy scalars, passthrough) and `files_matching` (patterns, posix
    paths, directories are not files).
  - `.claude/active_work.md`: the milestone exit and the issue list.

done_when:
  - `git grep -n -E "selectors\.yml|_coerce\b|def governed_files" -- . ':!.claude/task' ':!docs/quality_criteria.json'`
    finds nothing, and `git grep -n "governed_docs" -- scripts` finds nothing; `dbt_analytics/selectors.yml` does not
    exist. (`tests/tooling/test_doc_paths_exist.py` has its own, different `governed_docs`; it is not touched.)
  - `git grep -n "def coerce_cell\|def files_matching"` finds one definition each; both scripts of each pair call it.
  - Mutating `coerce_cell` (dates as `str(value)`) and `files_matching` (directories count) each fail a test.
  - `pytest tests -q` passes; `python scripts/check_context_budget.py` and `scripts/check_docs_indexed.py` pass.

known_limits:
  - `dbt` is not run here (no warehouse on this machine); nothing in the repo references `selectors.yml`, and dbt reads it
    only for `--selector`.

regression_checklist:
  - The export rows are unchanged: `tests/tooling/test_export_to_supabase.py` and `test_generate_assessments.py` pass as before.
  - Both doc checks still pass on the real tree.
