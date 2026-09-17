# Review
> DISPOSABLE. **Owns:** verdicts + diff hash for THIS task's staged change.
> **Never:** narrative of how the round went. Overwritten by the next task.

diff_sha256: aab790d953ef67d92f7312a0f421dd0d65389d96a15af44e4e1f42277723fe57

## scope-auditor
VERDICT: PASS
risks_checked:
- Prefix-matching normalization correctness and regression prevention: the original
  fixed-suffix approach was empirically rejected (139/956, ~15% false positives, systemic
  not an edge case); prefix matching validated against the real committed 956-row
  snapshot. The 57 remaining divergences were hand-reviewed: 54 confirmed via general
  knowledge, 3 verified via primary sources (GlobeNewswire, Euronext, LSE) before
  allowlisting. The allowlist's own staleness test reads real committed files and already
  caught 2 entries going stale mid-task when prefix matching made them redundant.
- CI failure-mode strictness and scope safety: `validate:full` (Tier A, unconditional),
  scope correctly limited to `provider: wikipedia` markets, snapshot staleness is a
  warning not a hard failure (verified in code, not just docstring).

## cto-reviewer
VERDICT: PASS
risks_checked:
- Constructed an adversarial case beyond the tests: a single-token seed name (e.g. "3M")
  has weak discriminating power under prefix matching -- a real residual gap, but already
  named explicitly in the function's own docstring as a conscious tradeoff, not an
  oversight. Not a blocker.
- CI dependency ordering: traced the full import chain (pandas/requests/yaml only, no
  duckdb/dbt), confirmed placement before `dbt deps` is safe.
- Exit-code logic verified by EXECUTION, not docstring: ran the guard directly against the
  committed snapshot, confirmed exit 0 with 7 warnings and 0 mismatches.
- Retry/rate-limit usage matches `ingest.py`'s own pattern; one cosmetic inaccuracy noted
  (doesn't separately import `is_rate_limited` for log labeling) with no behavioral effect.
- Spot-checked 6 allowlist entries against actual CSV data and hand-traced the tokenizer;
  all correct.
- `pytest`, `check_no_em_dash.py`, `check_context_budget.py`, `check_no_narrative_dates.py`
  all run independently, all pass.

## data-engineer-reviewer
VERDICT: PASS
risks_checked:
- Ticker-override ordering before fetch: confirmed `load_constituents()` applies
  `_apply_ticker_overrides()` before `refresh_yfinance_names.py` resolves the yfinance
  symbol -- fetches the corrected ticker, not a raw local one.
- Rate-limit posture on re-run: `--delay-seconds` default matches `ingestion/main.py`
  exactly; retry logic reuses the same shared `call_with_retry` helper other yfinance-
  calling scripts already use. No weaker posture introduced.
- Snapshot CSV structure verified directly: 956 rows across exactly the 8
  `provider: wikipedia` markets, counts matching the contract exactly, no duplicates, no
  empty names, one consistent `refreshed_at` timestamp (single real bulk run).
- File location (`ingestion/constituents/`) follows existing precedent
  (`ticker_overrides.csv`), distinct from gitignored `storage/raw/`.

## analytics-engineer-reviewer
VERDICT: PASS
risks_checked:
- CSV data quality verified directly: 956 rows, all columns present, zero duplicate keys,
  zero empty names. Apparent encoding corruption (mojibake in terminal display) confirmed
  as a false alarm by checking raw bytes -- genuinely correct UTF-8, a console display
  issue, not file corruption.
- Coverage gap (7 missing snapshot tickers) verified to match the contract's claimed count
  exactly once computed via the correct ticker-override-aware join key -- a naive diff
  against raw seed CSVs would misleadingly suggest a different, non-existent bug.
- `names_are_compatible` assessed as sound for this use case: symmetric as implemented,
  transitivity is moot since the guard never chains comparisons (each check is a single
  seed-vs-snapshot pair for an already-identified ticker, so it cannot cross-link two
  different companies through a third).
- One documentation nit found and fixed this round: the `au_asx200:ANZ` allowlist reason
  explained the seed's own acronym but not why the yfinance pairing is the same entity --
  corrected to name the 2022-23 holding-company restructure.

## Verified independently

- `pytest tests/ -q` -- 797 passed (full suite).
- `python scripts/check_company_names_vs_yfinance.py` -- exit 0 against the real committed
  snapshot: 0 mismatches, 7 benign "no snapshot entry" warnings (yfinance 404s on this
  particular fetch, a known non-blocking gap).
- `python scripts/check_no_em_dash.py`, `check_context_budget.py`, `check_docs_indexed.py`
  -- all pass.
