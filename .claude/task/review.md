# Review

diff_sha256: 6868587c75ac6092c5b5b2727d6cb2cc6fcf98079d201faca42e10e5b9aae8a8
rounds: 2

Closes #43 and works #71 items 1 to 6 (items 7 to 9 are owner calls, untouched). Round 1 (tree 5a387dc):
platform-reviewer PASS, data-engineer-reviewer PASS, equity-analyst-reviewer PASS, scope-auditor ESCALATE with
three owner questions about empty-row counting and storage. Round 2 (tree 89546f4) after the owner's answers:
all four PASS. Applied after the PASS verdicts, no round 3: a test pins that ok, failed, skipped and empty add up
to the requested tickers, the handover no longer lists the settled #43 question, the contract says where the
same-day-resume limit is filed.

Coordinator evidence:
- Mutations of the fixes and guards, file restored after each, 25 in all: seed written in place, helper leaving
  the temp file, helper writing the target directly, snapshot written in place, previous row not kept, kept and
  no-name counts, empty row not counted, one-field row counted empty, empty also counted ok, counter not
  printed, tickers not named, six `main()`/seed/refresh guards removed, refresh failure swallowed, no-target
  returning 0, two import column guards removed. Each fails a test.
- `pytest tests` 1439 passed; `scripts/bootstrap.py --verify` passes (dbt build 149 tests); em-dash,
  narrative-date and context-budget checks pass.

follow_ups (added to #70, filed with the merge request): same-day resume does not recount or name empties already
in the checkpoint; a failed file write after a row is appended can count one ticker as both ok/empty and
failed (present before this branch); the exit-1 guard "No provider:wikipedia markets selected." in
`scripts/refresh_yfinance_names.py` has no test; `scripts/backfill_fundamentals_parquet_schema.py` writes parquet
directly; a hand-edited name snapshot without the expected header raises `KeyError`, and a whitespace-only name is
accepted; the data contract does not say an empty row replaces the previous card (context budget is full).

## Owner answers

CPO ANSWER: the owner's chat answers to the three scope-review questions. Q1 B: an empty row leaves
`fundamentals_ok`, so ok, failed, skipped and empty add up. Q2 A: the empty row replaces the ticker's previous
fundamentals row as before, no keep-previous step. Q3 A: the log wording stays as built. Earlier answers: one
shared atomic-write helper for the seed CSV and the name snapshot (A, closes #43); the empty-row counter does not
count toward the 5% line (A); a failed or nameless ticker keeps its previous snapshot row (A). No FAIL stands.

## scope-auditor

VERDICT: PASS
reviewed_tree: 89546f451fea9d507ad510fec849f73c8b93eb21
risks_checked:
- The three owner answers are applied consistently in code, tests and docs; every file is in `scope_paths`.
- No new owner-level decision; items 7 to 9 of #71 are untouched.
wording_fixes: applied.

## platform-reviewer

VERDICT: PASS
reviewed_tree: 89546f451fea9d507ad510fec849f73c8b93eb21
risks_checked:
- The shared fixture change does not weaken the resume or schema-mismatch tests; the patched-network guard test cannot reach the network.
- The nameless-ticker parametrization separates `not x` from `is None`.
wording_fixes: none.

## data-engineer-reviewer

VERDICT: PASS
reviewed_tree: 89546f451fea9d507ad510fec849f73c8b93eb21
risks_checked:
- The counting split holds on the normal, skipped, failed and mismatch re-queue paths; nothing else reads `fundamentals_ok`.
- The 5% gate and exit code are unchanged; the atomic-write docstring matches the code.
wording_fixes: none.

## equity-analyst-reviewer

VERDICT: PASS
reviewed_tree: 89546f451fea9d507ad510fec849f73c8b93eb21
risks_checked:
- The data contract sentence is true against `ingest.py` and `main.py` and does not mislead next to the failed-ticker sentences.
- An all-null row cannot become a card.
wording_fixes: none.
