# Review

diff_sha256: e1721fc1a9a4ec26e864c724aac456d1ad31987af27fbabc56f074d1b48e958a

Five rounds. Round 1 (three reviewers, no `.sql`/`.yml` touched yet): scope-auditor PASS,
cto-reviewer FAIL, equity-analyst-reviewer FAIL. Round 2 (same three): equity-analyst-reviewer
PASS, cto-reviewer FAIL again on a deeper version of the same class of gap. Round 3
(scope-auditor + cto-reviewer; equity-analyst-reviewer's routed file unchanged since its PASS):
scope-auditor PASS, cto-reviewer FAIL. Round 4 (same two): scope-auditor PASS, cto-reviewer FAIL
on a fresh error introduced by round 3's own fix. Round 5 (same two): both PASS. The hash above
is the final staged hash all round-5 verdicts were rendered against.

## Round 1 findings and how each was resolved

1. **equity-analyst-reviewer FAIL -- overreached regulatory justification.** The first version
   banded `statement_roe_pct` `weak` on `financial` (forcing red outright), reasoned from US bank
   capital regulation (the FDIC's Prompt Corrective Action framework), after web research the
   owner explicitly required ("don't hallucinate, do it like it is done in reality"). Caught that
   this overreached what the data supports: `company_type == 'financial'` is the whole GICS
   "Financial Services" sector (insurers, asset managers, broker-dealers, payment networks,
   exchanges, mortgage finance, not only depository banks), spans nine markets under entirely
   different regulatory regimes, and includes firms (payment networks especially) known for the
   same benign buyback-driven negative equity operating companies can have -- exactly the case
   the original reasoning itself said should get the mild treatment. Fixed: changed the
   financial-type `bad_band` from `"weak"` to `"unknown"`, which still blocks green without
   forcing red, matching the neutral treatment every other axis gets for undeterminable
   information.
2. **cto-reviewer FAIL -- confounded test.** `test_operating_statement_roe_guard_caps_a_
   negative_equity_card_at_yellow` did not test the property it claimed -- confirmed by mutation
   testing (reverting only the new guard left the test passing identically) because
   `debt_to_equity`'s own, already-merged guard checks the SAME `stmt_stockholders_equity` field
   unconditionally and alone already explains the yellow outcome. Fixed: added a direct
   function-level test calling `_axis_unless_denominator_nonpositive` directly with each verdict
   function's actual parameters.

## Round 2 finding and how it was resolved

3. **cto-reviewer FAIL -- the round-1 fix didn't close the actual gap.** The direct
   function-level test proved the shared guard function works in isolation, but never called
   `_verdict_operating` at all, so it provided zero protection against the operating call site
   itself being silently reverted -- confirmed by mutation testing (reverting the call site left
   ALL 75 tests passing, including both the confounded verdict-level test and the new isolated
   function-level test). Root cause: because `debt_to_equity`'s guard fires unconditionally
   whenever `stmt_stockholders_equity` is negative, independent of `debt_to_equity`'s own value or
   presence, NO row constructible through `compute_verdict` can ever isolate `statement_roe_pct`'s
   call site from `debt_to_equity`'s. Fixed: added
   `test_operating_statement_roe_call_site_is_actually_wired`, using `pytest`'s `monkeypatch`
   fixture to neutralize `debt_to_equity`'s guard specifically while leaving `statement_roe_pct`'s
   call to the real guard, then driving the row through `compute_verdict` -- genuinely exercises
   `_verdict_operating`'s actual code path. Also fixed a stale line in the backlog doc's Related
   section, left over from the rejected "financial forces red" version.

## Round 3 finding and how it was resolved

4. **cto-reviewer FAIL -- stale shared comment.** The module-level "Ratio sign-inversion guards"
   preamble comment (untouched by any hunk in the diff until this point) still said "Two
   operating-type ratios" / "Both guards," undercounting the third guarded metric
   (`statement_roe_pct`, used from both verdict functions with a role-dependent band) this task
   added, and contradicting the correctly-updated `docs/data_contract.md`. Fixed: rewrote the
   preamble to count three guarded metrics across four call sites and explain
   `statement_roe_pct`'s dual role.

## Round 4 finding and how it was resolved

5. **cto-reviewer FAIL -- a fresh factual error introduced by the round-3 fix.** The rewritten
   preamble claimed `statement_roe_pct`'s numerator (net income) "is never negative" -- false, a
   loss is the entire premise of the bug this guard exists to catch, and the claim directly
   contradicted the preamble's own opening lines. Root cause: over-generalized `debt_to_equity`'s
   true "numerator never negative" property across to `statement_roe_pct` while merging the two
   explanations into one sentence. Fixed: rewrote the paragraph to describe three genuinely
   distinct failure modes separately (net_debt_to_ebitda: numerator can be negative;
   statement_roe_pct: numerator can also be negative, same double-negative ambiguity, which is
   why the guard keys on equity's sign alone; debt_to_equity: numerator never negative but can be
   exactly zero, a distinct third failure mode).

## scope-auditor
VERDICT: PASS
risks_checked:
- Re-verified every factual claim in the final preamble against the actual code, the dbt column
  comments in `int_stock__card_metrics.sql`, and `metric_catalogue.csv`'s applicability text --
  the round-4 defect is corrected and no new factual error survives in the same paragraph.
- Swept the whole repo (not just `scope_paths`) across multiple rounds for the same staleness
  pattern; found two further low-severity, out-of-scope instances
  (`scripts/generate_assessments.py`'s comment, `dbt_analytics/models/4_intermediate/_intermediate.yml`'s
  `stmt_stockholders_equity` description) -- both correctly disclosed in `impact_map` as deferred,
  not silently dropped.
- Independently re-verified the call-site count (4 across 3 metrics) by grepping the actual code
  rather than trusting the comment's own claim.
- Re-ran `pytest` at each round rather than trusting the contract's claimed counts -- always
  matched (459 passed on the full suite by the final round).
- Confirmed `scope_paths`, `done_when`, and cross-doc consistency (contract, `docs/data_contract.md`,
  backlog doc) hold at every round, with no silently-taken owner-level decision.

## cto-reviewer
VERDICT: PASS
risks_checked:
- Mutation-tested every guard boundary and call site across all five rounds: the operating and
  financial `statement_roe_pct` call sites, the monkeypatch-based wiring test's actual
  interception of `_verdict_operating`'s call (verified via CPython's late-binding global lookup
  semantics, not just assumed), and the floor/coverage boundaries inherited from prior fixes.
- Verified the final preamble's three failure-mode claims sentence by sentence against the real
  SQL numerator/denominator expressions in `int_stock__card_metrics.sql` -- each holds, and the
  three explanations no longer contradict each other or the per-call-site comments.
- Confirmed the direct function-level test and the monkeypatch wiring test both actually prove
  the property they claim, via live mutation (revert the guard, confirm the specific test fails,
  restore, confirm the suite is green again) rather than reading the assertions and assuming.
- Ran the full test suite directly at every round -- 459 passed, 0 regressions, matching the
  contract's claims exactly.

## equity-analyst-reviewer
VERDICT: PASS (round 2; unchanged since -- `docs/data_contract.md` was not touched in rounds 3-5)
risks_checked:
- Independently verified the corrected `"unknown"` treatment is genuinely defensible: it reuses
  the SAME semantics `_band` already assigns a genuinely missing value, not an invented severity
  tier, and there is no other signal in this dataset (capital-adequacy data is explicitly
  unsourceable from yfinance) to condition severity on -- the most defensible choice available.
- Confirmed no residual trace of the rejected bank-specific regulatory justification is used to
  support the CURRENT (not the rejected) severity anywhere in the diff.
- Cross-checked `docs/data_contract.md`'s reworded prose against the shipped code line by line --
  no overclaiming found.
