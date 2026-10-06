# Task contract
> DISPOSABLE. **Owns:** THIS task's objective, `scope_paths`, reserved decisions and
> `done_when`.
> **Never:** anything that outlives the task. Overwritten by the next task.

objective: Closes #41 -- the dot guard checks each market's own suffix, the US and UK
  sources document their class shares, and `record_ingestion_fixtures.py --ticker` records
  per-ticker dates and saves the manifest per market (including the two items in the issue's
  comment).

scope_paths:
  - tests/ingestion/test_market_onboarding.py
  - docs/constituent_sources.yml
  - scripts/record_ingestion_fixtures.py
  - tests/tooling/test_record_ingestion_fixtures.py
  - .claude/task/contract.md
  - .claude/task/review.md
  - .claude/task/review_input.patch

decisions_reserved: settled by the owner in-thread -- the cross-listing exemption reuses
  KNOWN_DUAL_INDEX_SYMBOLS (no new list); item 3 is option (a), a `rerecorded_at` map per
  market entry in `tests/fixtures/real/manifest.json`, written by `--ticker` and dropped by a
  full recording. No backfill of past re-record dates.

done_when:
  - A dotted resolved symbol passes only if it ends in its own market's suffix or
    KNOWN_DUAL_INDEX_SYMBOLS lists it for that market; `FOO.L` in us_sp500 fails.
  - us_sp500 and uk_ftse100 in `docs/constituent_sources.yml` note their dotted class shares
    and point at `ticker_overrides.csv`.
  - `--ticker` writes `rerecorded_at` (ticker -> date), keeps earlier dates for tickers still
    listed, drops unlisted ones, and leaves `recorded_at` unchanged.
  - `--ticker` across several markets writes the manifest after each market; a later
    market's failure leaves an earlier market's entry current.
  - A test re-records two tickers in one market.

known_limits:
  - Tickers re-recorded before this change carry no `rerecorded_at` entry.

regression_checklist:
  - Every active market's resolved symbols still pass the dot guard.
  - A full recording still replaces the market's manifest entry (and so clears
    `rerecorded_at`).
  - A failed network call in `rerecord_tickers` still changes no file.
