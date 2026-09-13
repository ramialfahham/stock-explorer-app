# Task contract
> DISPOSABLE. **Owns:** THIS task's objective, `scope_paths`, reserved decisions and
> `done_when`.
> **Never:** anything that outlives the task. Overwritten by the next task.

objective: `docs/development_workflow.md` describes `validate:full` as a short always-on list
  plus path-triggered dbt builds; the job has no path rules and runs nine more steps. Rewrite
  the tier from `.gitlab-ci.yml`, delete the partial copy in `docs/project_context.md`, fix
  the two twins that named a tier or a file that no longer exists.

scope_paths:
  - docs/development_workflow.md
  - docs/project_context.md
  - docs/engineering_standards.md
  - docs/operations_guide.md
  - .claude/task/contract.md
  - .claude/task/review.md
  - .claude/active_work.md

decisions_reserved:
  - None. Tier names kept (A for `validate:full`, C for `data-pipeline`); Tier B removed
    because nothing implements it. No CI change.

done_when:
  - Tier A lists every `validate:full` step in the job's order, and every step listed is in
    the job (reviewer diffs the list against `.gitlab-ci.yml`).
  - No "Tier B", "path-triggered" or "CI extensions" text remains outside `docs/handover_*`.
  - `docs/engineering_standards.md` names the `data-pipeline` job, not `data_pipeline.yml`;
    `docs/operations_guide.md` says Tier A, not A/B.
  - `scripts/check_context_budget.py` passes.

impact_map: Docs only.
