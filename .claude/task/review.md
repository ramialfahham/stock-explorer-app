# Review

diff_sha256: ba4475bf4db5c1cff50faf05e065a556b3c6eff348d1b361f716feba7f48a951
rounds: 1

Works #80 (ING-1 defect 1, ING-5 defect 2 of the second audit re-run). In `scripts/record_ingestion_fixtures.py`,
`record_market` fetches every ticker payload and the price batch before it writes a file; the Wikipedia page of a market
is fetched before the market is recorded and written after it (`record_wikipedia` is split into `fetch_wikipedia` and
`write_wikipedia`, no other caller); the manifest is saved after each market. `tests/ingestion/test_symbols.py` pins
`to_yfinance_ticker` and `to_yfinance_download_ticker`. Round 1 (tree 935b6d3): scope-auditor and platform-reviewer
PASS. After the PASS verdicts only the two wording fixes changed: the module docstring of the recorder's test file and
the contract's objective (the rule is per market).

Coordinator evidence:
- `pytest tests` 1505 passed, 1 skipped; `check_context_budget.py` passes.
- Mutations, file restored after each: removing the dot-to-hyphen `replace` fails 1 test; writing each ticker file
  before the fetches (the old order) fails 2; saving the manifest once after the loop fails 1.
- `git grep -n "record_wikipedia" -- . ':!.claude/task'` finds nothing.
- No live recording run: the recorder needs the network and is run by hand; the tests replace the network calls.

follow_ups: per-ticker progress lines now print only after a market's fetches finish (as `rerecord_tickers` already
does); `write_wikipedia`, the manifest and the parquet are written non-atomically (the declared local-write limit);
the `to_yfinance_download_ticker` docstring says "US class shares" but the rule keys on an empty exchange suffix (only
`us_sp500` has one today); no seed-level guard enforces the dotted-ticker convention (`BT.A` is taken as a complete
Yahoo symbol).

## scope-auditor

VERDICT: PASS
reviewed_tree: 935b6d3ed90766974fe2cfe9b35afd319c68e4c8
risks_checked:
- Only the four in-scope files changed; no recorded fixture, golden mart or ingestion file is in the diff, and `record_wikipedia` has no other caller.
- Full-mode manifest content is the same keys and sorting as before; only when it is saved changed, and `--ticker` mode is untouched.
wording_fixes: applied (test file docstring, contract objective).

## platform-reviewer

VERDICT: PASS
reviewed_tree: 935b6d3ed90766974fe2cfe9b35afd319c68e4c8
risks_checked:
- A network failure in market N leaves markets 1 to N-1 recorded with a matching manifest, and market N's files, including its Wikipedia file, untouched.
- Each new test would fail if the order regressed (old files carry a marker the new write replaces); no test reaches the network or writes outside `tmp_path`; the symbol tests cover every branch of `symbols.py`.
wording_fixes: none.
