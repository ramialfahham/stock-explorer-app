# Task contract
> DISPOSABLE. **Owns:** THIS task's objective, `scope_paths`, reserved decisions and
> `done_when`.
> **Never:** anything that outlives the task. Overwritten by the next task.

objective: While building a per-run cap on the AI-read step's cost (open item 8), a read-only
  production check surfaced something bigger: 80.3% of `card_assessments` rows (839 of 1045)
  have a NULL `ai_read` right now. The scheduled run's own log for 2026-09-15 reported
  `generated=165 carried=853 failed=25` -- 853 cards `attach_reads()` deliberately left
  untouched to PRESERVE their stored read -- yet 839 rows came out of that exact run with
  `ai_read` null. Root cause, confirmed against the installed `postgrest` library source: a
  bulk upsert call's `columns` query parameter is the union of keys across every record in
  that ONE call; a "carried" record omitting `ai_read` shares a call with a "generated"
  record that includes it, and PostgREST nulls the omitted column instead of leaving it
  untouched. This also explains open item 8 itself: a clobbered "carried" card looks
  read-null next run, so `attach_reads()` treats it as needing a fresh read even though its
  `input_hash` never changed -- the AI-read step's ungoverned cost is very likely mostly this
  bug, not genuine regeneration need. A second, related bug found in the same investigation:
  `_fetch_existing_assessments()`'s unranged select silently returns only PostgREST's default
  row cap (1000 of 1045 real rows today), so cards past that cutoff never appear in the
  "already has a read" set at all.

  Owner decision (in chat, 2026-09-15): investigate and fix the root cause now, before
  resuming the `--max-reads` cap work (parked on branch `pipeline/ai-read-max-reads-cap`,
  stashed -- not part of this task).

scope_paths:
  - scripts/generate_assessments.py
  - tests/tooling/test_generate_assessments.py
  - docs/data_contract.md
  - .claude/task/contract.md
  - .claude/task/review.md
  - .claude/active_work.md

decisions_reserved: none -- a bug fix restoring the pipeline's own already-documented,
  already-relied-upon contract ("a re-run never clobbers a stored read"), not a new decision.

done_when:
  - New `_upsert_records()` groups every upsert call by a record's exact `frozenset` of
    present keys before chunking into `batch_size`, so no single upsert call ever mixes a
    "carried" (omits `ai_read`/`read_model`) record with a "generated" one (includes them).
  - `_fetch_existing_assessments()` paginates via `.range()` past `_SELECT_PAGE_SIZE` (1000)
    instead of a single unranged select.
  - Regression test proves the OLD single-call shape actually clobbers, using a fake that
    accurately models PostgREST's real union-of-batch-columns semantics (not just asserting
    the new code's own internal behavior) -- so the test would fail against a reversion to
    the old code, not just against an obviously-different one.
  - `pytest tests/ -q` green.

impact_map: `scripts/generate_assessments.py` only -- no schema change, no new dependency.
  Fixes a live data-integrity defect in the `card_assessments` write path; does not itself
  change how many Claude API calls a run makes (that's the parked `--max-reads` task) beyond
  whatever calls this bug was causing to be unnecessary.
