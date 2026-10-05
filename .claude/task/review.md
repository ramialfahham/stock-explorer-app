# Review

diff_sha256: eaecb2a7fcc4b301ec3b098ae59f97275711113e856146bd2c07fd4b7c011678
rounds: 3

Six markets (fi_omxh25, se_omxs30, dk_omxc25, no_obx, ca_tsx60, it_ftsemib). Round 1 on the
cumulative diff (tree 6408cf9): data-engineer and scope-auditor PASS, analytics-engineer and
platform FAIL [broken-guarantee], fixed. Round 2 on the delta (tree d8c57b4): all four PASS,
committed. Round 3 on the delta for the owner's Nordea and legal-ending decisions (tree
6ffc46e): analytics-engineer, platform and scope-auditor PASS; data-engineer not re-dispatched
(no file in its territory changed since its round-2 PASS). Detail in `contract.md`'s amendments.

Coordinator evidence: `pytest tests` 1012 passed; fixture `dbt build` PASS=150;
`check_company_names_vs_yfinance.py` no mismatches; earlier rounds also ran the CI eligibility
baseline and registry sync checks (both OK). Follow-ups filed: #34, #35, #36, #37.

## analytics-engineer-reviewer

Round 1 FAIL, round 2 PASS. Round 3:

VERDICT: PASS
reviewed_tree: 6ffc46eed6de54ae7bc311c1c7464c7b378e0d3b
risks_checked:
- The 7 new headline rows are keyed on the tickers dbt joins on (NDA-DK.CO after
  ticker_overrides); no duplicate keys, no grain or ticker-mapping change.
- The pin test covers the 7 rows by exact set; the target test now checks post-override
  tickers.

## platform-reviewer

Round 1 FAIL, round 2 PASS. Round 3:

VERDICT: PASS
reviewed_tree: 6ffc46eed6de54ae7bc311c1c7464c7b378e0d3b
risks_checked:
- Reverting the target test to the raw seed fails on NDA-DK.CO.
- The delta is append-only to the overrides seed; the nine existing markets are untouched.

## data-engineer-reviewer

Round 1 PASS (tree 6408cf9). Round 2:

VERDICT: PASS
reviewed_tree: d8c57b4351f5e741e81fe0143ecf3a3c4957e0d5
risks_checked:
- The `_seeds.yml` claim (name overrides join on the post-override ticker) matches
  `load_constituents` and `ingest_market`.
- No write mode, history window, fan-out cap, raw schema or cadence changed in the delta.

## scope-auditor

Round 1 and 2 PASS. Round 3:

VERDICT: PASS
reviewed_tree: 6ffc46eed6de54ae7bc311c1c7464c7b378e0d3b
risks_checked:
- The 7 rows implement exactly the owner's Nordea and Nordic legal-ending decisions, keyed
  on real tickers.
- The target-test change is needed for the Nordea Copenhagen row and matches dbt's join.
