# Review

diff_sha256: af46cbad2688ef547c010d7e6c8d4d100f942a745a5117c726371bed4df2a818
rounds: 2

Guardrail tests for #48. Round 1 (tree 0ccf306): platform-reviewer PASS, scope-auditor FAIL on two
broken guarantees (the layer-contract and SQL-structure tests replaced the real paths and bypassed
`main()`, so disabling a wired check left every test green). Round 2 (tree 2fca3d8, delta only):
both PASS. Wording fixes applied after the round 2 verdicts, no round 3: the contract's `done_when`
and objective no longer carry history, and the criterion is named. equity-analyst-reviewer was not
routed (no catalogue, metric_layer or data_contract change).

Coordinator evidence:
- Before the fixes the R1 test failed on `equity-analyst-reviewer.md` and the R3 test failed on
  `.github/workflows/*`; after, both pass. `equity-analyst-reviewer` then appeared in the session's
  agent list.
- Mutation checks, guard restored after each (`git status` shows `scripts/` clean): dropping the core
  check from `check_layer_contract.main()` fails 3 tests; dropping `dbt_analytics/tests` from
  `check_dbt_sql_structure.SQL_PATHS` fails 1.
- `pytest tests` 1246 passed; `scripts/bootstrap.py --verify` passes; the em-dash check passes.
- The rate-limit message cases use "Too Many Requests" alone so that deleting that clause of
  `is_rate_limited` fails a test (the earlier text also contained "rate limit").

follow_ups (not built; to file as issues if the owner agrees):
- `check_dbt_sql_structure.py`: the scalar-subquery regex is anchored at `^\s*select`, so it cannot fire
  on a model that starts with WITH or with a comment line; fixing it changes a gate.
- GRD-3 allows a pattern documented as dormant; the routing test has no such exemption. Owner picks:
  add a marker (new mechanism) or amend the criterion to the stricter rule.
- The retry test swaps in a fake `YFRateLimitError`; the real yfinance class is not exercised.
- ING-5 beyond `rate_limit.py` (other ingestion rules without a test) is not in this issue.

## Owner answers

CPO ANSWER: recorded for #48. Decision 1: remove the dead routing pattern `.github/workflows/*` and
its comment mention (answer A). Decision 2: add a test that runs `check_registry_var_sync.py` and
keep the existing onboarding test (answer A).

## scope-auditor

VERDICT: PASS
reviewed_tree: 2fca3d8f5c0d79ba97fedaa48d1f04c3d85a9039
risks_checked:
- Round 1 findings resolved: core, intermediate and singular-test cases run through `main()`; the real path constants are asserted.
- All paths in the delta are in scope_paths; no script, hook or ingestion file changed.
- R1, R2, R3, R4 hold; no em-dash on an added line.
wording_fixes: applied.

## platform-reviewer

VERDICT: PASS
reviewed_tree: 2fca3d8f5c0d79ba97fedaa48d1f04c3d85a9039
risks_checked:
- The real-repo assertions are deterministic and duplicate the existing gate signal only.
- The `tracked` fixture, the pre-commit entry check and the registry-sync cases match the scripts' real behaviour.
- The rate-limit message change isolates the "too many requests" clause.
wording_fixes: applied.
