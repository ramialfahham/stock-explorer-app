# Task contract

objective: Item 2 of the 5-item portfolio-readiness list (from the prior 4-persona repo
  assessment): "alert on the scheduled pipeline job, checkpoint the ingestion loop." The
  scheduled `data-pipeline` CI job refreshes all card data twice a month (1st/15th, 06:00 UTC,
  unattended) and today has zero notification mechanism of any kind (confirmed by a full-file
  read of `.gitlab-ci.yml` and a repo-wide grep for slack/webhook/notify/alert/email/smtp/
  pagerduty -- every hit was an unrelated use of the same English word).
  `docs/operations_guide.md`'s own "Monitoring (v1)" section admits the current plan is a
  manual GitLab-UI spot-check. Because the schedule is infrequent, a failure can sit
  undiscovered for up to ~14 days -- that is the live risk this closes, not an imminent
  timeout: the one real scheduled run since all 9 markets went active (2026-09-01, pipeline
  `2808154517`, confirmed live via `glab api`) succeeded in 65 minutes against the 2h timeout,
  comfortable headroom.

  Full plan, including the options considered and declined with reasons, is in
  `C:\Users\Rami\.claude\plans\groovy-churning-scroll.md`, approved via `ExitPlanMode`. Two
  judgment calls were put to the owner explicitly and answered (not decided unilaterally):
  (1) alerting path -- GitLab's native "Pipeline emails" integration only (zero new dependency)
  over adding a Slack/webhook step (would need a new external service + secret) -- owner chose
  native only; (2) a finding from reading the real job's trace timestamps, that ingestion is
  only ~24 of the 65 minutes (37%) and the actual dominant, unguarded cost is
  `generate_assessments.py`'s AI-read step (~39 min, one Haiku call per changed card, no cap,
  will grow with card count) -- outside "checkpoint the ingestion loop" as scoped -- owner
  chose to flag it as a new backlog item rather than fold it into this task.

scope_paths:
  - docs/operations_guide.md (Monitoring section rewrite; ingestion skip-if-fresh note)
  - ingestion/yfinance/ingest.py (skip-if-fresh-today + incremental flush)
  - ingestion/main.py (`--force-refetch` flag, observability-only elapsed-time print)
  - tests/ingestion/test_ingest_resume.py (new)
  - .claude/active_work.md (close out item 2; log the generate_assessments.py backlog item;
    note the GitLab Pipeline-emails settings click-through as a pending owner action)
  - .claude/task/contract.md
  - .claude/task/review.md

decisions_reserved: none outstanding -- both judgment calls above were put to the owner and
  answered in-thread via `AskUserQuestion` during planning, not decided unilaterally. One
  implementation-level choice, disclosed as agent-executable, not a product/scope decision:
  the elapsed-time addition to `ingestion/main.py` is observability-only (a print after each
  market), not a hard stop/gate -- downgraded from an earlier draft's "stop early on budget
  exceeded" design after the real trace data showed ingestion isn't the phase actually at risk
  of the 2h ceiling, so a gating mechanism there would be solving the wrong part of the
  pipeline. Recorded in the plan file's "Explicitly declined" section.

