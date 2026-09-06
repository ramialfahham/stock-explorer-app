# Review

diff_sha256: d3b3dcb502c8725b613bbc2f13f78b522a298c10e7f954a049a7e39b86b6a2a5

## scope-auditor
Round 1 FAILED (five findings, all the same defect class)
- `docs/operations_guide.md:147,188,192,193` and `tests/ingestion/test_ingest_resume.py:2` --
  five em dashes on added lines, confirmed by grepping `[--]`-as-Unicode against the actual
  staged diff (not eyeballed), each one sitting on a `+` line. Breaks `done_when`'s explicit
  "No em dash or en dash on any added line." Root cause: the em-dash scan run before staging
  piped `git diff` through a shell pipe into Python's stdin, which silently mis-decoded on
  this machine (confirmed separately: this machine's default Python stdin/stdout encoding is
  `cp1252`, not UTF-8) -- the scan reported "0 hits" on a diff that actually had 5.

Everything else in round 1 held: every touched file is inside `scope_paths`; `impact_map`'s
reviewer claims (`ingestion/*` -> data-engineer-reviewer, `tests/*` -> cto-reviewer) verified
against the live `.claude/review_routing.json`, not trusted; `.claude/active_work.md` is
actually edited (not listed-but-unchanged); `decisions_reserved`'s "none outstanding" backed
by matching text found in the cited plan file, not a bare assertion; `.gitlab-ci.yml` invokes
`run_ingestion.py` with no flags, so the skip-if-fresh default genuinely governs the real
scheduled job.

Resolution: fixed both the 5 characters (replaced with `--`) and the scanning method itself
(write the diff to a file, `open(..., encoding="utf-8")` explicitly, never pipe through
stdin on this machine again) -- re-scanned the full diff clean with the corrected method.

