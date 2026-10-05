# Task contract
> DISPOSABLE. **Owns:** THIS task's objective, `scope_paths`, reserved decisions and
> `done_when`.
> **Never:** anything that outlives the task. Overwritten by the next task.

objective: Onboard the six queued markets in one batch -- Finland (OMX Helsinki 25), Sweden
  (OMX Stockholm 30), Denmark (OMX Copenhagen 25), Norway (OBX), Canada (S&P/TSX 60), Italy
  (FTSE MIB) -- following `docs/data_contract.md`'s market activation checklist per market.

scope_paths:
  - docs/market_registry.yml
  - docs/constituent_sources.yml
  - docs/operations_guide.md
  - docs/supabase_setup.md
  - storage/seeds/fi_omxh25/
  - storage/seeds/se_omxs30/
  - storage/seeds/dk_omxc25/
  - storage/seeds/no_obx/
  - storage/seeds/ca_tsx60/
  - storage/seeds/it_ftsemib/
  - dbt_analytics/dbt_project.yml
  - dbt_analytics/seeds/ticker_overrides.csv
  - dbt_analytics/seeds/company_name_overrides.csv
  - dbt_analytics/seeds/_seeds.yml
  - ingestion/constituents/refresh.py
  - ingestion/constituents/seeds.py
  - ingestion/constituents/yfinance_name_snapshot.csv
  - supabase/migrations/021_fi_se_dk_no_ca_it_markets.sql
  - frontend/markets.py
  - frontend/live_quote.py
  - frontend/card_copy.py
  - scripts/assessment_rules.py
  - scripts/check_company_names_vs_yfinance.py
  - scripts/eligibility_baseline.ci.json
  - tests/ingestion/test_market_onboarding.py
  - tests/ingestion/test_constituent_seeds.py
  - tests/tooling/test_assessment_rules.py
  - .claude/active_work.md
  - .claude/task/contract.md
  - .claude/task/review.md
  - .claude/task/review_input.patch

decisions_reserved: settled by the owner before implementation --
  Markets and batching: the six above, one branch (agreed earlier, recorded in the handover).
  Indices: Sweden OMXS30, Norway OBX, Canada S&P/TSX 60, Italy FTSE MIB (earlier); Finland
  OMX Helsinki 25 and Denmark OMX Copenhagen 25 (in-thread). Currency display: CAD "C$";
  SEK, DKK, NOK bare ISO codes (the rule recorded beside `_CURRENCY_SYMBOLS`). Headlines
  (in-thread, option A): Nordic headlines drop the share-class letter, except A.P.
  Moller-Maersk, whose A and B classes are both OMXC25 members.
  After round 2 (in-thread): `--max-reads` stays unset for the first run; all three Nordea
  cards read "Nordea"; Nordic headlines also drop the legal-form ending (ABB, the Norwegian
  ASA/Limited names), while Canada keeps "Inc."/"Limited" like the US and Australia.
  Taken by the builder within those decisions, flagged to the owner in the MR: market codes
  follow the existing `<country>_<index>` pattern; display names are the indices' common
  names; Carlsberg and Rockwool show their plain company names (seed gave "Carlsberg Group"
  and the former "Rockwool International").

known_limits:
  - Name check: KNOWN_STYLISTIC_DIVERGENCES accepts a listed trade-name/legal-name pair; a
    later rename of one of those companies shows up only when its divergence test fails.

regression_checklist:
  - The nine existing markets' seeds, overrides and name-snapshot rows are unchanged.
  - Every active market has a `public.markets` migration row matching the registry.
  - `test_market_onboarding.py`, `check_company_names_vs_yfinance.py` and
    `check_registry_var_sync.py` pass.

done_when:
  - Checklist steps 1-4 and 7-11 done for all six; step 5 sample run and step 6 estimated
    (both recorded in the MR); the full-run half of steps 5-6 recorded as open in
    `.claude/active_work.md` until the first production run.
  - Every seed ticker resolves to Yahoo's form; a missing source cell is dropped, never
    written as "nan"; the ticker "NA" survives fetch, write and load (tests).
  - `pytest tests` passes; fixture `dbt build` passes; review cycle run; MR opened. Not merged.

amendments:
  - Round 1: data-engineer and scope-auditor PASS; analytics-engineer FAIL [broken-guarantee]
    (the 7 ticker overrides and the Nordic headline overrides were unpinned) and platform FAIL
    [broken-guarantee] (the missing-cell test could not fail). Fixed: exact-pair pin for the 7
    ticker overrides, a Toronto-suffix test over the real ca_tsx60 seed, an exact-set pin for
    the se/fi/dk headline overrides, a `_clean_ticker` missing-cell test that fails on the old
    line. Wording fixes applied (incl. `_seeds.yml`, added to scope for it); `_CURRENCY_WORDS`
    gains krona/kronor/krone/kroner (platform follow-up, in scope). Other follow-ups filed.
  - Round 2 (delta): all four PASS. Then the owner's Nordea and legal-ending decisions: 7
    headline rows, the pin test extended, and the name-override target test now checks the
    ticker after ticker_overrides (the key dbt joins on; the Nordea Copenhagen row needs it).
