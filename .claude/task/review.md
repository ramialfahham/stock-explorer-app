# Review

diff_sha256: 1095662f7c38ba72297384021c531ab2b4ca771fafb9c1103bfbb191bbf578a5
rounds: 1

Works #75 (DOC-3 defects 32 and 33; the owner calls 34 to 52 are untouched). `docs/streamlit_deploy.md` no longer
claims three headline metrics and a "More metrics" section (it points at `north_star.md`); `docs/data_contract.md`
merges the "Current (Phase B baseline)" and "Planned (fundamentals)" tables into one "Files" table and drops the
"News (Phase 2)" freshness row; `docs/project_context.md` drops "(Phase B)". Round 1 (tree 0a7ba5a):
scope-auditor and equity-analyst-reviewer PASS. No edits after the PASS verdicts.

Coordinator evidence:
- Facts behind the deletions, checked against the code: `ingestion/yfinance/ingest.py` writes `yf_fundamentals.parquet`
  on every run; no news job exists in `.gitlab-ci.yml` or `scripts/`, and Saved-tab headlines are fetched on demand
  (`frontend/saved_news.py`, `docs/operations_guide.md` line 51); the frontend has no "More metrics" section.
- The done_when searches find nothing for "Phase B", "Planned (fundamentals)", "News (Phase 2)", "More metrics" or
  "three headline metrics" in docs, frontend, scripts and tests; `yf_fundamentals.parquet` is still named in
  `docs/data_contract.md` and `docs/project_context.md`.
- `pytest tests` 1482 passed, 1 skipped; `check_context_budget.py`, em-dash and narrative-date checks pass.

follow_ups (filed as an issue): the Freshness table row "Daily prices | Every two weeks or daily (supporting only)"
in `docs/data_contract.md` names a daily cadence that no schedule runs (the pipeline runs on the 1st and 15th); the
scope-auditor's wording is "Every two weeks (supporting only)". It is a different claim from the two defects, so it
is not in this diff.

## scope-auditor

VERDICT: PASS
reviewed_tree: 0a7ba5a1832d01ed5a0bb8ad16b38fb4944d84b5
risks_checked:
- The deleted claims are false against the code: the fundamentals file is written every run, no news workflow exists, the frontend has no "More metrics" section.
- No other copy of the changed claims is left, and nothing referenced the removed headings.
wording_fixes: none applied; the one suggested (the daily-prices cadence) is a separate claim, listed under follow_ups.

## equity-analyst-reviewer

VERDICT: PASS
reviewed_tree: 0a7ba5a1832d01ed5a0bb8ad16b38fb4944d84b5
risks_checked:
- The merged table keeps all three files with grain and notes; the field-mapping section depends on no removed heading.
- The Freshness table's remaining rows are unchanged; no metric, eligibility or verdict text changed.
wording_fixes: none.
