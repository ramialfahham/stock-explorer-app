# Task contract

objective: Give `current_ratio_stmt` relief from strong free cash flow in the operating verdict,
  the second point acted on from the owner's filed Gemini feedback
  (`docs/backlog/gemini_verdict_feedback.md`, points 6/8). `_verdict_operating` currently grades
  `fcf_margin_pct` (core) and `current_ratio_stmt` (supporting) completely independently, so a
  company with excellent free cash flow but a merely-weak current ratio is capped at yellow
  regardless -- exactly Apple's real card (current ratio 0.89, FCF margin 23.7%), which the
  owner judged contradicts real-world consensus on Apple's financial health. Shipped mechanism
  (see amendments for how this changed from the first, reviewer-failed version): when
  `current_ratio_stmt` bands `weak`, reclassify it to `ok` instead of `weak` when free cash flow
  (`stmt_free_cash_flow`, a raw dollar figure) covers the working-capital shortfall
  (`stmt_free_cash_flow >= -working_capital`) -- UNLESS `current_ratio_stmt` is below a floor of
  0.5 (current liabilities more than double current assets), in which case it stays `weak`
  regardless of FCF. `ok` is not `weak`, so it no longer blocks green on its own; it is also not
  `good`, so it earns no other privilege a genuinely strong ratio would.

scope_paths:
  - dbt_analytics/models/4_intermediate/int_stock__card_metrics.sql
  - dbt_analytics/models/4_intermediate/_intermediate.yml
  - dbt_analytics/models/5_marts/mart_stock_cards.sql
  - dbt_analytics/models/5_marts/_marts.yml
  - scripts/assessment_rules.py
  - scripts/generate_assessments.py
  - tests/tooling/test_assessment_rules.py
  - docs/data_contract.md
  - docs/backlog/gemini_verdict_feedback.md
  - .claude/task/contract.md
  - .claude/task/review.md
  - .claude/active_work.md

decisions_reserved: none for the shape of the fix -- the mechanism (relief to `ok`, not a full
  override to `good`) and the floor value (0.5) were both explicitly decided by the owner this
  session, after the owner rejected leaving the current behavior as-is. The specific gating
  signal changed mid-task (fcf_margin_pct -> dollar FCF-vs-shortfall comparison; see amendments)
  after a review round found the original gate financially unsound; the owner confirmed
  proceeding with the corrected mechanism before it was built, per the same standard applied to
  the mechanism's first version. This DOES change verdicts already shown to users: any operating
  card with a weak-but-not-catastrophic current ratio whose free cash flow covers its
  working-capital shortfall moves from yellow to green (unless another axis still blocks it).

done_when:
  - `int_stock__card_metrics.sql` exposes `stmt_free_cash_flow` as a new raw passthrough column
    (already fetched, just not currently passed past the intermediate layer -- the same pattern
    as `info_ebitda`/`stmt_stockholders_equity` from the prior fix). Documented in
    `_intermediate.yml`, data-only, not catalogued, not exported to Supabase. `mart_stock_cards.sql`
    passes it through too, documented in `_marts.yml`. `generate_assessments.py`'s
    `ASSESSMENT_INPUT_COLUMNS` includes it directly; `working_capital` needs no separate wiring
    since it's already part of `_METRIC_COLUMNS` via `INPUT_FIELDS_BY_TYPE["pre_revenue"]`, so
    every row already carries it regardless of company_type.
  - `scripts/assessment_rules.py` gets `CURRENT_RATIO_WEAK_TH`/`CURRENT_RATIO_GOOD_TH` (1.0/1.5,
    extracted from the pre-existing inline literals) and `CURRENT_RATIO_LIQUIDITY_FLOOR` (0.5,
    new), each with a comment stating the reasoning the owner gave (why 0.5, why relief lands on
    `ok` not `good`).
  - A new function, `_current_ratio_axis_with_fcf_coverage_relief(row)`, replaces the direct
    `_axis(row, "current_ratio_stmt", ...)` call in `_verdict_operating`'s `supporting` tuple.
    Bands normally (`good`/`ok`/`unknown`) in every case except: value present, bands `weak`,
    value `>= CURRENT_RATIO_LIQUIDITY_FLOOR`, `working_capital` present and negative, and
    `stmt_free_cash_flow` present and `>= -working_capital` -- only then does it return `ok`
    instead of `weak`.
  - `tests/tooling/test_assessment_rules.py`: `test_operating_supporting_weakness_blocks_green`
    updated to demonstrate the general "weak supporting axis blocks green" principle on an axis
    the relief mechanism does NOT touch (`statement_roe_pct`). New cases: relief actually flips a
    green-eligible Apple-shaped card to green; the exact debt-maturity-wall counter-example a
    revenue-scaled gate would have missed (decent FCF margin, real FCF far short of the dollar
    shortfall) is correctly denied; the floor still blocks relief below 0.5 regardless of FCF
    coverage; the floor boundary itself; the coverage boundary itself (FCF exactly equal to the
    shortfall clears it); missing `stmt_free_cash_flow` or `working_capital` earns no relief; a
    non-negative `working_capital` despite a weak ratio earns no relief (defensive); relief does
    not rescue an unrelated weak axis elsewhere; a missing `current_ratio_stmt` is untouched.
  - `docs/data_contract.md`'s verdict-rules section documents the relief mechanism and its floor,
    since it's the authoritative description of how the color is decided.
  - `docs/backlog/gemini_verdict_feedback.md` updated: points 6/8 marked acted on, with a pointer
    to this branch and the corrected mechanism.
  - `pytest` green. `dbt build` green for the changed models.
  - No em dash or en dash on any added line.

