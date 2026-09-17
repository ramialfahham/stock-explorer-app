# Task contract
> DISPOSABLE. **Owns:** THIS task's objective, `scope_paths`, reserved decisions and
> `done_when`.
> **Never:** anything that outlives the task. Overwritten by the next task.

objective: Refs #22. Adds explicit per-card logging to `attach_reads()` in
  `scripts/generate_assessments.py`, for every card it processes, not just failures.
  Today a silent success and a card that was never even bucketed look identical in the
  job log -- that gap is what made diagnosing issue #22 (a card stuck on the fallback
  read with zero log trace across two full runs) require a live manual repro instead of
  just reading the log. This closes that gap for future cases: every record now prints
  exactly one line naming its ticker and outcome (carried, generated, failed, rejected,
  capped, or no matching mart row), regardless of which bucket it lands in.

scope_paths:
  - scripts/generate_assessments.py
  - tests/tooling/test_generate_assessments.py
  - .claude/task/contract.md
  - .claude/task/review.md

decisions_reserved: none -- this is exactly what issue #22's own "what exactly" item 1
  asked for, confirmed directly in chat ("add the per-card logging").

done_when:
  - Every record `attach_reads` sees prints exactly one line: which bucket it landed in
    (carried / generated / failed / rejected / capped / no mart row) and its ticker.
  - Existing failure/rejection log wording is unchanged (tests assert on exact substrings
    like "read failed for", "malformed tool payload") -- only new lines are added, no
    existing ones reworded.
  - `pytest tests/tooling/test_generate_assessments.py -q` passes, including new coverage
    for the previously-silent paths (carried, generated, capped, no-mart-row).
  - `python scripts/check_no_em_dash.py` passes.

impact_map: one function's logging in one script, plus its tests. No behavior change to
  which cards get a read, what gets upserted, or the CI job's exit code -- purely
  observability for the next time a card like #22's ends up unexplained.
