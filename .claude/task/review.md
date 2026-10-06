# Review

diff_sha256: 818786e0311beedbd0a30f90e0259eb27a6ebd3a08d119d05d63fe71183e2ad8
rounds: 1

Issue #37. Round 1 on the cumulative diff (tree 3d11bb8): platform-reviewer and scope-auditor
PASS.

Coordinator evidence: `pytest tests` 1089 passed; changing one name in each group (Nordea DK,
Nestlé, SKY Perfect JSAT) fails all three pins; `company_name_overrides.csv` restored with no
diff.

## platform-reviewer

VERDICT: PASS
reviewed_tree: 3d11bb85b9b91fbd4bc980df113151ac76116739
risks_checked:
- All 65 pinned (ticker, name) pairs match the committed override CSV, accented names
  included; dict equality fails on a changed, added or removed row.
- The reworded docstring matches the test body and `load_constituents`.
- Test-only; no hook, CI, dependency, credential or cost change.
follow_ups:
- Optional: a check that every `market_code` in the override CSV is covered by a pin test,
  so a row added for an unpinned market fails (pre-existing limit).

## scope-auditor

VERDICT: PASS
reviewed_tree: 3d11bb85b9b91fbd4bc980df113151ac76116739
risks_checked:
- Pinned pairs match the CSV line by line; value, addition and removal changes all fail.
- The docstring claim matches `load_constituents` applying `ticker_overrides.csv`.
