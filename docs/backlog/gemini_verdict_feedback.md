# Gemini feedback on verdict methodology and metric-range scaling

**Status:** Backlog. Owner tested two live cards (4DMedical, an early-stage medtech, and
Apple/AAPL, a mature large-cap) and ran the results past Gemini, then asked that its feedback be
filed for later discussion, not acted on. Filed 2026-08-31 after verifying every checkable
technical claim against the codebase directly (not transcribed uncritically) -- see Context.
Does not choose a fix for anything.

## Summary

Gemini raised nine points across the two cards; seven describe real, confirmed gaps in the
current codebase (verdict thresholds, the AI-read prompt, and the metric-range visualization all
behave exactly as described), one is only partially true (early-stage framing exists but doesn't
reach 4DMedical's actual classification), and one (that all six of Apple's displayed metric
values are numerically accurate) needed no verification. None of this is acted on here: these
are product/methodology decisions (verdict rule changes, prompt changes, visualization changes)
squarely inside this repo's working agreement's owner-decision list, not something to implement
on a third-party AI's say-so without the owner's own call.

## Context (verified against the codebase, not assumed from Gemini's claims)

**On 4DMedical (early-stage medtech):**

1. **No ratio sign-inversion guard exists -- TRUE.** Every ratio in
   `dbt_analytics/models/4_intermediate/int_stock__card_metrics.sql` (`net_debt_to_ebitda`,
   `fcf_margin_pct`, `debt_to_equity`, `current_ratio_stmt`) guards only against a zero
   denominator (`!= 0`), never against a negative one flipping the sign. `assessment_rules.py`'s
   banding helpers classify purely by magnitude against `weak_th`/`good_th`, with no sign check
   either. A negative-EBITDA, negative-net-debt company can produce a small *positive*
   `net_debt_to_ebitda` (two negatives dividing out) that bands as "good," while the raw
   (inverted) ratio is still shown on the card face and named in the AI read as if healthy. No
   guardrail function exists anywhere in the repo today.

   **Acted on, branch `fix/ratio-sign-inversion-guard`.** `net_debt_to_ebitda` (a core axis) is
   now banded `unknown` when a new `info_ebitda` passthrough column is present and `<= 0`, since
   the ratio's own sign cannot distinguish genuine net cash from real debt over negative
   earnings. `debt_to_equity` (a supporting axis) is now banded `weak` when a new
   `stmt_stockholders_equity` passthrough column is present and `<= 0`. Both guards check the raw
   denominator directly rather than the ratio's own sign: an equity-analyst review round caught
   that inferring equity's sign from `debt_to_equity`'s sign misses a debt-free company with
   negative equity (total debt exactly zero divides out to a zero ratio regardless of equity's
   sign), which the raw-denominator check catches. See `docs/data_contract.md`'s verdict-rules
   section for the shipped behavior. The raw (possibly sign-flipped) value shown on the card face
   and named in the AI read is unchanged; that is candidate direction 4 (structured AI-read
   output), not this fix.

   **Sibling bug found while reviewing this fix, NOT fixed here (separate, unscoped issue).**
   `statement_roe_pct` (`stmt_net_income_common / stmt_stockholders_equity`, in
   `int_stock__card_metrics.sql`) has the identical sign-ambiguity problem `debt_to_equity` had --
   a loss over negative equity divides out to a spuriously POSITIVE return on equity, which an
   existing dbt unit test (`card_metrics_statement_metrics_negative_equity` in
   `dbt_analytics/models/4_intermediate/_intermediate.yml`) already documents as an accepted,
   unaddressed output. `statement_roe_pct` is itself a supporting axis in `_verdict_operating`,
   same as `debt_to_equity`, so the same `stmt_stockholders_equity`-based guard mechanism this fix
   already built could very likely apply directly. Not touched here because it was outside this
   task's confirmed scope (`.claude/task/contract.md` names only the two metrics above).

   **Acted on, branch `fix/statement-roe-sign-inversion-guard`.** `statement_roe_pct` now goes
   through the same guard as `debt_to_equity`, checking `stmt_stockholders_equity`'s own sign
   directly. On `operating` it bands `weak` (a supporting axis, caps at yellow, same as
   `debt_to_equity`). On `financial` it bands `unknown` (roe is effectively a core axis there:
   `unknown` still blocks green, but doesn't force red the way `weak` would).

   **Mid-implementation correction**: the first version banded `weak` on financial too, forcing
   red outright, reasoned from US bank capital regulation (the FDIC's Prompt Corrective Action
   framework). An equity-analyst review round caught that this overreached what the data
   supports: `company_type == 'financial'` is the whole GICS "Financial Services" sector
   (insurers, asset managers, broker-dealers, payment networks, exchanges, mortgage finance, not
   only depository banks), spans markets under entirely different regulatory regimes (this app
   covers US, UK, Japan, Australia, Germany, France, Netherlands, Switzerland, Spain), and
   includes firms (payment networks especially) known for the same benign buyback-driven negative
   equity operating companies can have -- exactly the case the original reasoning said should get
   the mild treatment, not the harsh one. Corrected to `unknown`: nothing in the data
   distinguishes a bank in genuine distress from a payment network mid-buyback, so the same
   neutral treatment every other axis gets for undeterminable information is the honest choice.
   See `docs/data_contract.md`'s verdict-rules section for the shipped behavior.

2. **Early-stage/pre-revenue context awareness -- PARTIALLY TRUE.** The framework is not
   blind to early-stage companies in general: `_verdict_pre_revenue()`
   (`scripts/assessment_rules.py`) judges only cash/runway/working-capital, never profitability,
   and the AI-read system prompt already frames a `pre_revenue`-type card as "a survival story,"
   not a profitability story. But strong indirect evidence places 4DMedical in the **operating**
   type, not `pre_revenue`: `ebit_margin_pct` ("Operating Margin," the figure Gemini saw at
   -823.3%) is defined only for the operating type, and pre-revenue classification requires
   revenue at or below zero, or revenue under 0.1% of market cap -- a bar 4DMedical's real,
   nonzero device revenue against a smaller market cap doesn't clear. So it's judged by
   `_verdict_operating`'s mature-company thresholds with no early-stage allowance, which is a
   real gap for this specific card even though the framework generically has an early-stage path.

   **Considered, not pursued.** The existing 0.1%-of-market-cap classification bar is not
   arbitrary: it was set from a specific degenerate case, Deep Yellow (ASX: DYL), whose revenue
   was ~0.001% of market cap and produced a -129,810%/-90,334% margin outlier that swamped its
   sector's whole range (see `int_stock__card_metrics.sql`'s classification CASE for the full
   account). 4DMedical does not clear that bar for a materially different reason: its revenue,
   while small, is not a rounding error the way Deep Yellow's was -- it is a genuinely different,
   non-degenerate situation (an early operating company with thin margins), not the same failure
   mode the threshold exists to catch. Moving the threshold specifically to also sweep in
   4DMedical would have no grounding beyond disliking one card's output -- the same invented-
   number problem point 9 was declined for. An `_verdict_operating` early-stage carve-out has the
   identical problem in a different spot: any relief condition still needs a cutoff with nothing
   external to anchor it to. -823.3% is an honest, correctly computed number for a company
   spending heavily against thin revenue; it is not evidence the classification or verdict logic
   is wrong. If the actual discomfort is how that number LOOKS on the card (an extreme ratio
   distorting a sector range mark), that is point 5's problem (outlier-aware metric-range
   scaling), a display change, not a classification or verdict-computation one.
   Decision: do not move the pre-revenue classification threshold, and do not add an
   early-stage carve-out to `_verdict_operating`.

