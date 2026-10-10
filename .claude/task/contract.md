# Task contract
> DISPOSABLE. **Owns:** THIS task's objective, `scope_paths`, reserved decisions and
> `done_when`.
> **Never:** anything that outlives the task. Overwritten by the next task.

objective: Closes #46 -- stale, contradictory and broken doc claims fixed, and a guard test so a
  governed doc can no longer name a repo path that does not exist.

scope_paths:
  - docs/engineering_standards.md
  - README.md
  - .claude/skills/onboard-market/SKILL.md
  - docs/project_context.md
  - CLAUDE.md
  - docs/metric_layer.md
  - docs/data_contract.md
  - scripts/export_metric_definitions_json.py
  - dbt_analytics/seeds/_seeds.yml
  - scripts/check_no_narrative_dates.py
  - tests/tooling/test_doc_paths_exist.py
  - .claude/task/contract.md
  - .claude/task/review.md
  - .claude/task/review_input.patch

decisions_reserved: settled by the owner in-thread, as recommended -- finding 38 (a): narrow the
  CLAUDE.md sentence to "every `.md` file", matching what `check_docs_indexed.py` enforces; add the
  broken-path guard test (a new check), scoped to the narrative check's governed docs through a
  shared `is_governed_markdown` helper rather than a second copy of the list. Round-1 widening
  under the working agreement's grep-the-claim rule: the same wrong `raw_path` default in
  `data_contract.md`, and the same wrong test path in `export_metric_definitions_json.py` and (round
  2) `dbt_analytics/seeds/_seeds.yml`.

done_when:
  - Findings 34-39 of #46 are fixed as proposed (38 as option a).
  - `tests/tooling/test_doc_paths_exist.py` fails when a path-shaped word anywhere inside a
    backtick span in a GOVERNED_MARKDOWN doc does not exist (so a path inside a command counts;
    relative paths resolved from the doc's folder); it fails on
    main's three broken metric_layer.md paths and on nothing else, and passes after the fix.
  - `is_governed_markdown` is the one definition of the governed set; the narrative check's
    behaviour is unchanged.

known_limits:
  - Only backticked words with a directory part and a known text extension are checked; a bare
    filename, an unbackticked path, or a DURABLE-header doc outside GOVERNED_MARKDOWN is not.
  - Existence is checked on disk, so a gitignored local file can hide a broken reference locally;
    CI's clean checkout does not have that gap.

regression_checklist:
  - The narrative check's tests and repo-tree test still pass.
  - Every rewritten sentence matches the code it describes.
