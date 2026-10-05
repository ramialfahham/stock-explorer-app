# Task contract
> DISPOSABLE. **Owns:** THIS task's objective, `scope_paths`, reserved decisions and
> `done_when`.
> **Never:** anything that outlives the task. Overwritten by the next task.

objective: Closes #25 -- each production run archives its raw ingestion parquet to a private
  Supabase Storage bucket, before dbt, append-only, one folder per run.

scope_paths:
  - scripts/archive_raw_to_supabase.py
  - tests/tooling/test_archive_raw_to_supabase.py
  - .gitlab-ci.yml
  - docs/project_context.md
  - docs/operations_guide.md
  - docs/layering.md
  - .claude/active_work.md
  - .claude/task/contract.md
  - .claude/task/review.md
  - .claude/task/review_input.patch

decisions_reserved: settled by the owner in-thread before implementation --
  Go on the archive (a new mechanism). Credential (option A): the existing
  `SUPABASE_SERVICE_ROLE_KEY` through the already-pinned `supabase` client; no S3 access key,
  no new CI variable, no new dependency (replaces the issue's S3-key owner action). Failure
  (option C): an archive failure does not stop the run; the cards still refresh and the
  `data-pipeline` job fails at its end. The bucket is created by the script when missing,
  not by a migration, so a bucket problem cannot block the migration step that runs first.
  Layout (owner: option B, after round 1): a run-id level under the date, so no two runs
  share a folder; the run id is the GitLab job id (a retry keeps the pipeline id but gets a
  new job id).
  Open, owner's: retention, if the 1 GB quota is ever approached.

known_limits: none.

regression_checklist:
  - `data-pipeline` still runs migrations, ingestion, dbt, the checks, export and
    assessments in that order; only the archive step and the final marker check are new.
  - With no key set the archive script exits 0 and uploads nothing.
  - An object already archived for the run is never overwritten.

done_when:
  - `scripts/archive_raw_to_supabase.py` uploads `storage/raw/<market>/*.parquet` to
    `raw-archive:raw/<UTC run date>/<CI_JOB_ID or local>/<market>/<file>`, skips objects
    already there, creates the private bucket when missing, exits 0 without a key and 1 on
    any failure (tests, fake client, no network).
  - `.gitlab-ci.yml`: the archive step runs after `run_ingestion.py` and before dbt; on
    failure it leaves a marker and the run continues; the job's last step fails on the
    marker (test on the CI config).
  - `docs/project_context.md` / `docs/operations_guide.md` say where the archive is and how
    to read it; `docs/layering.md` records full rebuild, marts as `table`, no incremental.
  - `pytest tests/tooling` and `python scripts/bootstrap.py --verify` pass; review cycle run;
    MR opened. Not merged.

amendments:
  - Round 1: both PASS. Owner then chose layout option B (platform-reviewer follow-up: a
    date folder could mix two runs). Its other follow-ups are filed as #32.
  - Round 2 (delta): both PASS; one wording fix applied; follow-ups filed as #33.
