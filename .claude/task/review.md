# Review

diff_sha256: 676da00bb79b04bf9f8d20fbc5f2a831653554f4449368ff15179d4708bb8025

Two rounds. Round 1 (hash db9d2f8b02726c3e7abd8fd9ec3a5e144f1f69ce0b29768a15f69134ca169c7c):
scope-auditor / cto-reviewer / analytics-engineer-reviewer PASS, equity-analyst-reviewer FAIL on
three findings (see below). All three findings fixed; round 2 (hash
b0065325918f11d2e4c1505da180bfbd83405bc2200773958e86018fcf81fa03) got PASS from all four. The
hash above is the FINAL staged hash, one wording-only touch-up to `.claude/active_work.md` after
round 2 (fixing a test-count miscount scope-auditor itself flagged in round 2) -- no reviewer
routes to that file beyond scope-auditor's "always" rule, and the fix matches exactly what
scope-auditor suggested, so this was not re-dispatched as a third full round.

## Round 1 findings (equity-analyst-reviewer FAIL) and how each was resolved

1. **Overclaiming.** `docs/data_contract.md`'s prose called negative `debt_to_equity` "a real
   solvency concern," stated as fact, when the metric catalogue's own applicability text
   attributes negative equity partly to "heavy buybacks" -- a benign, common pattern among the
   mature large-caps this app covers, not necessarily distress. Fixed: reworded in
   `docs/data_contract.md`, `scripts/assessment_rules.py`'s guard-section comment, and the
   backlog doc to frame `weak` as a deliberate caution given the two causes can't be
   distinguished from the data available, not a claim about which one it is.
2. **Real logic gap.** The guard checked `debt_to_equity`'s own sign to detect negative equity,
   but `stmt_total_debt` (the ratio's numerator) can be exactly zero, and zero divided by any
   nonzero number is zero, not negative -- a debt-free company with negative equity would
   silently evade the guard and keep banding "good". Fixed: added a second raw-denominator
   passthrough column, `stmt_stockholders_equity` (mirroring the existing `info_ebitda` pattern
   for `net_debt_to_ebitda`), end to end through `int_stock__card_metrics.sql` ->
   `mart_stock_cards.sql` -> `generate_assessments.py`'s `ASSESSMENT_INPUT_COLUMNS`. Generalized
   the guard into one function, `_axis_unless_denominator_nonpositive` (now taking the band to
   apply as a parameter), used for both metrics, checking each ratio's actual denominator
   directly, never the ratio's own sign. New test
   `test_debt_to_equity_guard_checks_equity_directly_not_the_ratios_sign` proves the specific
   edge case (`debt_to_equity == 0.0`, `stmt_stockholders_equity` negative) is now caught.
3. **Internal inconsistency.** `.claude/task/contract.md`'s `impact_map` claimed "none moves
   toward a WORSE color than the guard's own 'unknown, neutral' treatment would justify," which
   contradicted the contract's own `amendments` section explaining `debt_to_equity` was banded
   `weak` specifically BECAUSE `unknown` would have been a no-op (i.e. `weak` demonstrably is a
   worse color for some cards). Fixed: `impact_map` corrected to state the two guards land
   differently (`net_debt_to_ebitda` -> `unknown` is neutral; `debt_to_equity` -> `weak` is a
   real demotion).

Also surfaced during round 1 fix-up, not fixed here (see `.claude/task/contract.md`'s
`amendments` and `docs/backlog/gemini_verdict_feedback.md`): `statement_roe_pct` uses the same
`stmt_stockholders_equity` denominator and has the identical sign-ambiguity problem, already
documented as an accepted, unaddressed output by an existing dbt unit test
(`card_metrics_statement_metrics_negative_equity`). Out of this task's confirmed scope.

## scope-auditor
VERDICT: PASS
risks_checked:
- All 11 changed files fall inside `scope_paths`; no file outside the contract touched.
- Round-1 finding 1 (overclaim) confirmed fixed by re-reading the corrected prose against the
  catalogue's own applicability text.
- Round-1 finding 2 (debt-free/negative-equity edge case) confirmed fixed by tracing
  `_axis_unless_denominator_nonpositive` against the specific `debt_to_equity == 0.0,
  stmt_stockholders_equity == -500.0` case and confirming via `pytest` and `dbt build`.
- Round-1 finding 3 (impact_map self-contradiction) confirmed fixed by re-reading `impact_map`
  and `amendments` side by side.
- Ran `pytest` (442 passed) and `dbt build --select int_stock__card_metrics mart_stock_cards`
  (19 unit tests + 20 data tests + 2 models, all green) directly, not on trust.
- Scanned every added line for em/en dash bytes -- zero matches.

## cto-reviewer
VERDICT: PASS
risks_checked:
- Confirmed `_axis_unless_denominator_nonpositive` checks the raw denominator via `row.get(...)`
  directly, never the ratio's own sign, at both call sites in `_verdict_operating`.
- Hand-traced the debt-free/negative-equity edge case end to end and confirmed the new test
  exercises it correctly; old ratio-sign-only logic would have failed this test, new logic
  passes it.
- Verified `ASSESSMENT_INPUT_COLUMNS` wiring for both `info_ebitda` and `stmt_stockholders_equity`
  is correct with no double-counting and no Supabase export leak
  (`build_assessment_records`'s explicit field list omits both).
- Ran the full test suite directly: all passed, including all new sign-guard tests, no
  regression from the generalized guard function's new `bad_band` parameter.
- Grepped touched files for any remaining sign-as-denominator-proxy pattern -- none found;
  `statement_roe_pct`'s identical latent bug is honestly disclosed as out of scope, not silently
  left looking fixed.

## analytics-engineer-reviewer
VERDICT: PASS
risks_checked:
- `stmt_stockholders_equity` placement and documentation in `int_stock__card_metrics.sql`,
  `_intermediate.yml`, `mart_stock_cards.sql`, and `_marts.yml` matches the established
  `info_ebitda` pattern exactly (data-only, not catalogued, not exported).
- Confirmed directly (not asserted) that `scripts/export_to_supabase.py`'s `EXPORT_COLUMNS` and
  `dbt_analytics/seeds/metric_catalogue.csv` are untouched and free of both new column names.
- Ran `dbt build --project-dir dbt_analytics --profiles-dir .` directly: 122/122 PASS, 0 ERROR,
  including the pre-existing `card_metrics_statement_metrics_negative_equity` unit test.
- Verified the `statement_roe_pct` sibling-bug claim in the backlog doc is accurate: the bug is
  real (confirmed against the existing dbt unit test fixture), the doc note exists, and the code
  is genuinely untouched -- no partial or inconsistent fix.

## equity-analyst-reviewer
VERDICT: PASS
risks_checked:
- Re-verified the reworded `docs/data_contract.md` prose against the metric catalogue's own
  applicability text directly -- no longer asserts distress as fact, correctly hedged.
- Independently traced the zero-debt/negative-equity edge case through
  `int_stock__card_metrics.sql` -> `mart_stock_cards.sql` -> `generate_assessments.py` ->
  `_axis_unless_denominator_nonpositive`, confirming the guard now fires on the raw denominator
  regardless of the ratio's own value.
- Confirmed a missing (not just non-positive) denominator still bands normally by magnitude for
  both guards, matching every other axis's missing-means-unknown convention.
- Confirmed `weak` cannot force RED on its own for a supporting axis, so
  `docs/data_contract.md`'s "never forcing red on its own" claim is accurate.
