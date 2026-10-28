# Task contract
> DISPOSABLE. **Owner:** THIS task's objective, `scope_paths`, reserved decisions and
> `done_when`.
> **Never:** anything that outlives the task. Overwritten by the next task.

objective: Works #80 (ING-1 defect 1 and ING-5 defect 2 of the second quality-baseline audit re-run). The full-recording
  mode of `scripts/record_ingestion_fixtures.py` writes each ticker file before it has fetched the market's prices and
  saves the manifest once at the end, so a network failure leaves recordings that disagree with the manifest and the
  golden mart, unlike `--ticker` mode in the same script. And the rule that turns a US class-share dot into a hyphen
  (`to_yfinance_download_ticker`) has no test. One rule: a market's recording changes no file until that market's network
  calls have finished, the manifest is saved after each market, and every symbol rule has a test.

scope_paths:
  - scripts/record_ingestion_fixtures.py
  - tests/tooling/test_record_ingestion_fixtures.py
  - tests/ingestion/test_symbols.py
  - .claude/active_work.md
  - .claude/task/contract.md
  - .claude/task/review.md

decisions_reserved: None open. Both fixes copy what `rerecord_tickers` and the ticker-mode manifest save already do, and
  the test rule is `.claude/working-agreement.md` section 4. No recorded fixture, golden mart or ingestion code changes.

changes:
  - `record_market`: fetches every ticker payload and the price batch first, then writes the JSON files and
    `prices.parquet` (the order `rerecord_tickers` uses). A failed network call changes no file of that market.
  - `main` (full mode): the Wikipedia page of a `provider: wikipedia` market is fetched before `record_market` runs and
    written after it; the manifest is saved after each market, not once at the end. `record_wikipedia` is split into
    `fetch_wikipedia` (network) and `write_wikipedia` (file); nothing else called it.
  - `tests/tooling/test_record_ingestion_fixtures.py`: a failing ticker fetch, a failing price download and a failing
    Wikipedia fetch each leave every file as it was; a failure in the second market leaves the first market's manifest
    entry saved; the Wikipedia page is written and flagged; a full recording writes every ticker and the price batch.
  - `tests/ingestion/test_symbols.py` (new): pins `to_yfinance_ticker` and `to_yfinance_download_ticker`, including the
    dot-to-hyphen branch for an empty suffix and the unchanged dotted symbol for a non-empty one.
  - `.claude/active_work.md`: current facts.

done_when:
  - Moving the file writes back in front of the network calls in `record_market`, removing the dot-to-hyphen
    `replace`, and saving the manifest once after the loop each fail a test (mutation-checked).
  - `git grep -n "record_wikipedia" -- . ':!.claude/task'` finds nothing.
  - `pytest tests -q` passes; `python scripts/check_context_budget.py` passes.

known_limits:
  - The recorder needs the network and is run by hand; the tests replace the network calls, so no live recording run
    is part of this change.
  - A local file write that fails halfway (disk full) can still leave a market partly written; only network failures
    are covered, as in `rerecord_tickers`.

regression_checklist:
  - `--ticker` mode and its tests are untouched and pass as before.
  - The manifest content of a full recording is the same as before (`tickers`, `info_symbols`, `download_batch`,
    `wikipedia`, `recorded_at`, markets sorted); only when it is saved changes.
