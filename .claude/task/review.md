# Review

diff_sha256: d5b9171aee874cab03378029ba26e9cf3e63bfa85b6b7431b1a4b1268ac7f424
rounds: 2

Refs #51, items 2 to 5 (item 6 is kept by the owner's answer A). Round 1 (tree 666ef99): platform-reviewer
PASS, data-engineer-reviewer PASS, scope-auditor FAIL: the `price_tickers_all_nan` counter never fired for a
one-ticker batch, because yfinance returns (ticker, field) columns for one ticker too unless
`multi_level_index=False`, and the test used a flat frame yfinance does not return. Fixed in round 2 (tree
608bdf5): the one-ticker branch selects the ticker's block from the MultiIndex (a ticker absent from the
response is counted `price_tickers_missing`), three tests on the real shape, one test for a fundamentals
mismatch seen on the first ticker, the helper blanks every column. Round 2: scope-auditor, platform-reviewer and
data-engineer-reviewer all PASS. Applied after the PASS verdicts, no round 3: the guide says a fundamentals file
that already covers every ticker is reused as written, the failure-path comment says a failed one-symbol batch is
`price_batches_empty`, the test that raises is named for what it does and closes its file handle, the contract
names the two missing-only tests and records the added `docs/operations_guide.md` scope path.

Coordinator evidence:
- Mutations of the fixes, file restored after each, eleven in all: snapshot written directly, temp file not
  cleaned, schema check off, skipped tickers not re-queued, `already_fetched` kept after a mismatch, multi-symbol
  and one-ticker NaN not counted, one-ticker block not selected, one-ticker missing not counted, counter not
  printed, repeated ticker not refused. Each fails a test.
- Real Wikipedia fixtures of all 14 refresh markets: no repeated ticker today.
- `pytest tests` 1409 passed; `scripts/bootstrap.py --verify` passes (dbt build 149 tests); em-dash and
  narrative-date checks pass.

follow_ups (filed as issues): a flat one-ticker frame has no test (the code still accepts it); a lower-case local
ticker would be counted as missing in both price branches (yfinance upper-cases its keys); a kill mid-write can
leave `<name>.tmp-<pid>` and nothing sweeps it (a sweep is a new mechanism: owner call); an all-NaN symbol is
written and so counts as already fetched on a same-day resume, with the counter at 0 in that run; two scripts
write `yf_constituents.parquet` directly (`scripts/seed_ci_raw_fixtures.py`, `scripts/audit_mart_vs_yfinance.py`).

## scope-auditor

VERDICT: PASS
reviewed_tree: 608bdf55c3f15dad17d63cd94732a74ae2393815
risks_checked:
- The round-1 finding is resolved against the installed yfinance; every touched file is in `scope_paths`.
- No new owner-level decision; the raise, the counter and its placement are the owner's answers.
wording_fixes: applied.

## platform-reviewer

VERDICT: PASS
reviewed_tree: 608bdf55c3f15dad17d63cd94732a74ae2393815
risks_checked:
- The three one-ticker tests pin the real (ticker, field) shape; the old flat branch fails all three.
- The new tests use fakes and `tmp_path` only, with no ordering or file-lock dependence.
wording_fixes: applied.

## data-engineer-reviewer

VERDICT: PASS
reviewed_tree: 608bdf55c3f15dad17d63cd94732a74ae2393815
risks_checked:
- The one-ticker path on the real yfinance shape, an empty frame, a flat frame and the `continue` before the flush.
- The counters stay exclusive: all-NaN block versus ticker absent.
wording_fixes: none.