Round 2 (narrow re-check of the em-dash fix, plus confirming the data-engineer-reviewer and
cto-reviewer fixes below didn't introduce new scope_paths/done_when drift):
VERDICT: PASS
risks_checked:
- Round-1's exact failure mode (silent `cp1252` stdin-decode corrupting the em-dash scan)
  recurring in round 2 -- ruled out by scanning with a direct UTF-8 file-open (no stdin pipe),
  proving the scan logic itself detects real hits via a synthetic positive-control patch, and
  cross-confirming with an independently-implemented ripgrep scan; both report 0 hits against
  a diff confirmed byte-identical (SHA256-matched) to the live staged diff.
- Scope creep from the two extra reviewer-driven fix rounds silently touching a file outside
  `scope_paths` -- checked `git diff --staged --name-status` directly: exactly the 6
  already-scoped files, nothing new.
- `done_when`'s marker-file and `pending_tickers`-filtering claims being narrative-only --
  checked both against the actual current source and against the diff's removed/added lines,
  confirming each is a real, structural change.
- `ingest_market()` "no longer writes parquet itself" -- confirmed both old `.to_parquet()`
  calls are removed lines in the diff and absent from the current function (not just one of
  the two).

Round 3 -- merge-commit review (`git merge main --no-ff` into this branch, after MR !100
independently merged first). Verified the conflict resolution itself is correct and not lossy:
compared the resolved `.claude/active_work.md` against both pre-merge tips (`git show
HEAD:...`, `git show main:...`) and confirmed every substantive fact from both sides survived;
confirmed `.claude/task/contract.md`/`review.md`'s `--ours` resolution is byte-identical to
this branch's own pre-merge content (`git diff HEAD -- ...` empty, nothing leaked from main);
confirmed the full staged set is exactly the 3 resolved files plus what the merge naturally
carries from `main` (`docs/data_contract.md`, `frontend/card_copy.py`, `frontend/card_ui.py`,
`frontend/styles.py`, `tests/frontend/test_card_ui.py`); zero em/en dash in the newly-written
merge prose; full suite 529 passed. Also confirmed `git diff main -- frontend/ tests/frontend/
docs/data_contract.md` is empty -- the files this merge routes to cto-reviewer/
equity-analyst-reviewer are genuinely byte-identical to what already passed those reviewers'
own independent cycles under MR !100 and is already live on `main`, not silently modified.

Raised, not decided unilaterally: `.claude/review_routing.json` has no carve-out for a merge
commit carrying byte-identical, already-reviewed, already-merged content -- re-interpreting the
routing rule for this case is a §6 owner call (`.claude/working-agreement.md`: "reinterpreting
or extending a rule to a case it didn't cover"), not something to resolve by analogy.
VERDICT: ESCALATE
questions:
- Dispatch cto-reviewer/equity-analyst-reviewer fresh on the byte-identical carried-over files
  anyway (matches routing literally, zero expected new findings, costs two agent rounds), or
  record the identity-check as grounds to skip the fresh dispatch this one time (saves the
  redundant cost, sets a precedent for agent-verified content-identity substituting for a
  routing-required reviewer with no exception written into `review_routing.json` itself)?

CPO ANSWER: skip the fresh dispatch, record the byte-identity verification as the reason --
see cto-reviewer's round 4 and the new equity-analyst-reviewer section below, both written as
explicit carryover determinations, not fresh reviews.

## cto-reviewer
Round 1 FAILED (dispatched in parallel with scope-auditor/data-engineer-reviewer, against the
same pre-fix staged diff -- noted mid-review that unstaged edits had begun appearing on disk
and correctly reviewed only what was actually staged, flagging that explicitly rather than
either ignoring or crediting the in-progress fixes)
- Independently found the SAME two defects data-engineer-reviewer found (strong convergent
  confirmation, not overlap noise): the per-batch skip only fires when every ticker in a batch
  is already covered, so a mixed batch redownloads and duplicates rows; and non-atomic
  `.to_parquet()` writes leave the checkpoint exposed to a truncated file on a mid-write kill,
  reproduced directly (`pyarrow.lib.ArrowInvalid: Parquet magic bytes not found in footer` on
  an unguarded `pd.read_parquet` read-back, propagating through `ingest_market()` and aborting
  every remaining market in that run too).
- One genuinely new finding: `_is_fresh_today`'s file-mtime check has no protection against
  two OTHER in-repo scripts that write these exact raw parquet paths for unrelated reasons,
  uncoordinated -- `scripts/seed_ci_raw_fixtures.py` (writes fake fixture rows into real
  `market_code` directories for CI dbt builds) and `scripts/backfill_fundamentals_parquet_schema.py`
  (rewrites the schema across every market). Traced `.gitlab-ci.yml` and confirmed no collision
  in CI itself (separate ephemeral containers, only `data-pipeline` runs real ingestion), but a
  real, undocumented local-dev collision: running either script against a real `market_code`
  the same UTC day as real ingestion would make the freshness check wrongly trust that
  script's write as a completed run.
- Also confirmed clean (traced, not assumed): `_normalize_price_frame` is never double-applied
  to already-normalized `existing` data (reproduced flush-then-reread-then-flush-again against
  the actual pinned pandas/pyarrow versions, dtype-identical to a true single-shot write);
  fundamentals' per-market scoping has no cross-market leakage (fresh locals every call, no
  module-level cache) and `force=True` genuinely bypasses both the read and the skip;
  `KeyboardInterrupt`'s use in the tests is genuinely necessary, not test-theater (traced
  `except Exception` in both fetch loops and `call_with_retry`'s own exception handling
  directly -- a plain `Exception` would have been silently swallowed and never exercised the
  crash-durability path); no secrets/scope issues, no em/en dash (checked before the em-dash
  fix landed on disk -- ran its own `pytest` (523 passed) and mutation test independently
  rather than trusting the contract's prose.

Resolution for the new finding: `.checkpoint` marker file (same directory, same basename plus
`.checkpoint`), written only by `_atomic_write_parquet` after the parquet write completes.
Freshness is now keyed on the marker's mtime, not the parquet's own -- a same-day write from
either other script leaves no marker, so the next real ingestion run correctly treats the file
as not-fresh and self-heals by fully refetching, rather than trusting corrupted-looking-fresh
content. New regression test
`test_fundamentals_ignores_a_same_day_write_from_another_script`, mutation-verified: reverted
to mtime-based freshness, confirmed the new test fails (a fake fixture ticker leaked into the
fetched set), restored, confirmed green. One narrower residual case documented, not silently
claimed fixed: a same-day write from another script AFTER real ingestion already wrote both
file and marker still reads fresh despite altered content -- an unusual, deliberate sequence,
not a normal workflow; noted in the code comment and `docs/operations_guide.md`, with
`--force-refetch` as the escape hatch if ever suspected.

Round 2 FAILED (one finding, narrower than round 1)
- `contract.md`'s amendments claimed the disclosed residual marker-collision case (real
  ingestion writes first, another script overwrites the parquet later the same day, marker
  still reads fresh) was "noted in the code comment and `docs/operations_guide.md`" -- true
  for the code comment (`_is_fresh_today`'s docstring), false for the ops guide, which only
  documented the forward direction (another script writes first, can't be mistaken for a
  completed run) and never mentioned the reverse one or tied `--force-refetch` to it
  specifically. An operator who hits this scenario and consults the ops guide (not the source)
  gets no warning it exists. A record-accuracy gap, not a code defect -- the reviewer's own
  assessment: leaving the residual case unfixed (rather than extending the marker protocol
  into two unrelated, out-of-scope operator scripts) is itself sound; the finding was only
  that the disclosure trail overstated where it's documented.

Everything else re-confirmed clean, independently: `pending_tickers` prefilter structurally
eliminates the batch-duplication bug (traced directly, no residual path); `_atomic_write_parquet`
has no unsafe window (marker write only starts after `os.replace` already completed
atomically, so an interruption leaves either no marker or one whose content is never read);
full suite 526 passed (twice, before and after the mutation test); mutation test independently
reproduced (reverted to mtime-based freshness, confirmed the regression test fails exactly as
predicted, restored, zero diff via `git status`, suite green again); em/en-dash scan via
explicit UTF-8 file-open (not stdin) over all 679 added lines, 0 hits, patch confirmed
byte-identical to a live `git diff --cached` taken during the review.

Resolution: added the missing paragraph to `docs/operations_guide.md`'s "Run ingestion
locally" section, naming the exact reverse-order scenario and pointing at `--force-refetch`.

Round 3 (narrow re-check of exactly this doc fix, nothing else in scope):
VERDICT: PASS
risks_checked:
- Disclosure content accuracy (the round-2 FAIL): read `docs/operations_guide.md` in full. The
  new paragraph sits immediately after the existing marker-mechanism paragraph in "Run
  ingestion locally," and covers all three required elements: trigger (running one of the two
  named scripts against a real market_code AFTER real ingestion already ran the same day),
  symptom (the marker still reads fresh but the parquet content is no longer what ingestion
  produced), and remedy (`--force-refetch`). Closes the exact gap round 2 found.
