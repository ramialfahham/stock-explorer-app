# Task contract
> DISPOSABLE. **Owns:** THIS task's objective, `scope_paths`, reserved decisions and
> `done_when`.
> **Never:** anything that outlives the task. Overwritten by the next one.

objective: Stop serving stale cards silently when fundamentals fail to fetch. A ticker whose
  fundamentals fetch fails has no row in the parquet, so no row in the mart; its previous
  snapshot stays in the deck with an older `As of` date and no sign a refresh was attempted.
  The baseline gate fires
  only above a 15% eligible-count drop (warns above 5%), so failures under that line reach the
  reader unflagged.

  Fundamentals are the sole input to `is_card_eligible`; prices (issue #9 A3, MR !118) have no
  consumer. That is why this feed gates where prices did not.

scope_paths:
  - ingestion/yfinance/ingest.py
  - ingestion/main.py
  - tests/ingestion/test_ingest_resume.py
  - tests/ingestion/test_ingest_failure_reporting.py
  - docs/data_contract.md
  - .claude/task/contract.md
  - .claude/task/review.md
  - .claude/active_work.md

decisions_reserved:
  - Gate or tolerate: asked with two paths (strict: any failure fails the run; tolerant: fail
    above 5% of a market's tickers, continue below with the failed tickers named on stderr).
    Owner chose tolerant. The 5% is the baseline gate's `warn_drop_fraction`, pinned equal by
    a test. Same number, different denominator: that gate measures a drop in eligible count,
    this one fetch failures over all requested tickers, so 5% of fetches can be more than 5% of
    a deck.
  - A failed run skips the export, which keeps the last good Supabase snapshot. That is the
    contract's existing policy for a failed gate, not a new one.

done_when:
  - `_fetch_fundamentals` returns the failed tickers by name, not only a count, and
    `ingest_market` carries them in its summary.
  - `ingestion/main.py` exits 1 when any market's `fundamentals_failed` exceeds 5% of its
    `tickers_requested`, naming the market and the count on stderr; exits 0 below that,
    naming the failed tickers on stderr so the stale cards are findable. Exactly 5% passes.
  - Mutation-proven in `tests/ingestion`: one over the line fails, at the line passes, zero
    says nothing on stderr, the ticker names reach stderr, and the constant equals
    `scripts/eligibility_baseline.json`'s `warn_drop_fraction`.
  - `docs/data_contract.md` completeness section states the ingestion gate in one row and
    what a failed run leaves in Supabase.

impact_map: `run_ingestion.py` is step 2 of the scheduled job. A non-zero exit skips
  `dbt build`, the gates, the export and the assessments for that cycle; the previous Supabase
  snapshot stays. `storage/` is not cached between jobs, so a re-run in CI refetches every
  ticker.
