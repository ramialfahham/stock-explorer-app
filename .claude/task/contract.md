# Task contract
> DISPOSABLE. **Owns:** THIS task's objective, `scope_paths`, reserved decisions and
> `done_when`.
> **Never:** anything that outlives the task. Overwritten by the next task.

objective: Closes #32 -- the raw archive's end-of-job marker test pins the exact
  `test ! -f` form, and the credential and job-step docs list the raw archive.

scope_paths:
  - tests/tooling/test_archive_raw_to_supabase.py
  - README.md
  - docs/supabase_setup.md
  - docs/development_workflow.md
  - .claude/task/contract.md
  - .claude/task/review.md
  - .claude/task/review_input.patch

decisions_reserved: none open. Owner approved in-thread: an exact-form assertion rather than
  running the step through `bash -c`; also fix the same claim beyond the issue's checklist
  (README `SUPABASE_URL` row; `generate_assessments.py` in the `data-pipeline` step lists).

done_when:
  - The marker test fails when the last `data-pipeline` step is inverted to `test -f`.
  - README and `docs/supabase_setup.md` list every production writer that reads
    `SUPABASE_URL` / `SUPABASE_SERVICE_ROLE_KEY`: export, raw archive, assessments.
  - Both step lists in `docs/development_workflow.md` include the raw archive and the
    assessments step, in job order.

known_limits:
  - The marker test checks the step's text, not its shell behaviour.

regression_checklist:
  - The marker test still passes on the committed `.gitlab-ci.yml`.
  - No doc line lists a script that does not read the variable it is listed under.
