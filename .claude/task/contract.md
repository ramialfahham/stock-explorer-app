# Task contract
> DISPOSABLE. **Owns:** THIS task's objective, `scope_paths`, reserved decisions and
> `done_when`.
> **Never:** anything that outlives the task. Overwritten by the next task.

objective: Closes #39 -- a DAX constituent refresh keeps the committed bare ticker form (ADS)
  although the Wikipedia table now gives ADS.DE, so no DAX card is re-keyed.

scope_paths:
  - ingestion/constituents/refresh.py
  - docs/constituent_sources.yml
  - tests/ingestion/test_constituent_seeds.py
  - tests/ingestion/test_real_fixtures.py
  - .claude/active_work.md
  - .claude/task/contract.md
  - .claude/task/review.md
  - .claude/task/review_input.patch

decisions_reserved: settled by the owner in-thread before implementation --
  Ticker form (option A): DAX tickers stay bare. Mechanism (owner-approved as part of A): a
  new optional `strip_suffix` field in `docs/constituent_sources.yml`, read into
  `RefreshConfig` and applied by `refresh_market` before the seed is written; `.DE` for
  de_dax only. No seed, Supabase or card-key change.

known_limits: none.

regression_checklist:
  - Every other market's refresh is unchanged (no `strip_suffix`, page form kept).
  - A missing source cell is still dropped, never written as "nan".
  - The recorded Wikipedia pages still parse into their committed seeds.

done_when:
  - `refresh_market` strips exactly the configured suffix (ADS.DE -> ADS; AIR.PA and SAP
    unchanged); a market without `strip_suffix` keeps the page form (tests).
  - The recorded DAX page parses into the committed seed (de_dax off KNOWN_PAGE_DRIFT).
  - `pytest tests` passes; review cycle run; MR opened. Not merged.

amendments:
  - Round 1: all three PASS. Two reviewers' follow-up applied: the suffix is stripped after
    trimming whitespace, so a trailing space or non-breaking space cannot keep `.DE` and
    re-key a card; tests add `"BAS.DE\u00a0"` (a trailing non-breaking space) and end-anchoring (`"X.DEF"` kept); the strip
    test fails without the fix. Wording fix in the handover. Other follow-ups filed.
