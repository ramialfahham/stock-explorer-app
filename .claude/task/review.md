# Review

diff_sha256: 89339888075d4c88d5a7bc74c0bd5e86ca929c016916ab2ee52b3e1154bdc5fd
rounds: 1

Repo hygiene, findings 49-55 of the quality audit (issue #50) plus the extra copies the same rules found.
Round 1 (tree c4681df, the full cumulative diff): scope-auditor, platform-reviewer, data-engineer-reviewer
and analytics-engineer-reviewer all PASS. Applied after the PASS verdicts, no round 2: the stale `_esc()`
in a `card_copy.py` comment (sweep R6 now searches `_esc` and `_sql_model_names`); two test cases the
reviewers asked for (rows are counted as given; a required ticker with an empty summary), direct tests for
`esc` and `sql_model_names`, and an import test that allows only `ingestion.paths` / `ingestion.registry`
and handles relative imports; the registry test docstring and the contract's keep list and known limits
reworded; the handover says "done on branch" instead of "in an open MR". Final tree 669aac9.

Coordinator evidence:
- `hygiene_sweep.py`: 50 hits before the work, 0 after. Mutation checks, file restored after each: an
  unsorted `active_market_codes`, the old gate wording, `esc` without None handling, a non-recursive
  `sql_model_names`, a removed empty-summary check each fail 1 to 3 tests; the stale `_esc` comment
  makes the sweep print 1 hit.
- `pytest tests` 1357 passed; `scripts/bootstrap.py --verify` passes (pre-commit on all files, sqlfluff,
  dbt build 149 tests); budget, doc-index, narrative-date and em-dash checks pass.
- The pinned set of `requirements.txt` + `frontend/requirements.txt` is identical to HEAD (17 pins).
- Issues #51, #52 and #55 are separate open issues (checked live); their titles differ from this one.

follow_ups (not filed; the owner says which to file):
- The health gate now relies on the dbt unique test on `mart_stock_cards`; owner call whether the gate
  asserts uniqueness itself.
- `PyYAML` is pinned in `.pre-commit-config.yaml` and `requirements.txt`; R4 does not read the hook config.
- The 3-line `sys.path` block is copied in 17 scripts; R1 compares function bodies only.
- `load_markets` errors: a missing `index_name` surfaces as a bare `KeyError`, a blank `market_code`
  becomes "None", a missing `markets` key gives `[]`.
- Four scripts and two tests build the active-code set inline from `load_markets(active_only=True)`.
- `GITHUB_ACTIONS` in `scripts/apply_supabase_migrations.py` (owner decision, in the handover).

## Owner answers

CPO ANSWER: acknowledged. The owner answered A to all three scope questions in chat: delete
`probe_quarterly_op_labels.py`; delete the health check's own dedupe (log wording shown to the owner
beforehand); include the extra copies the rules found. Then "go". No FAIL stands.

## scope-auditor

VERDICT: PASS
reviewed_tree: c4681df8ad6ffe0108beba6084f269b4b4b321ad
risks_checked:
- All 29 files are in `scope_paths`; no change to the frozen assessment, verdict, dbt, migration or export files.
- The three owner decisions match the diff; the `GITHUB_ACTIONS` branch is left alone and recorded.
wording_fixes: applied.

## platform-reviewer

VERDICT: PASS
reviewed_tree: c4681df8ad6ffe0108beba6084f269b4b4b321ad
risks_checked:
- Each script importing `ingestion.registry` starts from the repo root and from the PyYAML-only hook.
- The CI pytest install line fails closed; the pinned set is unchanged; the new log wording is test-pinned.
wording_fixes: applied.

## data-engineer-reviewer

VERDICT: PASS
reviewed_tree: c4681df8ad6ffe0108beba6084f269b4b4b321ad
risks_checked:
- `active_market_codes()` returns what the seven removed copies returned, in the same sorted order.
- No ingestion or production-job path behaves differently; stricter registry parsing is declared.
wording_fixes: applied.

## analytics-engineer-reviewer

VERDICT: PASS
reviewed_tree: c4681df8ad6ffe0108beba6084f269b4b4b321ad
risks_checked:
- The deleted CSV has no reader and its 116 pairs are all in `jp_nikkei225/constituents.csv`.
- `mart_stock_cards` is unique per market and ticker (dbt test), so the removed dedupe was a no-op.
wording_fixes: applied.
