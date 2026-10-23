# Task contract
> DISPOSABLE. **Owner:** THIS task's objective, `scope_paths`, reserved decisions and
> `done_when`.
> **Never:** anything that outlives the task. Overwritten by the next task.

objective: Closes #71 (the six defects of the ingestion area in the quality-baseline audit re-run) and
  Closes #43 (the name snapshot written atomically). Three text files are written in place (the seed CSV and
  the name snapshot), so a kill mid-write leaves a truncated key list; an empty yfinance `info` is stored as an
  all-null fundamentals row and counted as `fundamentals_ok`; the name-snapshot refresh drops a ticker that
  failed or had no name, and with it the previous good row; and six guards in the ingestion entry points and the
  seed scripts have no test (deleting any leaves the suite green). One rule over every case: a committed
  or raw file is the last complete write or the new one, a defaulted or empty row is counted and named, and
  every exit-1 guard has a test that fails when the guard is removed.

scope_paths:
  - ingestion/atomic_write.py
  - ingestion/yfinance/ingest.py
  - ingestion/main.py
  - ingestion/constituents/seeds.py
  - scripts/refresh_yfinance_names.py
  - tests/ingestion/test_atomic_write.py
  - tests/ingestion/test_ingest_resume.py
  - tests/ingestion/test_ingest_failure_reporting.py
  - tests/ingestion/test_constituent_seeds.py
  - tests/ingestion/test_constituent_refresh_guards.py
  - tests/tooling/test_refresh_yfinance_names.py
  - tests/tooling/test_import_constituents.py
  - tests/tooling/test_refresh_constituents.py
  - docs/data_contract.md
  - .claude/active_work.md
  - .claude/task/contract.md
  - .claude/task/review.md

decisions_reserved: Answered by the owner in chat. Defect 1: one shared atomic-write helper used for the seed
  CSV and the name snapshot (A), which also closes #43; the fixture `manifest.json` stays out (hand-run
  recording script). Defect 2: a separate counter `fundamentals_empty`, printed on the summary line and named on
  stderr; it does NOT count toward the 5% line (A); the empty row also leaves `fundamentals_ok`, so ok, failed,
  skipped and empty add up (B, answer 1 to the scope review); the empty row replaces the ticker's previous
  fundamentals row as before, no new keep-previous step (A, answer 2); the log wording as built (A, answer 3). Defect 3: a failed or nameless ticker keeps its previous
  snapshot row if it had one; each market's summary prints how many failed, had no name, and kept the old row;
  exit code stays 0 (A). The owner-call items 7 to 9 of #71 (dropped-row count, the resume design, the price
  premise) are not touched. No change to a mart column, a card number or an export column.

changes:
  - `ingestion/atomic_write.py`: `replace_atomically(path, write)` -- `write(tmp)` into a same-directory temp
    file, `os.replace` onto `path`, temp removed if `write` raises. `_replace_parquet` in `ingest.py` calls it
    (same behaviour as now); `write_constituents` writes the seed through it; `write_snapshot` in
    `scripts/refresh_yfinance_names.py` writes the snapshot through it.
  - Defect 2: `_fetch_fundamentals` counts a built row whose every value outside `market_code`, `ticker` and
    `snapshot_date` is empty as `fundamentals_empty`, lists it in `fundamentals_empty_tickers`, and prints a
    warning line like the failed ones. The row is still written. `ingestion/main.py` adds
    `fundamentals_empty=N` to the summary line and names the tickers on stderr.
  - Defect 3: `refresh_snapshot` loads the previous snapshot; a ticker that raised or returned no `longName`
    keeps its previous row unchanged (old `refreshed_at`) when there is one; the per-market line prints
    `refreshed N names, failed F, no name E, kept previous K`.
  - Defects 4 to 6: tests only (no production change), listed in `done_when`.
  - `docs/data_contract.md`: the ingestion-gate paragraph says an empty row is counted as `fundamentals_empty` and does not count toward the 5%.
  - `.claude/active_work.md`: current facts (audit run, the six issues, this branch).

done_when:
  - New tests, each failing when its fix or guard is reverted (mutation-checked):
    - `replace_atomically`: previous file intact and no temp file when `write` raises; target replaced when it
      succeeds; the seed CSV and the name snapshot each survive a write that raises.
    - An empty-`info` ticker is counted in `fundamentals_empty`, listed, still written, not counted toward the
      5% line (a market with it exits 0); the summary line prints the counter and stderr names the ticker.
    - Name snapshot refresh: a ticker that raises and a ticker with no `longName` keep their previous row, a new
      ticker with no previous row is omitted, and the per-market line carries the three counts.
    - `ingestion.main.main`: `--market nope` returns 1 with the message on stderr; no active market returns 1;
      a market whose source is not yfinance is skipped with the notice and `ingest_market` is not called.
    - `load_constituents`: a seed missing a column raises with the columns named; a missing seed file raises
      `FileNotFoundError` naming the scripts; `refresh_market`: table_index beyond the tables raises
      `IndexError`, a manual/disabled market and an unsupported provider and an incomplete wikipedia config
      each raise `ValueError` with their message.
    - `scripts/refresh_constituents.main`: one market raising returns 1 with the message on stderr and the other
      market is still refreshed; no selected market returns 1. `scripts/import_constituents.main`: a missing
      `--ticker-column` returns 1 with the message.
  - `git grep -n "to_csv\|open(.*\"w\"" -- ingestion scripts/refresh_yfinance_names.py scripts/import_constituents.py scripts/refresh_constituents.py`
    lists no direct write of a committed seed or name snapshot (the keep list: `scripts/check_real_fixture_mart.py`,
    `scripts/replay_ingestion_fixtures.py`, `scripts/record_ingestion_fixtures.py`, which are hand-run fixture tools).
  - `git grep -n "fundamentals_failed" -- ingestion tests docs` lists the same places for `fundamentals_empty`
    where a list of the fundamentals counters appears (the pinned key sets, the summary line).
  - `pytest tests -q` and `python scripts/bootstrap.py --verify` pass.
  - #71 items 1 to 6 ticked; #43 closed by the merge request; items 7 to 9 stay in the issue as owner calls.

known_limits:
  - On a same-day resume, empty rows already in the checkpoint are skipped: they are not counted or named in
    the final run's summary (the first attempt's log named them). Filed in #70 with this merge request.
  - "Empty" is every value except the three key columns missing; a row with one field set is not counted. A
    ticker whose `info` is empty but whose statements carry values is a partial row, not counted.
  - A name-snapshot ticker that failed and has no previous row is omitted and counted under `failed`.
  - The atomic helper does not sweep a temp file left by a process kill (#70).

regression_checklist:
  - The summary line keeps every existing counter and its order; `fundamentals_empty` is added after
    `fundamentals_skipped`.
  - The 5% line and the exit code of `ingestion/main.py` are unchanged for failed tickers.
  - A snapshot refresh with no failures writes the same CSV as before (sorted rows, same columns).
  - The parquet writes (`_replace_parquet`, `_atomic_write_parquet`) behave as before, including the marker
    touched only by `_atomic_write_parquet`.