impact_map:
  - Changes verdicts for real cards: any operating-type company with `current_ratio_stmt` in
    [0.5, 1.0) whose free cash flow covers its working-capital shortfall moves from yellow to
    green, unless a different axis still blocks it. Below 0.5, nothing changes regardless of FCF.
    A company with a decent `fcf_margin_pct` but FCF far short of a real shortfall (e.g. a
    near-term debt-maturity wall) correctly does NOT move -- this is the specific case the first,
    reviewer-failed version of this fix would have wrongly relieved.
  - Requires re-running the pipeline (dbt build, then `scripts/generate_assessments.py`) to
    actually recompute verdicts against the fix -- not something `pytest` alone verifies. Local
    dev sample (63 cards) is unlikely to contain a card matching this exact profile, so this
    can't be visually verified pre-merge, matching the prior sign-inversion fix.
  - Known, explicitly out of scope: `_verdict_operating`'s other supporting axes
    (`debt_to_equity`, `statement_roe_pct`) get no analogous relief mechanism. This fix is scoped
    to the one metric pair Gemini's feedback and the owner's decision named; extending the same
    idea to other pairs is a new, separate decision, not implied by this one.
  - No frontend change; the card face already shows whatever `current_ratio_stmt`/
    `fcf_margin_pct` values the mart computes, unchanged by this fix. `stmt_free_cash_flow` and
    `working_capital` are internal signals only, not displayed.

amendments:
  - Round-1 review: equity-analyst-reviewer and cto-reviewer both FAILED the first version of
    this diff; scope-auditor PASSED. (1) equity-analyst-reviewer: gating relief on
    `fcf_margin_pct` banding `good` is a mismatched comparison -- margin is scaled by revenue,
    not by the size of the liquidity gap, which isn't proportional to revenue for a company whose
    current liabilities carry a near-term debt-maturity wall. Built a concrete counter-example
    (modest revenue, a 6% FCF margin that clears "good", but real FCF a small fraction of a real
    dollar shortfall) where the old mechanism would have wrongly relieved a card with genuine
    liquidity risk. Fixed: replaced the `fcf_margin_pct`-gated check with a direct dollar
    comparison, `stmt_free_cash_flow >= -working_capital` (does free cash flow actually cover the
    working-capital shortfall), requiring a new `stmt_free_cash_flow` raw passthrough column
    (same pattern as `info_ebitda`/`stmt_stockholders_equity`) and reusing the already-computed
    `working_capital` column (already flows through `_METRIC_COLUMNS` via
    `INPUT_FIELDS_BY_TYPE["pre_revenue"]`, no new wiring needed for it). This still relieves
    Apple (FCF a large multiple of its comparatively small shortfall) and correctly withholds
    relief from the counter-example. Surfaced to the owner before implementing; owner confirmed
    "go ahead" on the proposed redesign. (2) cto-reviewer: the test
    `test_current_ratio_relief_requires_fcf_margin_actually_good` did not test the property its
    docstring claimed -- confirmed by mutation testing (weakening the relief gate from `good` to
    `!= weak` left the test passing) because its fixture's `fcf_margin_pct=3.0` also failed the
    CORE axis's own independent `fcf_margin_pct >= 5.0` requirement, forcing yellow regardless of
    whatever the relief function did. Moot in the corrected design: the relief mechanism no
    longer references `fcf_margin_pct` at all, so this specific confound cannot recur; replaced
    with `test_current_ratio_relief_denied_when_fcf_margin_good_but_shortfall_too_large`, which
    sets `fcf_margin_pct=6.0` (clears the unrelated core gate) alongside an insufficient dollar
    shortfall, isolating the relief mechanism's own gate cleanly. Corrected diff re-dispatched to
    FOUR reviewers, not three -- the redesign's new `stmt_free_cash_flow` passthrough touches
    `.sql`/`.yml` files, which route to analytics-engineer-reviewer per
    `.claude/review_routing.json`'s `*.sql`/`dbt_analytics/*.yml` patterns, on top of the three
    from round 1.
  - Round-2 review: cto-reviewer, analytics-engineer-reviewer, and equity-analyst-reviewer all
    PASSED the corrected mechanism (dollar-comparison logic, boundary conditions, and financial
    soundness all independently verified, including mutation testing and a hand-traced re-check
    of the exact debt-maturity-wall counter-example). scope-auditor FAILED on a real but
    process-only finding: this `amendments` section's previous entry (see above) asserted, in
    completed past tense, that review had already happened and pointed at
    `.claude/task/review.md` as if it already recorded the outcome -- neither was true at the
    time it was written, and the reviewer count was still "three", not the four actually
    dispatched. Fixed: this entry replaces the premature claim; `.claude/task/review.md` is
    written only after all round-2 verdicts are in hand, per the same sequencing every prior task
    this session has followed. scope-auditor also flagged one flaky `pytest` failure (1 of 32
    full-suite runs, not reproducible in isolation or in 31 other runs including with a fixed
    hash seed) as a non-blocking observation, most likely transient interference from multiple
    reviewer agents running `pytest` concurrently in this same shared (non-worktree-isolated)
    working directory while cto-reviewer's own mutation testing was temporarily editing
    `scripts/assessment_rules.py` in place -- not a defect in the staged diff itself; re-run
    clean before commit.
