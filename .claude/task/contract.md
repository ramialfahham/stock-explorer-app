# Task contract
> DISPOSABLE. **Owns:** THIS task's objective, `scope_paths`, reserved decisions and
> `done_when`.
> **Never:** anything that outlives the task. Overwritten by the next task.

objective: Closes #19. Add a guard comparing each `provider: wikipedia` market's
  constituent seed `company_name` (after `ticker_overrides.csv` and
  `company_name_overrides.csv` are applied) against a cached snapshot of yfinance's own
  `info.longName`, so a wrong seed name (the class of defect that shipped as 11 wrong
  `jp_nikkei225` names, caught previously only by a one-off manual script) fails CI on the
  PR that introduces it, instead of shipping silently.

  Five decisions, all made via AskUserQuestion before implementation:
  1. **Data source**: a periodically-refreshed CACHED snapshot, not a live yfinance fetch
     on every CI run.
  2. **Match tolerance**: normalize known stylistic patterns (legal-form suffixes,
     punctuation, diacritics) before comparing; flag whatever still differs.
  3. **Scope**: only `provider: wikipedia` markets (`docs/constituent_sources.yml`) -- 8 of
     the 9 active markets; `jp_nikkei225` (`provider: manual`) has no independent source to
     compare against and is excluded.
  4. **Failure mode**: hard-fail on a seed-touching PR. Implemented by adding the check to
     `validate:full` (Tier A), which already runs unconditionally on every MR/push, per this
     repo's own documented "no path-triggered tier" philosophy -- no new conditional CI
     logic needed, consistent with every other Tier A check.
  5. **Snapshot refresh mechanism**: a manual script (`scripts/refresh_yfinance_names.py`),
     run occasionally by a human and its output committed -- exactly how
     `scripts/refresh_constituents.py` already works. NOT a CI job that commits back to the
     repo: this repo has no such mechanism today, and building one is its own new-mechanism
     decision (a CI push credential) that was explicitly declined in favor of the simpler,
     already-precedented manual-script pattern.

  **Match tolerance (decision 2) had to be substantially revised after real data.** A
  fixed legal-suffix normalization list, run against the real live snapshot (956
  companies, 8 markets), flagged 139 of 956 (~15%) -- systemic across every market, not a
  `ch_smi`-only edge case: yfinance's `longName` is very often the FULL legal name
  ("Commonwealth Bank" vs "Commonwealth Bank of Australia"). A fixed suffix list cannot
  bridge that at scale. Replaced with prefix matching (`names_are_compatible`): one name's
  tokens being a leading subsequence of the other's counts as the same company, which
  covers the whole class without enumerating every legal form -- cut 139 to 57 mechanically
  (plus two real normalization bugs found and fixed along the way: `&` vanishing as
  whitespace risked the exact Merck & Co / Merck KGaA false-merge this repo's own
  `test_market_onboarding.py` already warns about; a blanket dotted-abbreviation collapse
  fused "Amazon.com" into one token). The remaining 57 were reviewed by hand: 54 confirmed
  same-company via general knowledge (rebrands, acronyms, legal-form variants) and added to
  `KNOWN_STYLISTIC_DIVERGENCES`; the last 3 (au_asx200:PDI, es_ibex35:COL.MC,
  uk_ftse100:DCC) needed a source beyond general knowledge and were verified via WebSearch
  against primary sources (GlobeNewswire, Euronext, the London Stock Exchange's own listing
  page) before being added -- all three are genuine 2025/2026 renames or mergers the seed's
  own display name hasn't caught up with, not data bugs. Guard is fully clean (exit 0)
  against the real snapshot as committed.

scope_paths:
  - scripts/refresh_yfinance_names.py
  - scripts/check_company_names_vs_yfinance.py
  - ingestion/constituents/yfinance_name_snapshot.csv
  - ingestion/paths.py
  - .gitlab-ci.yml
  - docs/operations_guide.md
  - tests/tooling/test_check_company_names_vs_yfinance.py
  - .claude/task/contract.md
  - .claude/task/review.md

decisions_reserved: none further -- all five were answered via AskUserQuestion before this
  contract was written.

done_when:
  - `scripts/refresh_yfinance_names.py`: for each `provider: wikipedia` active market,
    resolves each constituent's yfinance symbol (via the existing `to_yfinance_ticker`
    helper, ticker-override-corrected via `load_constituents`), fetches `info.longName`
    only (not the full fundamentals payload `_fetch_fundamentals_row` pulls), using the
    existing `call_with_retry`/`is_rate_limited` retry stack and a `--delay-seconds`
    option matching `run_ingestion.py`'s convention. Writes
    `ingestion/constituents/yfinance_name_snapshot.csv` (market_code, ticker,
    yfinance_long_name, refreshed_at).
  - `scripts/check_company_names_vs_yfinance.py`: for each `provider: wikipedia` market,
    computes the FINAL seed name (seed CSV + `company_name_overrides.csv`, override wins),
    tokenizes both it and the cached snapshot name (diacritics, punctuation, dotted-
    abbreviation, trailing-parenthetical, leading-"the" insensitive) and flags a ticker
    UNLESS one name's tokens are a leading prefix of the other's, or the ticker is in
    `KNOWN_STYLISTIC_DIVERGENCES`. A ticker with no snapshot entry is a warning
    (stale/incomplete snapshot), not a hard failure -- a different failure class than a
    real name defect. Exits non-zero, listing every offender, if any hard mismatch remains.
  - The initial snapshot is a REAL fetch (not a stub), run as part of this task, and the
    guard run against it repeatedly as the matching logic was corrected -- confirmed
    empirically, not assumed, ending at zero real mismatches (7 tickers have no snapshot
    entry, 404s from yfinance on this fetch -- a known, non-blocking gap, not chased
    further this task).
  - `validate:full` in `.gitlab-ci.yml` runs the new check, placed alongside the other
    registry/seed-shaped checks (no DuckDB dependency).
  - `docs/operations_guide.md`'s "Manual operations" section documents the refresh script,
    alongside `refresh_constituents.py`.
  - Tests: tokenization and `names_are_compatible` are unit-tested, including the specific
    false-merge risk this repo has already reasoned about elsewhere (`test_market_onboarding.py`'s
    Merck KGaA vs Merck & Co warning), and a staleness test for `KNOWN_STYLISTIC_DIVERGENCES`
    (mirroring `test_market_onboarding.py`'s own `KNOWN_DUPLICATE_SEED_NAMES` pattern) that
    reads the real committed seeds/overrides/snapshot directly and fails if an allowlisted
    divergence has quietly resolved -- it already caught 2 of the original 3 entries going
    stale mid-task, when prefix matching made them redundant.
  - `pytest tests/ -q` green.

impact_map: two new scripts (ingestion-adjacent, no dbt/schema change), one new checked-in
  data file (the snapshot), one new `validate:full` CI step, one docs update. No live
  yfinance calls in CI -- only in the manually-run refresh script. No Supabase/production
  access needed anywhere in this task.