done_when:
  - `ingestion/yfinance/ingest.py`: `_fetch_fundamentals` and `_fetch_daily_prices` skip any
    ticker/batch whose output already exists for that market and is marked fresh by a
    same-UTC-day `.checkpoint` marker file (not the parquet's own mtime -- see amendments),
    instead of unconditionally refetching; both flush (atomically, via `_atomic_write_parquet`)
    periodically during their loop, not only once at the very end. Pending tickers/batches are
    filtered before batching, not skipped per-batch, so an already-fetched ticker can never
    re-enter a batch. A new `force: bool` parameter (threaded from `ingest_market`) bypasses
    the freshness check entirely.
    `ingest_market()` no longer writes parquet itself -- that responsibility moves into the two
    fetch functions.
  - `ingestion/main.py`: new `--force-refetch` CLI flag threaded through to `ingest_market()`;
    a plain elapsed-time print after each market completes (observability only, no gating
    behavior, no new exit code path).
  - `tests/ingestion/test_ingest_resume.py`: covers (a) the flush happens during the loop, not
    only at a never-reached end -- proven by simulating a real process death (`KeyboardInterrupt`,
    not a plain `Exception`, since the existing per-ticker `except Exception` already swallows
    those and would not exercise this path) partway through, and asserting the on-disk file has
    exactly the rows fetched before that point; (b) a second call skips tickers/batches already
    present in a fresh-today file and only fetches the new ones; (c) a file backdated to
    yesterday is treated as stale and fully refetched; (d) `force=True` bypasses the skip even
    with a fresh-today file present; (e) no duplicate rows when batch boundaries shift between
    two same-day calls (the data-engineer-reviewer regression); (f) a same-day write from
    another script with no checkpoint marker is not mistaken for a completed run (the
    cto-reviewer regression); (g) `_atomic_write_parquet` leaves no temp file behind. Both
    `_fetch_fundamentals` and `_fetch_daily_prices` covered.
  - Mutation-tested: temporarily break the freshness check (e.g. always return "not fresh"),
    confirm the skip-specific tests fail, restore, confirm green again.
  - Full `pytest` suite green.
  - Manually verified: `python scripts/run_ingestion.py --market ch_smi --max-tickers 20
    --delay-seconds 1`, interrupted with Ctrl+C partway through, re-run identically -- second
    run's summary shows tickers skipped, finishes visibly faster, and
    `storage/raw/ch_smi/yf_fundamentals.parquet` ends with exactly 20 rows. `dbt build` (or
    `dbt parse`) against the result confirms the incrementally-written file is
    schema-identical to a normal single-shot write.
  - `docs/operations_guide.md`: "Monitoring (v1)" section rewritten with the exact GitLab
    Pipeline-emails settings path, what it covers, and what it does not (the dead-man's-switch
    gap -- the schedule silently never firing at all); a note added near the existing
    "run per-market if a full run hits rate limits" guidance explaining the new skip-if-fresh
    behavior and `--force-refetch`.
  - `.claude/active_work.md`: item 2 closed out; the `generate_assessments.py` runtime finding
    logged as a new, separate open item; the GitLab settings click-through noted as a pending
    owner action (not verifiable as done from this environment).
  - No em dash or en dash on any added line.

impact_map:
  - No user-visible change (ingestion/CI/ops-doc only, nothing in `frontend/`).
  - `ingestion/*` touched -- per `.claude/review_routing.json`, requires data-engineer-reviewer.
  - `tests/*` touched -- requires cto-reviewer.
  - scope-auditor always.

amendments:
- Round 1 of the three required reviewers found three real, evidenced defects, none a false
  alarm -- full findings and fixes in `review.md`:
  1. scope-auditor: 5 em dashes on added lines (4 in `docs/operations_guide.md`, 1 in the new
     test file's module docstring), breaking `done_when`'s explicit rule. Root cause: the
     em-dash scan run before staging piped `git diff` through a shell pipe into Python's
     stdin, which silently mis-decodes on this machine (confirmed: Python's default
     stdout/stdin encoding here is `cp1252`, not UTF-8) -- the scan reported "0 hits" on a
     diff that actually had 5. Fixed both the 5 characters and the scanning method (write the
     diff to a file first, `open(..., encoding="utf-8")` explicitly) -- re-scanned clean.
  2. data-engineer-reviewer: `_fetch_daily_prices`'s per-batch skip (`if already_fetched and
     all(t in already_fetched for t in batch_local)`) only skipped a batch when EVERY ticker
     in it was already covered. A batch mixing already-fetched and pending tickers (batch
     boundaries shift between two same-day runs whenever `--max-tickers` differs, or the
     constituent list changes) redownloaded the WHOLE batch, appending a second row per
     already-covered `(ticker, trading_date)` alongside `existing` -- would have failed
     `stg_yf__daily_prices`'s `dbt_utils.unique_combination_of_columns` test in the real
     pipeline. Fixed by filtering to `pending_tickers` before batching, not per-batch inside
     the loop, so an already-fetched ticker can never re-enter a batch at all. New regression
     test (`test_prices_no_duplicate_rows_when_batch_boundaries_shift`) added and
     mutation-verified: reintroduced the old per-batch check, confirmed the new test fails,
     restored, confirmed green.
  3. data-engineer-reviewer: both `_flush()` functions wrote `.to_parquet(output_path, ...)`
     directly -- a process kill mid-write could leave a truncated file whose mtime still reads
     as today, so the next run would trust it as fresh and crash reading it back
     (`pd.read_parquet` with no surrounding try/except), wedging every same-day retry until
     manually deleted. A real robustness regression for exactly the interruption case this
     feature exists to handle. Fixed with a shared `_atomic_write_parquet` helper (write to a
     same-directory temp file, `os.replace()` onto the final path) -- atomic on both POSIX and
     Windows, so `output_path` always holds either the last complete write or the new one,
     never a partial one. New test (`test_atomic_write_leaves_no_temp_file_behind`).
  All three independently re-verified after the fix, not just asserted: full `pytest` suite
  green (525 passed), both bug fixes mutation-tested, live re-run against real `ch_smi` data
  confirmed the skip path still works end to end, `dbt build` against the result passed all 8
  staging-layer tests again. Narrow re-checks dispatched to all three reviewers against the
  fixed code -- see `review.md`.
- cto-reviewer's round 1 (dispatched in parallel with the above, against the same pre-fix
  diff) independently found the same two data-engineer-reviewer defects -- strong convergent
  confirmation both were real, not one reviewer's misreading -- plus one genuinely new risk:
  `_is_fresh_today`'s file-mtime check has no protection against two OTHER in-repo scripts
  that write these exact raw parquet paths for unrelated reasons with no coordination
  (`scripts/seed_ci_raw_fixtures.py`, CI dbt fixtures; `scripts/backfill_fundamentals_parquet_schema.py`,
  a schema backfill). Confirmed safe inside CI (separate ephemeral containers, only
  `data-pipeline` runs real ingestion) but a real, undocumented local-dev collision: running
  either script against a real market_code the same UTC day as real ingestion would make the
  freshness check wrongly trust that script's write as a completed ingestion run. Fixed with a
  dedicated `.checkpoint` marker file (same directory, same basename plus `.checkpoint`) that
  only `_atomic_write_parquet` ever touches -- freshness is keyed on the marker's mtime, not
  the parquet's own, so a same-day write from either other script leaves no marker and the
  next real ingestion run correctly self-heals by fully refetching. New regression test
  (`test_fundamentals_ignores_a_same_day_write_from_another_script`), mutation-verified:
  reverted to mtime-based freshness, confirmed the new test fails (a fake fixture ticker
  leaked into the fetched set), restored, confirmed green. One narrower residual case
  documented, not silently claimed fixed: if one of those scripts overwrites the parquet file
  itself AFTER a real ingestion run already wrote both the file and the marker the same day,
  the marker still reads fresh even though the content is no longer what ingestion wrote -- an
  unusual, deliberate action sequence, not a normal workflow; noted in the code comment, with
  `--force-refetch` as the escape hatch if ever suspected.
  Re-verified live against the real (pre-marker) `ch_smi` files on disk: first run correctly
  treated them as not-fresh (no marker existed yet) and fully refetched -- self-healing, not a
  crash -- second run correctly skipped using the new marker; `dbt build` passed all 8 tests
  again.
- cto-reviewer's round 2 re-check FAILED on one finding, narrower than the above: the
  amendment two bullets up claimed the residual marker-collision case was "noted in the code
  comment and `docs/operations_guide.md`" -- true for the code comment
  (`_is_fresh_today`'s docstring), false for the ops guide, which only documented the forward
  direction (another script writes first) and never mentioned the reverse one (real ingestion
  writes first, another script overwrites the parquet later the same day, marker still reads
  fresh) or tied `--force-refetch` to it specifically. A record-accuracy gap, not a code
  defect -- the reviewer's own assessment agreed leaving the residual case unfixed (rather
  than extending the marker protocol into two unrelated, out-of-scope operator scripts) is
  sound; the finding was only that the disclosure trail overstated itself. Fixed by adding the
  missing paragraph to `docs/operations_guide.md`'s "Run ingestion locally" section, naming
  the exact scenario and pointing at `--force-refetch`.