- No em/en dash introduced: scanned the full diff with an explicit UTF-8 file-open (not
  stdin-piped) across all added lines -- zero hits. Codepoint-checked the new paragraph's added
  lines specifically: every hyphen-like character is plain ASCII, matching the repo's
  double-hyphen convention.

Round 4 -- merge-commit carryover, not a fresh review (see scope-auditor's merge-review round
below for the full reasoning and the owner's decision). Merging `main` (carrying already-merged
MR !100) into this branch put `frontend/card_copy.py`, `frontend/card_ui.py`,
`frontend/styles.py`, and `tests/frontend/test_card_ui.py` into this commit's staged diff,
which `.claude/review_routing.json` routes to cto-reviewer. `git diff main -- frontend/
tests/frontend/` confirmed empty -- these four files are byte-identical to what MR !100's own
independent cto-reviewer pass already approved and what is already live on `main`. No fresh
dispatch: nothing to re-review that wasn't already reviewed under a different MR.
VERDICT: PASS
risks_checked:
- Byte-identity to already-reviewed, already-merged content, not assumed: `git diff main --
  frontend/ tests/frontend/` confirmed empty by scope-auditor's merge-review round, cross-
  checked here.
- This is a carryover determination, stated as such, not a claim that cto-reviewer freshly
  re-read this code in this commit.

