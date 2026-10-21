# Task contract
> DISPOSABLE. **Owner:** THIS task's objective, `scope_paths`, reserved decisions and
> `done_when`.
> **Never:** anything that outlives the task. Overwritten by the next task.

objective: Refs #51 (items 2 to 6 of the audit list), milestone "3 · Professional baseline". Four places in
  ingestion can leave partial, mixed-schema or silently reduced raw data: the constituents snapshot is written
  straight to its final path (item 2); a same-day fundamentals checkpoint is reused without a schema check, so
  an old-schema file mixes with new rows (item 3); `write_constituents` drops repeated tickers without a word
  (item 4); a per-symbol price download that failed inside a good batch is written as all-NaN rows and counted
  as retrieved (item 5). Item 6 (a resumable run overwrites the last complete raw file with a partial one) is
  a documented design and stays. One rule over every case: a raw file is either the last complete write or
  the new one, a schema change forces a refetch, and every dropped or empty row is counted or refused.

scope_paths:
  - ingestion/yfinance/ingest.py
  - ingestion/main.py
  - ingestion/constituents/seeds.py
  - tests/ingestion/test_ingest_resume.py
  - tests/ingestion/test_ingest_failure_reporting.py
  - tests/ingestion/test_constituent_seeds.py
  - tests/ingestion/test_market_onboarding.py
  - docs/operations_guide.md
  - .claude/active_work.md
  - .claude/task/contract.md
  - .claude/task/review.md

decisions_reserved: Answered by the owner in chat. Item 4: a repeated ticker raises an error naming the
  tickers, "seed not written" (A), like the unnamed-row guard; checked on the recorded Wikipedia pages of all 14
  refresh markets, none repeats a ticker today. Item 5: a new counter `price_tickers_all_nan`, printed on the
  summary line with the other price counters (A). Item 6: keep the resume design, no code change (A); the
  reworded criterion ING-1 ("no torn file; partial coverage only while a resumable run is unfinished") goes
  into the criteria v4 bump the owner already has pending (DOC-2, HYG-4), and a criteria change needs the
  owner, so `docs/quality_criteria.json` is not touched here. No change to a mart column, a card number or
  an export column.

changes:
  - Item 2: `_replace_parquet(frame, path)` (same-directory temp file, then `os.replace`) is split out of
    `_atomic_write_parquet`; the snapshot write uses it and does not touch any checkpoint marker;
    `_atomic_write_parquet` calls it, then touches the marker as before.
  - Item 3: `_fetch_fundamentals` compares the column set of the first freshly built row with the columns of
    the same-day checkpoint. A mismatch discards the checkpoint rows and refetches every ticker, as for a
    stale file. The row schema is built at run time (INFO_FIELDS plus statement, quarterly and balance-sheet
    fields), so the check compares against the real row, not a second list.
  - Item 4: `write_constituents` finds tickers that repeat after cleaning (non-empty ones), and raises
    `ValueError` naming them with "seed not written", before the unnamed-row check.
  - Item 5: `_fetch_daily_prices` counts a symbol whose downloaded block has no non-NaN `Close` as
    `price_tickers_all_nan`, still writes its rows, and `ingestion/main.py` prints the counter on
    the summary line; a one-ticker batch selects the ticker's block from the (ticker, field) columns
    yfinance returns, like the many-ticker branch; the comment about the uncaught case is replaced by the counter's description.
  - Item 4 also updates the two comments that say `write_constituents` de-duplicates on ticker
    (`ingestion/constituents/seeds.py`, `tests/ingestion/test_market_onboarding.py`): it now checks tickers.
  - `docs/operations_guide.md` (added to scope_paths: the re-run paragraph states the item 3 refetch).
  - `.claude/active_work.md`: current facts (14 blank cards, #55 and #52 merged, #51 state, the criteria v4
    wording for ING-1, #69).

done_when:
  - Tests, each failing when its fix is reverted (mutation-checked): a write that raises during the snapshot write leaves
    the previous snapshot in place and no temp file; the snapshot write leaves no marker; a same-day
    fundamentals checkpoint with a different column set is fully refetched and the output has one schema; a
    table with a repeated ticker raises naming it and writes nothing; an all-NaN symbol block in a batch is
    counted and the summary line prints it.
  - `git grep -n "price_tickers_missing" -- ingestion tests docs` lists the same places for
    `price_tickers_all_nan`, except the two tests that exercise only the missing case
    (`test_empty_and_missing_are_counted_from_the_real_fetch`, `test_empty_batches_and_missing_tickers_do_not_fail_the_run`).
  - `pytest tests -q` and `python scripts/bootstrap.py --verify` pass; the real-fixture replay tests
    (`tests/ingestion/test_real_fixtures.py`) still pass.

known_limits:
  - Item 3 detects a schema change only when at least one ticker is still pending; a checkpoint where every
    ticker is already fetched is reused as written (nothing mixes), as before.
  - A symbol is "all NaN" when its downloaded block has no non-NaN close; a symbol with partial NaN rows is
    not flagged.
  - Item 6: after an interrupted resumable run the raw file covers only the tickers fetched so far with a
    fresh timestamp. Production keeps no raw files between pipelines, so only a local re-run sees it.

regression_checklist:
  - Resume, force-refetch, stale-file and other-script-write behaviour of both fetch functions is unchanged
    (the existing resume tests pass; the pinned counter key sets gain the new counter).
  - The summary line keeps every existing counter and its order; the new one is added.
  - A refresh of a market with no repeated ticker writes the same seed as before.
