# Review

diff_sha256: 06600667124599dd39ed17cee4414926938cfcefff64a39a4d4366262368baca
rounds: 1

Works #83 (DOC-3 defect 29, DOC-1 defect 30, DOC-2 defects 34 to 37 of the second audit re-run). The scheduled-run
diagram in `docs/operations_guide.md` no longer lists the manual constituent refresh; the pre-revenue company count (3, 11
and 15 stated in six places, two of them a migration comment and a test comment) is replaced by the rule; the history,
measurement log, open to-do and redesign parenthetical are deleted from the five docs the defects name. Round 1 (tree
01162d8): scope-auditor, platform-reviewer, equity-analyst-reviewer, data-engineer-reviewer and
analytics-engineer-reviewer PASS. After the PASS verdicts only wording changed: the rejected-argument sentence and the
`/auth/v1/health` sentence in the monitor paragraph, "rows that each metric actually renders" in
`docs/data_contract.md`, and the reflow of the test comment.

Coordinator evidence:
- `pytest tests` 1515 passed, 1 skipped; `check_context_budget.py` and `check_docs_indexed.py` pass.
- The contract's `done_when` search finds nothing outside `.claude/task` and `tests/fixtures`; `refresh constituents` in
  `docs` finds only the heading `### Refresh constituents`.
- Migration 017 changes in two comment lines; `scripts/apply_supabase_migrations.py` tracks applied files by name only, so
  the edit trips no checksum. The `supabase-migrate` job runs on `main` for any change under `supabase/migrations/` and
  finds nothing pending.

follow_ups: the retained rule "too few pre-revenue companies exist to clear the 8-peer threshold" has no per-sector count
behind it in the repo (a dbt test or audit query would make it fail loudly if the population grew); the measured
pre-revenue ranges in `docs/data_contract.md` carry no sample size now; `docs/supabase_setup.md` 3c says the export
"completes inside 8s" with no measured duration (the export could log the RPC time, an owner call); the scheduled-run
diagram and "Expect:" line in `docs/operations_guide.md` still omit migrations, source freshness and assessments (#75
item 38); `frontend/styles.py:907` carries feedback-round history in a comment.

## scope-auditor

VERDICT: PASS
reviewed_tree: 01162d8964e67e530be1c7850706bbd1e2d6ba4a
risks_checked:
- All ten changed paths are in `scope_paths`; the only owner choice (item 36, delete) is the owner's answer A; no SQL, copy, label or number changed.
- The `done_when` searches hold, the diagram still matches the data-pipeline job order in `.gitlab-ci.yml`, and no doc relied on the dropped 2.87s and 2.8x figures.
wording_fixes: applied (monitor paragraph).

## platform-reviewer

VERDICT: PASS
reviewed_tree: 01162d8964e67e530be1c7850706bbd1e2d6ba4a
risks_checked:
- The test change is comment-only and the assertions below it still match the comment.
- No test reads the removed phrases; the doc readers in `tests/` look at tables and markers this diff does not touch.
wording_fixes: applied (comment reflow).

## equity-analyst-reviewer

VERDICT: PASS
reviewed_tree: 01162d8964e67e530be1c7850706bbd1e2d6ba4a
risks_checked:
- No metric definition, formula, bound or interpretation changed; the 8-peer rule and "Peer threshold" are intact, and peers are grouped by market and sector with `pre_revenue` removed from the peer set.
- "Too few pre-revenue companies to clear the 8-peer threshold" is still a true statement of why the four metrics are unbenchmarked.
wording_fixes: applied ("rows that each metric actually renders").

## data-engineer-reviewer

VERDICT: PASS
reviewed_tree: 01162d8964e67e530be1c7850706bbd1e2d6ba4a
risks_checked:
- Migration 017 changes in two comment lines only; applied migrations are tracked by file name, so no checksum or re-run is affected.
- Section 3c still states true things: one `replace_cards_snapshot` RPC, the 8s `authenticator` timeout as an observation, and a failed export rolls back.
wording_fixes: none.

## analytics-engineer-reviewer

VERDICT: PASS
reviewed_tree: 01162d8964e67e530be1c7850706bbd1e2d6ba4a
risks_checked:
- No SQL statement changed and no dbt model is in the diff; the new wording matches `peer_threshold = 8` and the `pre_revenue` exclusion in `int_stock__sector_benchmarks.sql`.
wording_fixes: none.