3. **No structured/JSON output from the AI-read prompt -- TRUE.** `scripts/
   generate_assessments.py`'s call to the Claude API passes no `tools`, `tool_choice`, or JSON
   schema; the system prompt explicitly asks for "2-3 sentences" of prose, parsed back as free
   text.

   **Acted on, branch `feat/ai-read-structured-hallucination-guard`.** See point 4's entry below
   for the mechanism; the structured-output and hallucination-guard changes shipped together.

4. **No post-generation KPI/hallucination reference-check -- TRUE.** The generated read is
   taken verbatim (only checked for being non-empty) and stored with no step that parses numbers
   out of it and cross-checks them against the card's actual metric values. The only mitigation
   is a soft prompt-level instruction ("reason only from the numbers given, never guess").

   **Acted on, branch `feat/ai-read-structured-hallucination-guard`.** The Claude Haiku call now
   forces tool-use (`write_card_read`): the model returns `read` plus `referenced_metrics`, one
   `{label, value_as_shown}` entry per metric the read cites, copied exactly as shown in the
   prompt's own facts block. `validate_read_metrics` checks each pair against the same rendering
   the model was shown (`_present_metric_renderings`, reused from `build_read_messages`): a
   numeric cross-check, not an LLM judge, so it catches a stated number that does not match the
   card's data but not an unsupported qualitative claim that cites no wrong number. Any mismatch,
   unknown label, or malformed tool response fails exactly like an API exception already does:
   `ai_read`/`read_model` stay absent and the existing regenerate-on-`input_hash`-change path
   picks the card up again next run. No retry. `INPUT_HASH_VERSION` not bumped: this is a
   generation-mechanism change, not an input change, so already-stored reads are unaffected. When
   `ai_read` is absent, the card now shows a deterministic, owner-authored one-line summary under
   its own "What the verdict means" heading instead of a bare badge (`frontend/card_copy.py`'s
   `VERDICT_FALLBACK_READ`), never labeled AI-written. See `docs/data_contract.md`'s
   `card_assessments` section for the shipped behavior.

