# Review

diff_sha256: f909b3eef3be1d1163ad770e5890dcf6025570801c2e6faa0a2a540df8cdb047
rounds: 1

Refs #52, items 16, 17 and 19 (item 18 is split out by the owner's answer B). Round 1 (tree aa2b18e):
scope-auditor, platform-reviewer and analytics-engineer-reviewer all PASS. Applied after the PASS verdicts,
no round 2: the schema test now rejects any DO block that mentions the table other than the precision-cap
drop of 019 (it skipped every DO block before), reads `alter table only`, skips `exclude` and `references`
lines in a create body, names where to add a missing type mapping, and the ledger test names the heading it
needs; the contract states the second allowlist (`DATABASE_ONLY`: `id`, `exported_at`) and the parser's
limits. Each fix has a test.

Coordinator evidence:
- Real-file mutation checks, file restored after each: `_marts.yml` back to `bigint` makes the schema test fail
  with "sector_peer_count: contract bigint but migrations integer"; removing a ledger row fails the ledger test
  ("015_nl_ch_es_markets.sql: on disk but not in the ledger"); adding an unlisted `099_x.sql` fails it.
- The three exported-column sets: 80 contract columns, 77 exported plus the 3 named in `NOT_EXPORTED`, and 79
  table columns, the 77 plus `id` and `exported_at`.
- `pytest tests` 1400 passed; `scripts/bootstrap.py --verify` passes (dbt build 149 tests); em-dash and
  narrative-date checks pass.

follow_ups: item 18 of #52 (run the migrations and `replace_cards_snapshot` against a throwaway Postgres in CI)
filed as its own issue; `alter table` forms without the `public.` prefix and quoted names are not read by the
schema test (declared in the contract and the docstring).

## scope-auditor

VERDICT: PASS
reviewed_tree: aa2b18e2cbd650ca7ec48a9c9b42da76a59fb974
risks_checked:
- Every edited file is in `scope_paths`; items 16, 17 and 19 match the issue; item 18 is not built.
- The `NOT_EXPORTED` reasons hold against the SQL; the removed ledger sentence has no other copy.
wording_fixes: applied.

## platform-reviewer

VERDICT: PASS
reviewed_tree: aa2b18e2cbd650ca7ec48a9c9b42da76a59fb974
risks_checked:
- The migration parse was traced by hand over all 21 files and equals what the migrations build (79 columns).
- The ledger parse reads the 21 real rows and stops at the next heading.
wording_fixes: applied.

## analytics-engineer-reviewer

VERDICT: PASS
reviewed_tree: aa2b18e2cbd650ca7ec48a9c9b42da76a59fb974
risks_checked:
- The cast sits in the model that creates the value; no downstream model, unit test, fixture or the export changes.
- The mart contract type now matches the Postgres column and `docs/data_contract.md`.
wording_fixes: none.
