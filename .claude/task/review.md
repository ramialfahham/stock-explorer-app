# Review

diff_sha256: b5417b75378741ed74af23177091b901a389024467b6395665c16fa46c6c2a65

Three reviewers, by routing: scope-auditor (`always`), data-engineer-reviewer (`ingestion/*`),
cto-reviewer (`tests/*`). Four rounds.

## What shipped

`_fetch_daily_prices` returns `(frame, stats)` instead of a bare frame, carrying
`price_batches`, `price_batches_failed`, `price_batches_empty` and `price_tickers_missing` --
the shape `_fetch_fundamentals` beside it already used. `ingest_market` merges them into its
summary; `ingestion/main.py` prints them and writes a stderr warning naming the affected
markets when a batch failed.

The run does NOT fail. That reverses the first answer, and the reversal is the substance of this
review.

## The decision, asked twice

The owner was first asked "should a failed price batch fail the run" and answered yes, on two
premises the author supplied without checking. Both were false:

- **Nothing reads prices.** `stg_yf__daily_prices` is `ref`'d by no model. No price column
  reaches the mart, the export or a card. scope-auditor found this; cto and data-engineer each
  re-derived it independently.
- **`call_with_retry` retries rate limits only.** `rate_limit.py` re-raises unless
  `is_rate_limited(exc)`, so a connection reset or timeout reaches the failure path on attempt 0.
  The contract had claimed retries were exhausted. data-engineer and cto both caught it.

Corrected blast radius: `run_ingestion.py` is step 2 of 10 in `data-pipeline`'s plain `script:`
list with no `retry:`, and `storage/` has no `cache:`. A non-zero exit would skip `dbt build`,
all three gates, the Supabase export and the assessments, and a re-run would refetch ~1,190
tickers. One unretried blip in ~25 batch calls would have cost a whole twice-monthly refresh, to
protect data with no consumer.

Put back to the owner with the correction. Answer on the corrected facts: report, do not gate.

## Verification

`pytest tests/ -q` 625 passed. 362 added lines, zero em-dashes, zero over 100 characters.

Mutation-tested. cto ran 20 mutants, each proving it applied (occurrence count, sha256 before
and after, on-disk readback) before its result was trusted -- after an earlier mutation in this
task silently failed to apply and reported a false pass. All killed except two that exist
verbatim at HEAD. The kills include deleting the stderr warning, un-naming the market,
redirecting it to stdout, cross-swapping two counters, and renaming a counter in `ingest.py`
alone, which previously passed every test and would have raised `KeyError` in production after a
24-minute ingest.

## scope-auditor

Failed rounds 1 and 2. Found that the gate's blast radius was never put to the owner, that
"re-run before trusting downstream output" was false because nothing consumes prices, and that
the branch gated the feed affecting no shipped output while leaving ungated the one that decides
whether a card exists. Then found four test docstrings still describing the reversed design.

Withdrew its own date-stamp finding after checking four precedents: "My original reading was too
strict."

VERDICT: PASS

## data-engineer-reviewer

Failed rounds 1, 2 and 3. Established that `call_with_retry` retries rate limits only. Found the
failure message claimed the parquet was partial and freshly stamped, which is false when every
batch fails, because `_flush` is never reached. Then found the corrected comment had
over-corrected into contradicting its own file: it declared `price_tickers_missing` blind to
per-symbol loss while `ingest.py` increments it on exactly that, asserted by a test in the same
diff.

VERDICT: PASS

## cto-reviewer

Failed round 1 on the retry premise and on four surviving mutants. Verified the yfinance claim
against the pinned source rather than from memory, and recovered dangling blobs to prove no
executable drift between rounds instead of accepting the author's summary.

Answered the question it was asked directly: the shipped warning is stderr in a green single-job
log, so "make failures visible" ships as "make them greppable, if someone already suspects a
problem and goes looking". It judged this not a defect in the diff but a gap in the menu the
owner was offered.

VERDICT: PASS

## Owner decisions

One taken, twice, recorded in `contract.md` with both answers and the correction between them:
report, do not gate.

Three `NOT DONE, FLAGGED`, none decided here:

- The counters cannot see the loss yfinance's own failure path produces. A failed symbol is
  concatenated back as an all-NaN OHLCV block, so the column is present and the symbol counts as
  retrieved; `_yfinance_staging.yml` puts no `data_tests` on OHLCV at all. Closing it is a
  data-contract change, and a bare `not_null` on `close` is the wrong instrument because
  legitimate NaN exists (non-trading days, halted sessions, mid-window listings).
- Nothing ENFORCES the "nothing reads prices" precondition the whole decision rests on. It is a
  comment. `ref('stg_yf__daily_prices')` would make it wrong silently.
- "Report loudly" buys less than it sounds, and the owner was not told so when choosing. A
  separate CI job with `allow_failure: true` surfaces a visible pipeline warning without gating.
  No existing repo mechanism does this, so it is a new workflow step. The choice was put as
  gate-or-report because the author did not know the third option existed.

## Follow-ups, disclosed not fixed

- `done_when` enumerates three counters where four ship. A minimum, not an inventory
  (scope-auditor, not raised under the stopping rule).
- The contract cites `ingest.py:238-244`; the block starts at 237. Names the right code.
- For a batch of exactly one ticker a failure degenerates to `downloaded.empty` and is counted as
  `price_batches_empty`, not as an invisible NaN block. The comment describes the multi-symbol
  case, which is what `BATCH_SIZE` produces in production (cto).
- Nothing couples the `ingest.py` comment's `yfinance==1.3.0` citation to `requirements.txt`, so
  a version bump fires nothing. cto judged naming the version the LOWER-liability option, since
  unfalsifiable prose rots invisibly while a named version makes staleness self-announcing.