5. **Metric-range visualization has no extreme-outlier handling -- TRUE.**
   `frontend/card_copy.py`'s `benchmark_range()` is pure linear min-max normalization, clamped
   only to keep the marker inside the visible track, not to compress outliers; the sector
   min/max inputs feeding it are raw aggregates with no percentile trimming. An extreme value
   like -823% simply becomes the new range floor, compressing every peer toward the opposite end.

**On Apple (AAPL), a mature large-cap:**

6. **The "Mixed" verdict's liquidity check doesn't weigh FCF margin against the current
   ratio -- TRUE.** Apple is `operating`-type. `fcf_margin_pct` is a *core* axis and
   `current_ratio_stmt` is a *supporting* axis in `_verdict_operating`, evaluated completely
   independently: green requires every core axis good **and** no supporting axis weak, with
   nothing that lets a strong core axis offset a weak supporting one. This is confirmed by the
   repo's own existing test, `test_operating_supporting_weakness_blocks_green`
   (`tests/tooling/test_assessment_rules.py`), which asserts exactly this pattern (strong FCF
   margin, weak current ratio) still yields yellow. Apple's real figures (current ratio 0.89,
   FCF margin 23.7%) map to precisely that case, which is why it read Mixed.

   **Acted on, branch `fix/joint-liquidity-evaluation`.** Owner judged the Mixed reading
   contradicted real-world consensus on Apple's financial health. `current_ratio_stmt` now bands
   `ok` instead of `weak` when free cash flow (`stmt_free_cash_flow`, a raw dollar figure) covers
   the working-capital shortfall and `current_ratio_stmt` is at or above a new floor,
   `CURRENT_RATIO_LIQUIDITY_FLOOR` (`0.5`) -- below that floor, current liabilities are more than
   double current assets, a real distress signal no amount of free cash flow overrides.
   **Mid-implementation correction**: the first version gated relief on `fcf_margin_pct` banding
   `good` (free cash flow ÷ revenue). A review round caught that this is a mismatched comparison
   -- margin doesn't track the SIZE of the liquidity gap, which isn't proportional to revenue for
   a company whose current liabilities carry a near-term debt-maturity wall, so it only worked
   for Apple by coincidence of scale. Corrected to a direct dollar comparison
   (`stmt_free_cash_flow >= -working_capital`) that still relieves Apple and correctly withholds
   relief from the debt-maturity-wall case a margin-only check would have missed.
   `test_operating_supporting_weakness_blocks_green` was updated to demonstrate the general "weak
   supporting axis blocks green" principle on `statement_roe_pct` instead, since its old fixture
   now falls inside this relief. See `docs/data_contract.md`'s verdict-rules section for the
   shipped behavior.

7. All six metric values Gemini read off Apple's card (Operating Margin 33.2%, Revenue Growth
   YoY 16.4%, FCF Margin 23.7%, Return on Equity 151.9%, Debt/Equity 1.34, Net Debt/EBITDA 0.13)
   were reported as accurate by Gemini itself; no verification needed here.

8. **No function jointly evaluates current ratio against FCF margin -- TRUE.** Same evidence
   as point 6: the two axes are gated fully independently; no combined liquidity function exists
   in the codebase.

   **Acted on, branch `fix/joint-liquidity-evaluation`.**
   `_current_ratio_axis_with_fcf_coverage_relief` in `scripts/assessment_rules.py` is that
   combined function now. See point 6's entry above for
   the mechanism.

