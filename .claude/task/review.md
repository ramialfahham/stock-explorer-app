# Review

diff_sha256: 48b33ca93fc2b87dc47bbb1bb355804e3362acfaa5cb90b135b45823ae7120fd
rounds: 2

Issue #38. Round 1 on the cumulative diff (tree f22ff2d; the re-recorded raw files under
`tests/fixtures/real/yfinance/` excluded from the patch, sampled on disk): analytics-engineer,
data-engineer and scope-auditor PASS; platform FAIL [broken-guarantee] (the recorder's
`--ticker` mode untested), fixed. Round 2 on the delta (tree af33b40): platform and
scope-auditor PASS; analytics-engineer and data-engineer not re-dispatched (none of their
routed files changed since their round-1 PASS). platform's round-2 wording fix (docstring)
applied after round 2.

Coordinator evidence: `pytest tests` 1074 passed; the guard test fails for exactly us_sp500 and
uk_ftse100 with the three override rows removed; before regeneration the golden check showed
exactly 3 differences (new rows us_sp500/BRK-B and uk_ftse100/BT-A.L; us_sp500/JPM
sector_peer_count 1 -> 2); name check no mismatches. Follow-ups: #41.

## platform-reviewer

Round 1 FAIL (tree f22ff2d). Round 2:

VERDICT: PASS
reviewed_tree: af33b406f29b6d2c550a2b876f7cac59f69be9ff
risks_checked:
- Each `--ticker` behaviour has a test that fails on revert: named ticker replaced, others
  kept, stale JSON removed, files byte-identical when the network fails, flat frame wrapped.
- Bad argument combinations exit 2; no dependency, CI or cost change.

## analytics-engineer-reviewer

VERDICT: PASS
reviewed_tree: f22ff2d9405607e4e9295df08514be24fad9625d
risks_checked:
- The golden diff is exactly the two new rows plus JPM's peer count; no benchmark moves (the
  8-peer threshold is not reached).
- No company_name_overrides row is keyed on the old dotted tickers; no production card key moves.

## data-engineer-reviewer

VERDICT: PASS
reviewed_tree: f22ff2d9405607e4e9295df08514be24fad9625d
risks_checked:
- Raw files are rewritten whole per run, so no old dotted key can persist beside the new one.
- The three name-snapshot rows are keyed on the post-override ticker and match the seed names.

## scope-auditor

Round 1 PASS (tree f22ff2d). Round 2:

VERDICT: PASS
reviewed_tree: af33b406f29b6d2c550a2b876f7cac59f69be9ff
risks_checked:
- Network calls finish before any file write, pinned by a test.
- Stale JSON cleanup is pinned by a test.
