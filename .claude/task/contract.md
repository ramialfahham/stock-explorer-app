# Task contract

objective: Make price-ingestion failures visible instead of silent. Issue #9 finding A3.

  `_fetch_daily_prices` catches a failed batch, prints a warning and `continue`s
  (`ingestion/yfinance/ingest.py:238-244`). It returns only a DataFrame, so nothing downstream
  can tell a complete fetch from a partial one. The fundamentals path already does this
  correctly: `_fetch_fundamentals` returns `(frame, stats)` and its counts reach the per-market
  summary.

  The consequence is not a lost warning in a log. `_flush` writes the partial result over the
  previous complete file through `_atomic_write_parquet`, giving it a fresh mtime and a fresh
  `ingested_at`, so `dbt source freshness` (warn 20d / error 30d) reads green while part of the
  universe has silently lost its prices. Eligibility is fundamentals-driven, so the completeness
  and baseline gates do not catch it either. No `check_*` script mentions prices at all.

scope_paths:
  - ingestion/yfinance/ingest.py
  - ingestion/main.py
  - tests/ingestion/test_ingest_resume.py
  - tests/ingestion/test_ingest_failure_reporting.py
  - .claude/task/contract.md
  - .claude/task/review.md
  - .claude/active_work.md

decisions_reserved:
  - MAKING A PARTIAL PRICE FETCH FAIL THE RUN changes what the scheduled pipeline treats as
    success: a job that previously exited 0 with missing prices would now exit non-zero. That is
    the point of the fix, but it is a CI behaviour change, and `ingestion/main.py` carries a
    deliberate "observability only -- not a gate" decision for the elapsed timer, so the file
    has precedent in the other direction. OWNER DECISION: fail the run, or surface the counts
    and leave the exit code alone.
    ASKED AND ANSWERED TWICE. The first answer was FAIL THE RUN, given on two premises the
    author supplied and had not checked. Both are false:
      * Prices have NO downstream consumer. `stg_yf__daily_prices` is defined and never selected
        from anywhere in `dbt_analytics/models`, and no price column reaches the mart, the export
        or a card. Losing prices costs nothing shipped today.
      * `call_with_retry` retries rate limits ONLY (`rate_limit.py`: it re-raises unless
        `is_rate_limited(exc)`). Connection resets, timeouts and parse errors reach the failure
        path on attempt 0, unretried. The author's impact_map claimed retries were exhausted.
    Corrected blast radius: `run_ingestion.py` is step 2 of 10 in `data-pipeline`'s plain
    `script:` list with no `retry:`, so a non-zero exit skips `dbt build`, all three gates, the
    Supabase export and the assessments. `storage/` has no `cache:`, so a re-run refetches
    ~1,190 tickers. One unretried blip in ~25 batch calls would cost a whole twice-monthly
    refresh.
    OWNER ANSWER on the corrected facts: DO NOT GATE. Count and report loudly; leave the exit
    code alone. The rejected alternative was keeping the gate. The recommendation was the
    author's, presented with the correction.
    Recorded so it is not re-derived: this is safe ONLY while nothing reads prices. A price
    column gaining a consumer makes the gate question live again, which is why the reason sits
    in the code beside the check.

  - NOT DONE, FLAGGED: the counters cannot see the loss yfinance's OWN failure path produces.
    `_download_one` catches a failed symbol and concatenates `utils.empty_df()` back in under
    that ticker's key (yfinance 1.3.0, `multi.py`), so the column is present and all-NaN rather
    than absent. `price_tickers_missing` tests column presence only, so those rows are written
    and counted as retrieved, and `_yfinance_staging.yml` puts no `data_tests` on OHLCV at all.
    Closing it means testing those columns, which is a data-contract change (§6) and not a
    drop-in: a bare `not_null` on `close` fires on legitimate NaN (non-trading days in the
    lookback window, halted sessions, a mid-window listing), so it needs a designed bound such
    as an all-NaN share per ticker. It would also gate a model with no consumer, which is the
    opposite of the decision above.

  - NOT DONE, FLAGGED: nothing ENFORCES the precondition the decision above rests on. "Nothing
    reads prices" is a comment. The day someone writes `ref('stg_yf__daily_prices')` the
    reasoning becomes wrong and no test, gate or reviewer fires. Closing it needs a new
    mechanism, so it is the owner's call.

  - NOT DONE, FLAGGED, and the owner was NOT told this when choosing: "report loudly" buys less
    than it sounds. The warning is stderr in a single-job pipeline whose log is not read while
    the job is green -- cto-reviewer's words, "make them greppable, if someone already suspects
    a problem and goes looking". A genuinely louder non-blocking form exists: a separate CI job
    with `allow_failure: true`, which GitLab surfaces as a visible warning on the pipeline
    without gating it. No existing repo mechanism does this (every `check_*` runs inline in
    `data-pipeline` and gates everything after it), so it is a new workflow step and §6. The
    choice was put as gate-or-report; the third option was not on the table because the author
    did not know it. The counters shipped here are the prerequisite for any alerting built
    later, so this is groundwork either way.

done_when:
  - `_fetch_daily_prices` returns `(frame, stats)` carrying batches attempted, batches failed and
    tickers missing, mirroring `_fetch_fundamentals`' existing shape.
  - `ingest_market` merges those into its summary and `ingestion/main.py` prints them beside the
    fundamentals counts.
  - A failed batch is provably non-silent: tests inject a batch failure and assert the counts
    reach `ingest_market`'s summary and the operator warning, mutation-verified. The summary's
    whole key set is pinned, because `ingestion/main.py` indexes every counter by name and a
    rename would otherwise pass every test and raise `KeyError` after a ~24-minute ingest.
  - A clean run prints nothing on stderr, so the warning stays worth reading.
  - Resume behaviour is unchanged. A partial file stays a usable checkpoint that a re-run
    completes, which is what `_is_usable_checkpoint` and the pending-ticker filter exist for.
    This task makes failure visible; it does not stop the write.
  - `pytest tests/ -q` green.

impact_map: `ingestion/` only. No dbt model, no export, no frontend, no schema, and no exit
  code changes: a run that would have passed still passes. The only behaviour change is four
  counters in the per-market summary line and a stderr warning when a batch failed. Nothing
  consumes the summary dict programmatically (`ingestion/main.py` is its sole reader), so the
  added keys cannot break a caller.
