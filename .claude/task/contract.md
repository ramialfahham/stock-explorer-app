# Task contract
> DISPOSABLE. **Owns:** THIS task's objective, `scope_paths`, reserved decisions and
> `done_when`.
> **Never:** anything that outlives the task. Overwritten by the next task.

objective: `scripts/generate_assessments.py` writes to Supabase like `export_to_supabase.py`
  but has no `--target dev`, so a change to it can only be tried against production. Give
  it the same flag, the same client wiring, and a place in `dev-schema-check`. Issue #4,
  part 3.

scope_paths:
  - scripts/generate_assessments.py
  - tests/tooling/test_generate_assessments.py
  - .gitlab-ci.yml
  - docs/supabase_setup.md
  - docs/operations_guide.md
  - .claude/task/contract.md
  - .claude/task/review.md
  - .claude/active_work.md

decisions_reserved:
  - Zero spend, standing owner rule: the `dev-schema-check` step runs the script with
    `ANTHROPIC_API_KEY=` (empty), so the manual button writes verdicts only and never
    generates a prose read. Empty is treated as absent (the script already skips on a falsy
    key; a test now pins it). Recorded because it is a CI step; the button stays `web` only,
    manual, so no run cadence changes.

done_when:
  - `--target {prod,dev}` on `generate_assessments.py`, default prod; the client is built
    with `SyncClientOptions(schema=...)` exactly as the export does; the upsert line names
    the schema.
  - Tests: dev passes schema "dev"; default passes "public"; the options object is the sync
    variant (has `.storage`); an empty `ANTHROPIC_API_KEY` skips the reads and never
    constructs an Anthropic client.
  - `dev-schema-check` runs the script after the export with the empty key.
  - `docs/supabase_setup.md` §3b and `docs/operations_guide.md` say three writers, the
    exposed-schema step applies to the two PostgREST ones, and the empty-key prefix is
    explained.
  - `pytest tests/ -q` green; `.gitlab-ci.yml` parses.

impact_map: One flag on one script (default unchanged, so the scheduled `data-pipeline`
  behaves as before); one added step in a manual, web-only CI job; two docs.
