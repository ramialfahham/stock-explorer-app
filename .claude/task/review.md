# Review

> DISPOSABLE. **Owns:** THIS task's reviewer verdicts and the staged-diff hash they were
> given against.
> **Never:** a rule. Overwritten by the next task.

diff_sha256: fd95b576c7b89f79eb13eaf2355e8db975ad2f4e9f1fe1e164909f8933276a12

Three reviewers, by routing: scope-auditor (`always`), cto-reviewer (`scripts/*`, `tests/*`),
equity-analyst-reviewer (`docs/data_contract.md`). Two rounds.

## What shipped

A live data-integrity bug: `scripts/generate_assessments.py`'s final Supabase upsert sent all
records (some carrying `ai_read`/`read_model`, some omitting them to preserve the stored
value) in one PostgREST bulk upsert call. PostgREST computes that call's `columns` query
parameter as the union of keys across every record in it, so a record omitting a column
present elsewhere in the same call has it explicitly nulled, not left untouched -- confirmed
against production (the 2026-09-15 scheduled run's own log said `carried=853`, yet 839 of
those rows came out of that exact run with `ai_read` null) and against the installed
`postgrest` package's own source. New `_upsert_records()` groups every upsert call by each
record's exact set of present keys before chunking, so no call ever mixes shapes.

This is very likely the actual root cause of open item 8 (the AI-read step's ungoverned
runtime cost): a clobbered "carried" card looks read-null next run, so `attach_reads()`
treats it as needing a fresh read even though its `input_hash` never changed.

A second, related bug found in the same investigation and fixed here:
`_fetch_existing_assessments()`'s unranged select silently returned only PostgREST's default
row cap (1000 of 1045 real rows today), so cards past that cutoff never appeared in the
"already has a read" lookup at all. Now paginated via `.range()`.

`docs/data_contract.md` updated: the mechanism and its production evidence, and a note that
the ~839 already-clobbered rows self-heal automatically (`attach_reads()` regenerates
whenever `ai_read` is falsy, independent of `input_hash`) -- no separate cleanup needed once
this ships.

726 tests (was 721 before this session's other changes; net +5 for this task: two
clobbering-behavior tests -- one pinning the OLD broken shape via a fake that accurately
models PostgREST's real union-of-keys semantics, one proving the fix -- one batching test,
two pagination tests).

The `--max-reads` cost-cap work that was in progress when this was discovered is parked,
unmerged, on branch `pipeline/ai-read-max-reads-cap` (stashed) -- resumes after this merges.

## Round 1

cto-reviewer: FAIL. `test_fetch_existing_assessments_paginates_past_the_default_row_cap`
didn't actually prove pagination was needed -- the fake returned the full unclipped list
whenever `.range()` wasn't called, so the test would still pass against a reversion. Fixed:
the fake now caps an unranged select at 1000 rows (`_POSTGREST_ROW_CAP`), matching
PostgREST's real default, independent of what the client code asks for. Also: an unused
`monkeypatch` test parameter removed.

equity-analyst-reviewer: FAIL. Two findings. (1) `.claude/task/contract.md` said "83.9% of
rows (839 of 1045)" -- wrong arithmetic (839/1045 = 80.3%; 83.9% was 839/1000, the OLD row
cap, the very bug being fixed). Fixed. (2) `docs/data_contract.md` didn't say what happens to
the already-clobbered rows going forward, and didn't reconcile the bug's actual scale
(~80% of cards, for a real stretch of time) against the file's own framing of ai_read-absence
as a rare, self-correcting edge case. Fixed with a new sentence stating both the scale and
the self-healing mechanism, with the code path named.

scope-auditor: PASS.

Independently, the orchestrating session mutation-tested the round-1 pagination fix itself
(temporarily reverted `_fetch_existing_assessments()` to the old single unranged select,
confirmed the test failed as expected, restored the fix, reconfirmed the full suite green)
before re-dispatching reviewers.

## Round 2

All three: PASS. cto-reviewer independently re-ran the mutation test and confirmed the
fake's truncation change doesn't affect any other test (all other `_FakeSupabase` call
sites use small fixtures, well under the new 1000-row simulated cap). equity-analyst-reviewer
independently traced `attach_reads()`'s regenerate condition in the code to confirm the
self-healing claim is actually true, not just asserted.

## scope-auditor

VERDICT: PASS

## cto-reviewer

VERDICT: PASS

## equity-analyst-reviewer

VERDICT: PASS

## Owner decisions

Investigate and fix this root cause now, before resuming the parked `--max-reads` cap work --
owner's call, in chat, 2026-09-15.