## equity-analyst-reviewer
Merge-commit carryover, not a fresh review -- same reasoning as cto-reviewer's round 4 above.
`docs/data_contract.md` (routed to equity-analyst-reviewer) entered this commit's staged diff
only via merging already-merged MR !100 into this branch. `git diff main -- docs/data_contract.md`
confirmed empty -- byte-identical to what MR !100's own independent equity-analyst-reviewer
pass (4 rounds) already approved and what is already live on `main`.
VERDICT: PASS
risks_checked:
- Byte-identity to already-reviewed, already-merged content: `git diff main --
  docs/data_contract.md` confirmed empty.
- This is a carryover determination, stated as such, not a claim that equity-analyst-reviewer
  freshly re-read this file's financial content in this commit.

## data-engineer-reviewer
Round 1 FAILED (two findings)
- `ingestion/yfinance/ingest.py`'s `_fetch_daily_prices`: the per-batch skip (`if
  already_fetched and all(t in already_fetched for t in batch_local): continue`) only skipped
  a batch when EVERY ticker in it was already covered. A batch mixing already-fetched and
  pending tickers -- batch boundaries shift between two same-day runs whenever `--max-tickers`
  differs, or the constituent list changes -- redownloaded the WHOLE batch, appending a second
  row per already-covered `(ticker, trading_date)` alongside `existing`. Would fail
  `stg_yf__daily_prices`'s `dbt_utils.unique_combination_of_columns` test in the real
  pipeline, not a silent corruption but a real, non-obvious failure caused by the feature
  meant to make retries safer. The reviewer traced this to the exact scenario the contract's
  own manual-verification step demonstrates (a `--max-tickers 20` run, then a full run) and
  noted the existing test suite never exercised misaligned batch boundaries.
- Both `_flush()` functions wrote `.to_parquet(output_path, ...)` directly, no atomic
  temp-file-plus-rename. A process kill mid-write (the exact scenario this feature exists to
  handle) can leave a truncated file whose mtime still reads as today -- the next run's
  `_is_fresh_today` would trust it as fresh, then crash on the unguarded `pd.read_parquet`
  read-back, wedging every same-day retry until manually deleted. A real robustness
  regression: pre-diff, a mid-write crash left either an old complete file or nothing, never
  something that looked fresh but was actually corrupt.

Both independently confirmed correct (not disputed) by tracing the exact code paths named.

Resolution:
1. `_fetch_daily_prices` now filters to `pending_tickers = [t for t in tickers if t not in
   already_fetched]` BEFORE batching, not per-batch inside the loop -- an already-fetched
   ticker can no longer re-enter a batch at all, so the duplication can't occur structurally,
   not just by convention. New regression test
   `test_prices_no_duplicate_rows_when_batch_boundaries_shift`, mutation-verified: reintroduced
   the old per-batch check, confirmed the new test fails (`assert "AAA" not in calls` ->
   `AssertionError: assert 'AAA' not in ['AAA', 'BBB', 'CCC', 'DDD', 'EEE']`), restored,
   confirmed green.
2. New shared `_atomic_write_parquet(frame, output_path)` helper (temp file in the same
   directory, `os.replace()` onto the final path -- atomic on both POSIX and Windows), used by
   both `_flush()` functions. New test `test_atomic_write_leaves_no_temp_file_behind`.

Round 2 (narrow re-check of exactly these two fixes, plus the marker mechanism cto-reviewer
added independently, nothing else in scope):
VERDICT: PASS
risks_checked:
- Cross-run duplicate rows: traced every path that appends to `frames` (single-ticker and
  multi-ticker branches) -- both index exclusively off `batch_local`, a slice of
  `pending_tickers` computed once before the batch loop starts; `existing` is loaded once and
  never re-appended to. Duplication structurally excluded, not just less likely. Confirmed live
  via `test_prices_no_duplicate_rows_when_batch_boundaries_shift`.
- Atomic write / crash safety: `_atomic_write_parquet` writes to a same-directory temp file,
  `os.replace()`s it onto `output_path` (atomic on POSIX and Windows), only then touches the
  marker. Ran the crash-simulation and no-temp-file-leftover tests live -- passed.
- Marker/parquet disagreement window (new since round 1): `_is_fresh_today` reads only the
  marker's mtime, never its content, so a torn marker write is inert; the marker is written
  strictly after the parquet swap succeeds, so "marker exists, dated today" structurally
  implies a complete parquet write landed today, never a torn one. Worst case is staleness
  (self-heals next run), not corruption. Also checked every glob-based raw-parquet scan in the
  repo (`backfill_fundamentals_parquet_schema.py`, `check_pipeline_completeness.py`,
  `raw_parquet_union.sql`) -- none can sweep up the new `.checkpoint`/`.tmp-{pid}` sidecar
  files as data.
- Schema/dtype compatibility on the genuinely new path (`_fetch_fundamentals`'s resume branch
  round-tripping `existing.to_dict(orient="records")` and remixing with freshly-fetched rows):
  wrote and ran a standalone script against the real pinned pandas/pyarrow with real
  `datetime.date` values, round-tripped and remixed exactly as the resume path does -- dtype
  stayed `object`/`datetime.date` across two full write-read cycles, no drift.
- `python -m pytest tests/ingestion/test_ingest_resume.py -v` run for real: 11 passed.
- Ingestion contract ("no business logic... raw fields only"): the marker's content is
  write-only, nothing ever reads it back (only mtime is consulted), and it's structurally
  excluded from dbt ingestion (exact-literal-filename reads, never a glob). Pure I/O
  bookkeeping, not derived logic.

## Full suite
526 passed (523 baseline + 3 new regression tests: batch-duplication, atomic-write-no-leftover,
same-day-write-from-another-script). Re-run after every fix round.

## Mutation tests
- Freshness check (`_is_fresh_today` forced to always return `False`): both
  `test_fundamentals_skip_if_fresh_today` and `test_prices_skip_if_fresh_today` failed as
  expected via the planted `AssertionError` in the fake fetch functions; all other tests
  unaffected. Restored, 523 passed.
- Batch-duplication fix (old per-batch skip check reintroduced):
  `test_prices_no_duplicate_rows_when_batch_boundaries_shift` failed as expected
  (`assert "AAA" not in calls` -> `AssertionError`). Restored, green.
- Marker-based freshness fix (reverted to mtime-based freshness on the parquet file itself):
  `test_fundamentals_ignores_a_same_day_write_from_another_script` failed as expected (a fake
  "ZZZ" fixture ticker leaked into the fetched set). Restored, 526 passed.

## Manual verification
Real `ch_smi` data, not simulated. Pre-marker files already on disk from earlier runs: first
run after the marker fix landed correctly treated them as not-fresh (no marker existed yet)
and fully refetched (20/20 ok, 0 skipped, ~65s) -- self-healing, not a crash. Marker files
(`yf_daily_prices.parquet.checkpoint`, `yf_fundamentals.parquet.checkpoint`) confirmed written
alongside the parquet files. Immediate re-run: ~7s, 20/20 skipped, identical row counts.
`dbt build --select stg_yf__daily_prices stg_yf__fundamentals` against the result: 10/10 (2
view models + 8 data tests, including the uniqueness constraints on
`(market_code, ticker, trading_date)` and `(market_code, ticker, snapshot_date)` that the
duplication bug would have failed) passed both before and after every fix round. No stray
`.tmp-*` files left in `storage/raw/ch_smi/`; `git status` confirms the new `.checkpoint`
files are covered by the existing `storage/raw/*` gitignore pattern, no gitignore change
needed.