9. **No sector or company-size calibration of verdict thresholds -- TRUE.** Every `weak_th`/
   `good_th` pair is hardcoded per `company_type` bucket only (three buckets total), with no
   reference to sector or size anywhere in the three verdict functions. Sector-relative
   `sector_median`/`min`/`max` columns exist in the mart, but feed only the card-face range
   visualization, never the verdict computation. A small-cap and a mega-cap in the same sector
   are judged against identical thresholds today.

   **Considered, not pursued (branch `docs/decline-sector-size-calibration`).** Investigated
   whether the fixed thresholds should be calibrated by sector and/or size, at the owner's
   request that any proposal be grounded in real practice, not invented. Findings against:
   the current thresholds are not actually arbitrary -- `net_debt_to_ebitda` good/weak at
   1.5x/3x mirrors common leverage credit-quality bands (rating-agency-style "low"/"aggressive"
   leverage tiers, not a specific loan covenant, which typically sits higher, around 4x-6x, for
   leveraged borrowers); `ebit_margin_pct` good at 10% is a standard double-digit-margin
   heuristic; `current_ratio_stmt` good/weak at 1.5/1.0 is classic textbook liquidity convention;
   `cash_runway_months` good/weak at 24/12 months is a standard startup-finance heuristic.
   `docs/north_star.md` already carries an owner-signed rule against naive sector-relative
   rankings for the display benchmark, and the same risk applies to verdict thresholds:
   calibrating to sector would let a mediocre company in a currently-weak sector read green
   purely because its peers are worse, contradicting the AI-read's own closing claim of an
   absolute "financially healthy on these figures," not a relative one. Sector-relative
   comparison is a real, standard equity-analysis practice, but size-adjusted THRESHOLDS are not
   -- real credit/fundamental analysis handles issuer size through business-risk-profile
   overlays that typically TIGHTEN expectations for smaller, less-diversified issuers to hold
   the same rating, not through loosening what counts as a healthy margin or leverage ratio, so
   any size-bucket cutoffs here would run backwards from how size is actually treated and would
   still be exactly the kind of invented number the owner was concerned about. Sector medians
   also shift on every biweekly refresh, and the display feature's own 8-peer minimum shows how
   thin these peer groups can get, so a company's verdict could flip color with none of its own
   numbers changing -- a real stability cost on top of the methodology concern.
   This declines specifically the mechanism point 9 actually proposed (live `sector_median`/
   `min`/`max` recalculated every refresh, the same one `north_star.md`'s existing rule already
   warns against). It does not rule out a structurally different version -- deliberately set,
   externally-anchored per-sector benchmark tables, revised on a deliberate cycle rather than a
   live biweekly refresh -- which would sidestep the instability concern while still respecting
   genuine sector-driven margin and leverage differences. Worth naming as the version to scope if
   this is ever revisited, not something this decision forecloses.
   Decision: do not calibrate verdict thresholds by sector or size.

## Open questions (owner decisions, not answered here)

- **Is any of this worth fixing, and if so which parts first?** Seven confirmed gaps span three
  different subsystems (dbt ratio computation, the verdict rule engine, the AI-read prompt, and
  the metric-range visualization) -- a metric-definition and methodology decision squarely
  inside this repo's working agreement's owner-decision list (§6: metric definitions and
  anything that changes an already-shipped verdict), not something to default silently.
