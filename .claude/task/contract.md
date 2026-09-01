# Task contract

objective: Fix the `statement_roe_pct` sign-ambiguity bug flagged (but not fixed) while shipping
  MR !73's `debt_to_equity` fix: `statement_roe_pct = stmt_net_income_common /
  stmt_stockholders_equity * 100.0`, guarded only against `stmt_stockholders_equity != 0`, has the
  identical sign-inversion problem `debt_to_equity` had -- a loss over negative equity divides out
  to a spuriously POSITIVE percentage, which the deterministic verdict then bands by raw
  magnitude. The metric catalogue's own applicability text already says so verbatim: "Misleads
  when equity is thin or negative: a loss over negative equity can read as a spuriously positive
  percentage... Means something different for banks." An existing dbt unit test
  (`card_metrics_statement_metrics_negative_equity`) already documents the raw SQL output
  (`statement_roe_pct: 20.0` from a loss over negative equity) as an accepted, unaddressed case.

  `statement_roe_pct` is used in TWO verdict functions with DIFFERENT roles. Shipped mechanism
  (see amendments for how this changed from the first, reviewer-failed version):
  `_verdict_operating` treats it as a SUPPORTING axis (same role `debt_to_equity` had) -- banded
  `weak` when `stmt_stockholders_equity` is present and `<= 0`, capping the card at yellow, never
  forcing red on its own. `_verdict_financial` treats it as effectively a CORE axis (`good` is
  required for green; only `weak` forces red) -- banded `unknown` instead: an `unknown` roe still
  blocks green (it is never `good`) but does not force red the way `weak` would. `unknown`, not
  `weak`, because `company_type == 'financial'` spans a heterogeneous, multi-jurisdiction
  population (insurers, asset managers, broker-dealers, payment networks, exchanges, mortgage
  finance, not only depository banks, across nine markets with very different bank regulators)
  the data cannot distinguish "genuine distress" from "a payment network mid-buyback" within.

scope_paths:
  - scripts/assessment_rules.py
  - tests/tooling/test_assessment_rules.py
  - docs/data_contract.md
  - docs/backlog/gemini_verdict_feedback.md
  - .claude/task/contract.md
  - .claude/task/review.md
  - .claude/active_work.md

decisions_reserved: none for the shape of the fix -- the mechanism (reuse the existing
  `_axis_unless_denominator_nonpositive` guard, no new function, no new dbt column since
  `stmt_stockholders_equity` already flows end to end from MR !73) was explicitly confirmed by
  the owner this session, who also explicitly required the reasoning be verified against real
  practice rather than assumed. The specific band for the financial-type consequence changed
  mid-task (weak/forces-red -> unknown/blocks-green-only; see amendments) after a review round
  found the original band's justification did not actually hold for the population it was applied
  to. This DOES change verdicts already shown to users: any operating OR financial card with
  negative `stmt_stockholders_equity` no longer gets a false assist from a spuriously positive
  ROE; financial cards specifically can no longer reach green on this basis, though (per the
  correction) they are no longer forced to red by it alone either.

done_when:
  - `scripts/assessment_rules.py`: `_verdict_operating`'s `statement_roe_pct` call replaced with
    `_axis_unless_denominator_nonpositive(row, "statement_roe_pct", "stmt_stockholders_equity",
    "weak", weak_th=0.0, good_th=10.0)` (unchanged thresholds, just routed through the guard).
    `_verdict_financial`'s `statement_roe_pct` call replaced the same way but with `"unknown"` as
    the band (see amendments), keeping its own existing thresholds (`weak_th=0.0, good_th=8.0`).
    No new function -- the guard already exists and is generic over which band to apply when the
    denominator is nonpositive.
  - `tests/tooling/test_assessment_rules.py`: a direct function-level test isolating the guard
    mechanism from `debt_to_equity`'s own guard on the same shared denominator (both key off
    `stmt_stockholders_equity`, so a `compute_verdict`-level test alone cannot isolate this
    guard's own effect on operating cards -- see amendments), plus verdict-level cases per
    function proving a real outcome change (operating caps at yellow; financial blocks green
    without forcing red, and a genuinely weak margin still independently forces red), a case per
    function confirming a genuinely healthy card (positive equity) is unaffected, and a case per
    function confirming a MISSING `stmt_stockholders_equity` does not trigger the guard.
  - `docs/data_contract.md`'s verdict-rules section documents both guards (operating and
    financial), including why the financial consequence is `unknown` rather than `weak`.
  - `docs/backlog/gemini_verdict_feedback.md` updated: the sibling-bug note left in MR !73's entry
    marked acted on, with a pointer to this branch.
  - `pytest` green. No dbt changes needed -- `stmt_stockholders_equity` already reaches the Python
    layer for every row regardless of company_type (MR !73).
  - No em dash or en dash on any added line.

impact_map:
  - Changes verdicts for real cards: any operating-type company with negative
    `stmt_stockholders_equity` no longer gets a false assist toward green on the ROE axis (caps
    at yellow instead, same as `debt_to_equity`'s existing treatment). Any financial-type company
    with negative `stmt_stockholders_equity` can no longer reach green on this basis (roe blocked
    from `good`), but is not forced to red by it alone -- corrected from an earlier version that
    would have forced red (see amendments).
  - Requires re-running the pipeline (dbt build not needed this time since no dbt file changes;
    `scripts/generate_assessments.py` re-run against real data) to actually recompute production
    verdicts against the fix -- not something `pytest` alone verifies.
  - No frontend change; the card face already shows whatever `statement_roe_pct` value the mart
    computes, unchanged by this fix (only the internal verdict-banding interpretation changes).
  - Known, explicitly out of scope: `frontend/card_copy.py`'s `metric_gloss()` has no
    value-aware negative-equity branch for `statement_roe_pct` yet (unlike `debt_to_equity` and
    `net_debt_to_ebitda`, which do) -- a display-layer change, not touched here, matching the
    precedent that display-layer fixes are separate from verdict-engine fixes.
  - Also known, explicitly out of scope: `scripts/generate_assessments.py:56-63`'s comment above
    `ASSESSMENT_INPUT_COLUMNS` still says "two sign-inversion guards" -- stale by the same
    undercount `scripts/assessment_rules.py`'s own preamble had (see amendments), caught by
    cto-reviewer in round 3 as a non-blocking collateral note since that file is not in
    `scope_paths`. Confirmed no functional gap: `info_ebitda` and `stmt_stockholders_equity` are
    both already unconditional in `ASSESSMENT_INPUT_COLUMNS`, not company_type-gated, so the data
    wiring itself is correct -- comment-only staleness, left for a future pass.

amendments:
  - Round-1 review: equity-analyst-reviewer and cto-reviewer both FAILED the first version of
    this diff; scope-auditor PASSED. (1) equity-analyst-reviewer: the first version banded
    `weak` on `financial` (forcing red outright), reasoned from US bank capital regulation (the
    FDIC's Prompt Corrective Action framework). Caught that this overreached what the data
    supports: `company_type == 'financial'` is not "bank" -- it is the whole GICS "Financial
    Services" sector (insurers, asset managers, broker-dealers, payment networks, exchanges,
    mortgage finance), spans nine markets under entirely different regulatory regimes (US, UK,
    Japan, Australia, Germany, France, Netherlands, Switzerland, Spain), and includes firms
    (payment networks especially, e.g. Visa/Mastercard-style buyback patterns) known for the
    same benign buyback-driven negative equity operating companies can have -- exactly the case
    the original reasoning itself said should get the mild treatment, not the harsh one. Fixed:
    changed the financial-type `bad_band` from `"weak"` to `"unknown"`, which still blocks green
    (an `unknown` roe is never `good`) without forcing red, matching the same neutral treatment
    every other axis gets for information this app cannot actually determine. Rewrote the
    justification in `scripts/assessment_rules.py`, `docs/data_contract.md`, and the backlog doc
    accordingly. (2) cto-reviewer: the operating-side verdict-level test
    (`test_operating_statement_roe_guard_caps_a_negative_equity_card_at_yellow`) did not test
    the property it claimed -- confirmed by mutation testing (reverting only the new
    `statement_roe_pct` guard left the test passing identically) because `debt_to_equity`'s own,
    already-merged guard checks the SAME `stmt_stockholders_equity` field unconditionally, so it
    alone already explains the yellow outcome on any row with negative equity, regardless of
    whether the new guard is wired in at all. Fixed: added a direct function-level test calling
    `_axis_unless_denominator_nonpositive` directly with each verdict function's actual
    parameters, isolating this guard's own effect from `debt_to_equity`'s; kept the
    verdict-level test as an integration sanity check with a corrected docstring that no longer
    claims isolation. Corrected diff re-dispatched to all three reviewers.
  - Round-2 review: equity-analyst-reviewer PASSED (confirmed the `"unknown"` correction genuinely
    resolves the applicability concern, with no residual trace of the rejected bank-specific
    justification). cto-reviewer FAILED again, on a deeper version of the same class of gap: the
    round-1 fix (a direct function-level test) proved the shared guard function works correctly
    in isolation, but that test never calls `_verdict_operating` at all, so it cannot prove the
    operating call site is actually wired to it -- confirmed by mutation testing (reverting the
    operating call site back to a plain `_axis(...)` call left the ENTIRE suite passing, 75/75,
    including both the confounded verdict-level test AND the new isolated function-level test).
    Root cause: because `debt_to_equity`'s guard fires unconditionally whenever
    `stmt_stockholders_equity` is negative, independent of `debt_to_equity`'s own value or even
    its presence in the row, NO row constructible through `compute_verdict` can ever isolate
    `statement_roe_pct`'s call site from `debt_to_equity`'s -- the two are structurally coupled
    at the verdict level, not just confounded by a specific test's fixture choice. Fixed: added
    `test_operating_statement_roe_call_site_is_actually_wired`, which uses `pytest`'s
    `monkeypatch` fixture to neutralize `debt_to_equity`'s guard specifically (falls back to
    plain magnitude banding for that one call) while leaving `statement_roe_pct`'s call to the
    real guard, then drives the row through `compute_verdict` -- this genuinely exercises
    `_verdict_operating`'s actual code path and fails if the call site is ever silently reverted
    (verified directly: reverted the call site, confirmed this specific new test fails while the
    old confounded test still passes, then restored the file and reran the full suite green).
    cto-reviewer also caught a stale line in `docs/backlog/gemini_verdict_feedback.md`'s Related
    section, newly added in round 1, that described the first (rejected) "financial forces red"
    behavior rather than the shipped `"unknown"` behavior -- fixed. Corrected diff re-dispatched
    to scope-auditor and cto-reviewer (equity-analyst-reviewer's routed file, `docs/data_contract.md`,
    is unchanged since its round-2 PASS, so not re-dispatched).
  - Round-3 review: scope-auditor PASSED, independently mutation-testing the round-2 fix itself
    (reverted the operating call site, confirmed only the new wiring test failed, restored the
    file, confirmed a clean diff). cto-reviewer FAILED on one new finding: the module-level
    "Ratio sign-inversion guards" preamble comment above `_axis_unless_denominator_nonpositive`
    (`scripts/assessment_rules.py`, untouched by any hunk in this diff until now) still said "Two
    operating-type ratios" / "Both guards" -- stale, since this diff adds a third guarded metric
    (`statement_roe_pct`) used from both `_verdict_operating` and `_verdict_financial` with a
    role-dependent band, which the preamble neither counted nor explained, and which now
    contradicted the correctly-updated `docs/data_contract.md`. The same class of gap as round
    2's finding, a documentation-accuracy analogue rather than a test-coverage one, in the one
    shared comment every other per-call-site update this task made missed sweeping. Fixed:
    rewrote the preamble to count three guarded metrics across four call sites, name
    `statement_roe_pct`'s dual role explicitly, and cross-reference `_verdict_financial`'s own
    comment for why that function's population makes `"unknown"` the choice there. cto-reviewer
    also flagged (non-blocking, correctly out of scope) an identical staleness pattern in
    `scripts/generate_assessments.py`'s comment, not in `scope_paths` -- noted in `impact_map`
    above, not fixed here. Corrected diff re-dispatched to scope-auditor and cto-reviewer.
  - Round-4 review: scope-auditor PASSED (independently re-verified the call-site count by
    grepping the actual code rather than trusting the comment, confirmed 4 call sites across 3
    metrics matching the rewritten preamble; also swept the whole repo, not just `scope_paths`,
    for the same staleness pattern and found one further low-severity, non-blocking instance in
    `dbt_analytics/models/4_intermediate/_intermediate.yml`'s `stmt_stockholders_equity` column
    description, which names only `debt_to_equity` as a dependent, not `statement_roe_pct` --
    out of scope, not fixed here, noted for a future pass). cto-reviewer FAILED on a fresh
    factual error introduced BY the round-3 fix itself: the rewritten preamble claimed
    `statement_roe_pct`'s numerator (net income) "is never negative," which is false -- a loss
    (negative net income) is the entire premise of the bug this guard exists to catch, and the
    claim directly contradicted the preamble's own line 2 sentences earlier ("can read as a
    spuriously positive percentage") and the per-call-site comments elsewhere in the same file.
    Root cause: over-generalized `debt_to_equity`'s true "numerator never negative" property
    across to `statement_roe_pct` while merging the two explanations into one sentence during the
    round-3 rewrite. Fixed: rewrote the paragraph to correctly describe THREE distinct failure
    modes -- net_debt_to_ebitda's numerator can be negative (ambiguous double-negative with the
    denominator); statement_roe_pct's numerator can also be negative (a real loss), the same
    double-negative ambiguity, which is WHY the guard keys on equity's sign alone rather than
    net income's; debt_to_equity's numerator is genuinely never negative but CAN be exactly zero
    (a distinct, third failure mode -- zero divided by anything is zero, not negative). Corrected
    diff re-dispatched to both scope-auditor and cto-reviewer for a full round 5, since the file
    changed again after scope-auditor's round-4 PASS; see `.claude/task/review.md`, written only
    after all reviewers' final verdicts are in hand.
