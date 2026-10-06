# Review

diff_sha256: 11dbe8b21403bb1fc1a1db463642b3d5381cf247e7185aa777405bdd0cad006e
rounds: 2

Issue #34. Round 1 on the cumulative diff (tree 8ffab76): scope-auditor PASS, platform FAIL
(the full-rewrite test did not pin the `if args.markets:` merge guard, since every fixture
market was a no-argument target). Fix: a fixture row for a non-target market, kept by a
`--market` run and pruned by a full run. Round 2 on the delta (tree 23b5b19): both PASS.

Coordinator evidence: `pytest tests` 1079 passed; the `--market` test fails with the script
fix removed; the full-rewrite test fails with only the merge guard forced to `if True:`
(`{'NEW', 'OLD'} == {'NEW'}`); em-dash check passes.

## platform-reviewer

Round 1 FAIL (tree 8ffab76). Round 2:

VERDICT: PASS
reviewed_tree: 23b5b1943bb452f3f1b1a71f9a6d65249d848f10
risks_checked:
- `xx_retired` is pruned on a full run and kept on a `--market` run, so the merge guard is
  pinned from both sides.
- The `snapshot` fixture points `NAME_SNAPSHOT_PATH` at `tmp_path` and stubs the fetch; the
  committed CSV is never written.
- Re-running the same `--market` refresh replaces, never appends.
follow_ups:
- `write_snapshot` truncates the CSV in place; a crash mid-write leaves a partial file
  (pre-existing, recoverable from git).

## scope-auditor

Round 1 PASS (tree 8ffab76). Round 2:

VERDICT: PASS
reviewed_tree: 23b5b1943bb452f3f1b1a71f9a6d65249d848f10
risks_checked:
- `--market ch_smi` leaves it_ftsemib, us_sp500 and xx_retired rows unchanged.
- A full refresh prunes `xx_retired`; `merge_with_existing` is not called without `--market`.
