# Review

diff_sha256: 7cbb866b58594027ff570aca0766ad1696d2387500c76d3ea008da1470868ab0
rounds: 3

Works #75 (items 38 to 52), #70 (ING-3), #79 (DOC-3) and #18 (DOC-1) of the second audit re-run. Round 1 (platform and
scope-auditor FAIL on the deleted `_fetch_pooler_host_port` still imported by `scripts/print_supabase_pooler_config.py`;
data-engineer PASS) led to deleting the helper; round 2 (tree bd4f528): equity-analyst and platform PASS, scope-auditor
ESCALATE on the helper deletion; the owner answered A (delete). Round 3 (tree ecc389c): scope-auditor PASS. After the PASS
verdicts only wording changed: the direct-host sentence in `docs/operations_guide.md` and the `ANTHROPIC_API_KEY` row in
`docs/supabase_setup.md`.

Coordinator evidence:
- `pytest tests` 1521 passed, 1 skipped; `check_context_budget.py`, `check_docs_indexed.py` and `check_no_em_dash.py` pass.
- The contract's `done_when` search (plus `SUPABASE_ACCESS_TOKEN`) finds nothing outside `.claude/task`, `.claude/active_work.md` and `tests/fixtures`.
- The ingest test fails on the old code (mutation-checked).
- Not exercised: the Management API deletion against a live Supabase project; the CI jobs use `SUPABASE_DB_HOST`, the first resolution step, which is unchanged.

follow_ups: a test that sets `SUPABASE_DB_POOLER_URL` (pooler URL beats the direct host); a smoke test importing every
`scripts/*.py` (an unused import would have caught the round-1 failure); tests for the column-mismatch reset with a failing
write and for an empty row whose write fails; `scripts/discover_supabase_db_host.py:6` docstring says "GitHub secret
values"; measurement figures still in `docs/data_contract.md` (roa_pct, current_ratio_stmt, dividend_yield, fill-floor,
ch_smi count); `frontend/styles.py:279` and `:907` carry history in comments; `frontend/metrics.json` columns
`importance_tier` and `basis_column` stay (tracked in #57).

## scope-auditor

VERDICT: PASS
reviewed_tree: ecc389c8babbcab30cea16525f05b2eec7abf379
risks_checked:
- The round-3 delta touches only paths in `scope_paths`; the helper deletion is recorded as the owner's answer (1b).
- The direct-host sentence matches `resolve_database_url`; a repo-wide grep finds no dangling `SUPABASE_ACCESS_TOKEN` or Management API reference.
wording_fixes: applied (`SUPABASE_DB_POOLER_URL` named, "fails with an error that asks for", scope of the blanked key).

## platform-reviewer

VERDICT: PASS
reviewed_tree: bd4f528b1b8687d7a2048461d50ab4ee885b716a
risks_checked:
- The `resolve_database_url` tests are hermetic and pin the order; no script imports the deleted function.
- Routed files (`scripts/*`, `tests/*`, `.claude/working-agreement.md`) are unchanged since this verdict.
wording_fixes: none.

## equity-analyst-reviewer

VERDICT: PASS
reviewed_tree: bd4f528b1b8687d7a2048461d50ab4ee885b716a
risks_checked:
- No metric definition, formula or accepted_range bound changed in `docs/data_contract.md` or `docs/metric_layer.md`.
wording_fixes: applied (1,000 months).

## data-engineer-reviewer

VERDICT: PASS
reviewed_tree: 4f21ad6086b56799f31e9e52a1ed2cf19fa5b424
risks_checked:
- A failed checkpoint write drops the row so a ticker is counted once; `ingestion/yfinance/ingest.py` and `tests/ingestion/test_ingest_resume.py` are byte-identical in every later tree.
wording_fixes: applied.
