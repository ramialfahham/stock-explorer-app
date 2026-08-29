# Task contract

objective: Fix `au_asx200`'s Block ticker (`XYX`, has fetched no data since May) by building an
  ingestion-time ticker-override mechanism, mirroring the seed-override design built for the
  Nikkei and SMI name fixes but applied before the yfinance fetch instead of downstream in dbt,
  because a wrong ticker breaks the fetch itself rather than just the display. Owner-authorized
  2026-08-29 ("proceed with 1-5") after presenting the finding and the design choice.

scope_paths:
  - ingestion/paths.py
  - ingestion/constituents/seeds.py
  - ingestion/constituents/ticker_overrides.csv
  - tests/ingestion/test_constituent_seeds.py
  - tests/ingestion/test_market_onboarding.py
  - .claude/task/contract.md
  - .claude/task/review.md
  - .claude/active_work.md

decisions_reserved:
  - **Root cause, found during Explore, not assumed from the prior handover.** The earlier
    handover called this a "one-keystroke transcription error," implying a scraper bug. Fetched
    the live `S&P/ASX 200` Wikipedia table with the repo's own `_fetch_wikipedia_table` and
    confirmed it currently lists Block, Inc.'s code as `XYX` too. The error is on Wikipedia's own
    page, not in our scrape or parse. Confirmed against yfinance: `XYX.AX` 404s, `SQ2.AX` (an
    earlier ticker floated in the seed's own comment trail) also 404s, `XYZ.AX` resolves to
    Block, Inc. in AUD.
  - **Why this can't be a dbt-layer override like the name fixes.** `ingestion/yfinance/
    ingest.py:312` builds the yfinance fetch list from `load_constituents()`'s output before dbt
    ever runs; a correction applied in staging or base would arrive too late to fix what already
    fetched nothing. The correction has to intercept `load_constituents()` itself.
  - **Why the raw seed CSV (`storage/seeds/au_asx200/constituents.csv`) is NOT hand-edited to
    XYZ.** `scripts/refresh_constituents.py` is a standalone, manually-invoked script (not wired
    into CI or `scripts/run_ingestion.py`), so it will not silently overwrite a hand-edit today.
    But the next time anyone runs it for `au_asx200`, it re-scrapes Wikipedia and would put `XYX`
    right back, since that is what the source page still says. A hand-edit would look fixed and
    then quietly regress. The override sits between the raw seed and everything that consumes
    it, the same relationship the Nikkei/SMI seed override has to `storage/seeds/*/
    constituents.csv`, so a future refresh can put `XYX` back in the raw file and the override
    still corrects it before any fetch or write happens.
  - **Scope of the new mechanism.** One market-agnostic CSV (`market_code, ticker,
    corrected_ticker, reason`) and one interception point in `load_constituents()`, which is the
    single function all four current callers (`ingest.py`, and the three `scripts/probe_*.py` /
    `audit_yfinance_coverage.py` diagnostic scripts) already go through. No change to any of
    those callers. Not building a name-and-ticker unified override file: the two correct
    different things at different layers (pre-fetch vs. post-fetch) and a shared file would
    imply a shared consumer that does not exist.

done_when:
  - `ingestion/constituents/ticker_overrides.csv` exists with one row: `au_asx200, XYX, XYZ`,
    reason recording that Wikipedia's own table has it wrong and citing the yfinance check.
  - `ingestion/paths.py` gains `TICKER_OVERRIDES_PATH`, matching the existing `SEEDS_DIR` /
    `RAW_DIR` constant style.
  - `ingestion/constituents/seeds.py`'s `load_constituents()` applies the override to the
    `ticker` column before returning, via a pure `_apply_ticker_overrides(market_code, tickers,
    overrides)` function (testable with a synthetic frame, no disk I/O) plus a thin
    `_load_ticker_overrides()` reader, mirroring `_clean_company_name`'s pure-function shape in
    the same file. A missing or genuinely empty (zero-byte) override file is a no-op, not an
    error, so every other market and every future ticker are unaffected until a row is added for
    them; a file with the wrong columns raises a clear `ValueError` at load time (mirroring
    `load_constituents()`'s own missing-columns check) rather than a bare `KeyError` surfacing
    from inside `_apply_ticker_overrides` for whichever market happens to load first. Fixed in
    round 1 review after cto-reviewer reproduced both crash modes empirically.
  - `tests/ingestion/test_constituent_seeds.py` gains unit tests for `_apply_ticker_overrides`
    against synthetic data: a matching (market, ticker) pair is replaced; a different market or
    a different ticker is left untouched; an empty overrides frame is a no-op; vectorises over a
    multi-row series. Mirrors the file's existing `_clean_company_name` test shape. Also gains
    tests for `_load_ticker_overrides()` itself (monkeypatching `TICKER_OVERRIDES_PATH` to a
    `tmp_path` file): a missing file and a zero-byte file are both no-ops; a file with the wrong
    columns raises `ValueError`.
  - `tests/ingestion/test_market_onboarding.py` gains: a test that every override's ticker
    exists in that market's real raw seed (mirrors `test_company_name_overrides_target_real_
    constituents`); a test with no duplicate `(market_code, ticker)` keys in the override file;
    a test pinning the exact `au_asx200` row; and an end-to-end test that calls the real
    `load_constituents("au_asx200")` against the real seed and override files on disk and
    asserts the Block row's ticker comes back `XYZ`, not `XYX`, proving the mechanism actually
    fires today, not just that the override file has the right row.
  - The `blockinc` entry in `KNOWN_CROSS_MARKET_COMPANIES` is reworded: it no longer says Block
    is "NOT on the deck," since the next real ingestion run will fetch it correctly and it
    becomes a genuine cross-market duplicate like Amcor, Newmont, ResMed and Rio Tinto in the
    same list.
  - `pytest` green, no other test touched or weakened.
  - `check_layer_contract.py`, `check_dbt_tests.py`, `check_dbt_documentation.py`,
    `check_dbt_sql_structure.py`, `check_registry_var_sync.py` all green (none of these touch
    ingestion, so this is confirming no accidental regression, not exercising new coverage).
  - No em dash or en dash on any added line.

impact_map:
  - `ingestion/constituents/seeds.py`'s `load_constituents()` changes what it returns for any
    market with a row in `ticker_overrides.csv`: today, only `au_asx200`. Every one of its four
    callers sees the corrected ticker: `ingest.py`'s fetch list and its `yf_constituents.parquet`
    snapshot write, and the diagnostic scripts. No dbt model changes: the fix lands entirely
    before dbt runs, so `stg_yf__constituents` and everything downstream of it see the corrected
    ticker as if it had always been right, with no join or coalesce needed on that side.
  - Card-visible effect: on the next real ingestion run for `au_asx200`, Block, Inc. starts
    fetching real data and becomes eligible for a card, where today it silently ingests nothing.
    Not observable against CI's synthetic fixture tickers.
  - No already-shipped number changes for any other market or ticker; the override is keyed to
    one specific wrong ticker and is a no-op everywhere else.

amendments: (none)
