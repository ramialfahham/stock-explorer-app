# Review

diff_sha256: 7fe95bb1c9c46d19080a2f72242d6cd605ef379c75502387e6ae5c35b44b1e37
rounds: 1

Issue #36. Round 1 on the cumulative diff (tree 571eb06): data-engineer-reviewer,
platform-reviewer and scope-auditor PASS.

Coordinator evidence: `pytest tests` 1089 passed. With the three source files reverted, 9 new
or changed tests fail (writer count, four empty-name cases, NA ticker override, TSX 60 count,
both import tests); the OBX prefix test passes either way, the strip predating this branch.

## data-engineer-reviewer

VERDICT: PASS
reviewed_tree: 571eb06897797b6cbe1497b86b76300ad4eabd86
risks_checked:
- The unnamed-row check runs after the ticker drop and dedupe and before any write, so a
  refused run leaves the previous seed untouched.
- Both entry points fail loudly: the import exits 1, the refresh loop reports the market as
  failed and exits 1 without blocking other markets.
- No committed seed has an empty company name; every recorded page replays through the
  new writer.
follow_ups:
- Dedupe keeps the first row per ticker, so an unnamed first duplicate raises even if a later
  one is named (stricter, loud, not a failure).

## platform-reviewer

VERDICT: PASS
reviewed_tree: 571eb06897797b6cbe1497b86b76300ad4eabd86
risks_checked:
- The null-name check relies on pandas 3 keeping NA through `astype(str)`; `requirements.txt`
  pins 3.0.3 and `test_clean_company_name_does_not_invent_a_name_for_a_null` fails on a
  downgrade.
- Each new test fails when its fix is reverted; no caller of the old Path return remains.
- No dependency, hook, workflow, credential or cost change.
follow_ups:
- The import script prints the path from its own import-time `seed_path` binding (harmless
  in tests, low priority).

## scope-auditor

VERDICT: PASS
reviewed_tree: 571eb06897797b6cbe1497b86b76300ad4eabd86
risks_checked:
- `NA` survives import, override lookup and the recorded TSX 60 page.
- Empty, blank and null names are refused before the write; the import exits 1.
