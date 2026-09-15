# Task contract
> DISPOSABLE. **Owns:** THIS task's objective, `scope_paths`, reserved decisions and
> `done_when`.
> **Never:** anything that outlives the task. Overwritten by the next task.

objective: `generate_assessments.py`'s AI-read step is the scheduled pipeline's dominant
  runtime cost. Its actual root cause (a batch-upsert bug nulling most "carried" cards' reads
  every run, making nearly the whole deck look like it needed regeneration) was found and
  fixed separately (MR !149). This task resumes the work that was in progress when that was
  found: a per-run cap on new Claude calls (`--max-reads`), as a bound for whatever real cost
  remains once the fix's effect is measurable, and because the deck keeps growing as more
  markets are onboarded regardless. Owner decided (in chat, 2026-09-15): resume this now
  rather than wait for the next scheduled run (2 weeks away) to re-measure cost first -- the
  cap's own correctness doesn't depend on that measurement.

scope_paths:
  - scripts/generate_assessments.py
  - tests/tooling/test_generate_assessments.py
  - docs/data_contract.md
  - docs/context_budget.yml
  - .claude/task/contract.md
  - .claude/task/review.md
  - .claude/active_work.md

decisions_reserved:
  - Cap shape (per-run count cap, over a time budget or visibility-only): owner's call,
    2026-09-15, per-run cap chosen.
  - The actual `--max-reads` value used in the `data-pipeline` CI job (`.gitlab-ci.yml`) is
    NOT set by this task -- stays unbounded (unchanged default) until the owner picks a
    number, ideally after seeing one clean scheduled run's real generated/carried/capped
    counts post-!149.

done_when:
  - `attach_reads()` takes `max_reads: int | None = None` (unbounded default -- omitting
    `--max-reads` changes nothing).
  - Cards with no stored read (new, or a stored `ai_read` that is empty) are filled before
    cards that only need a refresh; both buckets keep the records' own relative order.
  - A card the cap doesn't reach this run, or whose generation attempt fails, has any stale
    stored read explicitly cleared (not left showing under this run's fresh verdict/numbers)
    -- `_clear_stale_read_if_present()`.
  - New `capped` counter in the returned summary dict and the printed CLI summary line.
  - `--max-reads` CLI flag threads through `main()` end to end; a negative value is rejected
    at the CLI (`parser.error`) and clamped defensively inside `attach_reads()` itself.
  - Mutation-proof: input order opposite of expected priority still gives the no-stored-read
    candidate the slot; a naive list-order implementation would fail this test.
  - A `_clear_stale_read_if_present()`-nulled (capped/failed) record and a genuinely generated
    record, fed through `_upsert_records()` together, land in the same upsert call and neither
    clobbers the other -- the one composition path between this task and MR !149 that neither
    task's own review covered on its own.
  - `pytest tests/ -q` green.

impact_map: `scripts/generate_assessments.py` only -- no schema change, no new dependency.
  The `data-pipeline` CI job's actual behavior is unchanged until the owner sets
  `--max-reads` there.