- **Does a joint liquidity evaluation (point 6/8) change verdicts on cards already shown to
  users, and is that an acceptable outcome?** Any change here would flip some already-computed
  `health_verdict` values; the working agreement treats "changing an already-shipped output" as
  an owner call every time. **Answered:** yes, and yes -- owner judged the alternative (leaving
  Apple's card reading Mixed) as the actual defect, since it contradicted real-world consensus on
  Apple's financial health. See candidate direction 2's "Done" entry.
- **Does sector/size calibration (point 9) fit this app's stated design at all?** `north_star.md`
  already states a rule against naive sector-relative rankings ("do not use naive 'Top 10% in
  sector' rankings -- misleading for debt, negative growth, etc."); calibrating verdict
  *thresholds* by sector/size is a related but distinct question from ranking by sector, and
  worth keeping that distinction explicit rather than treating this point as already answered by
  that existing rule. **Answered: no.** Investigated properly rather than treated as
  pre-answered; the same underlying risk that rule was written for applies here too. See point
  9's "Considered, not pursued" entry above for the full reasoning.
- **Is a sign-inversion guard (point 1) a targeted dbt/rules fix, or does it call for rethinking
  which ratios are safe to show raw at all** for companies with negative EBITDA or negative net
  debt? A narrow guard could mask the same companies' problems differently rather than fixing
  the display.

## Candidate directions (not decisions, for owner discussion)

1. **Ratio sign-inversion guard (point 1). Done -- branch `fix/ratio-sign-inversion-guard`.** A
   small, targeted `scripts/assessment_rules.py` function that detects a negative-denominator
   inversion and reclassifies the axis instead of banding it by raw magnitude. Lowest engineering
   risk of the set; narrow scope, no new dependency. See point 1's Context entry above.
2. **Joint liquidity evaluation (points 6/8). Done -- branch `fix/joint-liquidity-evaluation`.**
   Replaced `_verdict_operating`'s independent core/supporting gating for `current_ratio_stmt`
   with a function that gives it relief when free cash flow covers the working-capital shortfall
   (a dollar comparison, not a revenue-scaled margin), floored so the relief can't apply to a
   genuinely dangerous ratio. Owner explicitly signed off before it was built, per the
   requirement above -- see point 6's Context entry.
3. **Sector/size threshold calibration (point 9). Declined -- considered, not built.** The
   largest change of the set: reworking `weak_th`/`good_th` from a flat per-type constant to
   something sector- or size-aware would touch the verdict engine's core structure and change
   verdicts broadly, not just for outlier cards. Given its own scoping pass, per the owner's
   explicit request that any proposal be grounded in real practice: the current thresholds
   already mirror standard financial conventions rather than being arbitrary, this app already
   has an owner-signed rule against a closely related naive-sector-relative pattern for the same
   underlying reason, and size-adjusted thresholds specifically have no real-analyst convention
   to anchor them to. See point 9's Context entry above for the full reasoning.
4. **Structured AI-read output + hallucination guard (points 3/4). Done -- branch
   `feat/ai-read-structured-hallucination-guard`.** Forced tool-call output from the Claude API
   call (a prompt/parsing change, no new dependency, `anthropic` already pinned), plus a
   post-generation step that cross-checks the model's cited metrics against the card's own values
   before storing the read, closing the hallucination gap named in point 4. See point 3/4's
   Context entries above for the shipped behavior.
5. **Outlier-aware metric-range scaling (point 5).** Compress or cap extreme values in
   `benchmark_range()`'s positioning (e.g. a log scale past some threshold, or clamping the
   *displayed* extreme while still labeling the true value) rather than linear min-max. Purely a
   display change; doesn't touch verdict computation.
6. **Early-stage classification review (point 2). Declined -- considered, not built.** Neither
   moving the pre-revenue classification threshold nor adding an early-stage carve-out to
   `_verdict_operating` has any grounding beyond making one card's output (4DMedical) look less
   extreme; the existing threshold is set from a real degenerate case (Deep Yellow) that
   4DMedical is not an instance of. See point 2's Context entry above for the full reasoning.

## Related

- `scripts/assessment_rules.py`: `_verdict_operating`, `_verdict_financial`,
  `_verdict_pre_revenue`, `_band`/`_axis`, `READ_SYSTEM_PROMPT`.
- `scripts/generate_assessments.py`: the Claude API call and its lack of structured output or
  post-generation validation.
- `dbt_analytics/models/4_intermediate/int_stock__card_metrics.sql`: ratio computation, `!= 0`
  guards.
- `dbt_analytics/models/.../int_stock__sector_benchmarks.sql`: raw sector min/max aggregation.
- `frontend/card_copy.py`'s `benchmark_range()`, `frontend/styles.py`'s `.ss-metric-range-*`
  rules.
- `tests/tooling/test_assessment_rules.py`'s `test_current_ratio_weak_gets_relief_when_fcf_covers_the_shortfall`
  and its neighbors: the point 6/8 fix's test coverage.
  `test_operating_supporting_weakness_blocks_green` demonstrated the pre-fix behavior for
  `current_ratio_stmt` specifically; it now demonstrates the general "weak supporting axis blocks
  green" principle on `statement_roe_pct` instead, since `current_ratio_stmt` is no longer an
  example of that principle without qualification.
- `docs/north_star.md`'s existing rule against naive sector-relative rankings, distinct from but
  adjacent to point 9.
- `tests/tooling/test_assessment_rules.py`'s `test_operating_statement_roe_guard_*` and
  `test_financial_statement_roe_guard_*`: the sibling-bug fix's test coverage, including the
  asymmetric consequence (operating caps at yellow; financial blocks green but does not force red,
  since `company_type == 'financial'` spans a heterogeneous, multi-jurisdiction population the
  data can't distinguish real distress within).
