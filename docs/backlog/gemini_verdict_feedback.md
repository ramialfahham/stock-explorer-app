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

   **Sibling bug found while reviewing this fix, NOT fixed here (separate, unscoped issue):**
   `statement_roe_pct` (`stmt_net_income_common / stmt_stockholders_equity`, in
   `int_stock__card_metrics.sql`) has the identical sign-ambiguity problem `debt_to_equity` had --
   a loss over negative equity divides out to a spuriously POSITIVE return on equity, which an
   existing dbt unit test (`card_metrics_statement_metrics_negative_equity` in
   `dbt_analytics/models/4_intermediate/_intermediate.yml`) already documents as an accepted,
   unaddressed output. `statement_roe_pct` is itself a supporting axis in `_verdict_operating`,
   same as `debt_to_equity`, so the same `stmt_stockholders_equity`-based guard mechanism this fix
   already built could very likely apply directly. Not touched here because it was outside this
   task's confirmed scope (`.claude/task/contract.md` names only the two metrics above).

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

3. **No structured/JSON output from the AI-read prompt -- TRUE.** `scripts/
   generate_assessments.py`'s call to the Claude API passes no `tools`, `tool_choice`, or JSON
   schema; the system prompt explicitly asks for "2-3 sentences" of prose, parsed back as free
   text.

4. **No post-generation KPI/hallucination reference-check -- TRUE.** The generated read is
   taken verbatim (only checked for being non-empty) and stored with no step that parses numbers
   out of it and cross-checks them against the card's actual metric values. The only mitigation
   is a soft prompt-level instruction ("reason only from the numbers given, never guess").

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

7. All six metric values Gemini read off Apple's card (Operating Margin 33.2%, Revenue Growth
   YoY 16.4%, FCF Margin 23.7%, Return on Equity 151.9%, Debt/Equity 1.34, Net Debt/EBITDA 0.13)
   were reported as accurate by Gemini itself; no verification needed here.

8. **No function jointly evaluates current ratio against FCF margin -- TRUE.** Same evidence
   as point 6: the two axes are gated fully independently; no combined liquidity function exists
   in the codebase.

9. **No sector or company-size calibration of verdict thresholds -- TRUE.** Every `weak_th`/
   `good_th` pair is hardcoded per `company_type` bucket only (three buckets total), with no
   reference to sector or size anywhere in the three verdict functions. Sector-relative
   `sector_median`/`min`/`max` columns exist in the mart, but feed only the card-face range
   visualization, never the verdict computation. A small-cap and a mega-cap in the same sector
   are judged against identical thresholds today.

## Open questions (owner decisions, not answered here)

- **Is any of this worth fixing, and if so which parts first?** Seven confirmed gaps span three
  different subsystems (dbt ratio computation, the verdict rule engine, the AI-read prompt, and
  the metric-range visualization) -- a metric-definition and methodology decision squarely
  inside this repo's working agreement's owner-decision list (§6: metric definitions and
  anything that changes an already-shipped verdict), not something to default silently.
- **Does a joint liquidity evaluation (point 6/8) change verdicts on cards already shown to
  users, and is that an acceptable outcome?** Any change here would flip some already-computed
  `health_verdict` values; the working agreement treats "changing an already-shipped output" as
  an owner call every time.
- **Does sector/size calibration (point 9) fit this app's stated design at all?** `north_star.md`
  already states a rule against naive sector-relative rankings ("do not use naive 'Top 10% in
  sector' rankings -- misleading for debt, negative growth, etc."); calibrating verdict
  *thresholds* by sector/size is a related but distinct question from ranking by sector, and
  worth keeping that distinction explicit rather than treating this point as already answered by
  that existing rule.
- **Is a sign-inversion guard (point 1) a targeted dbt/rules fix, or does it call for rethinking
  which ratios are safe to show raw at all** for companies with negative EBITDA or negative net
  debt? A narrow guard could mask the same companies' problems differently rather than fixing
  the display.

## Candidate directions (not decisions, for owner discussion)

1. **Ratio sign-inversion guard (point 1). Done -- branch `fix/ratio-sign-inversion-guard`.** A
   small, targeted `scripts/assessment_rules.py` function that detects a negative-denominator
   inversion and reclassifies the axis instead of banding it by raw magnitude. Lowest engineering
   risk of the set; narrow scope, no new dependency. See point 1's Context entry above.
2. **Joint liquidity evaluation (points 6/8).** Replace `_verdict_operating`'s independent
   core/supporting gating for `current_ratio_stmt` with a function that weighs it against
   `fcf_margin_pct`. Would change some already-shipped verdicts (see open questions); needs
   explicit sign-off before it's built, not just before it's shipped.
3. **Sector/size threshold calibration (point 9).** The largest change of the set: reworking
   `weak_th`/`good_th` from a flat per-type constant to something sector- or size-aware would
   touch the verdict engine's core structure, likely needs new baseline data, and would change
   verdicts broadly, not just for outlier cards. Warrants its own scoping pass, not a quick fix.
4. **Structured AI-read output + hallucination guard (points 3/4).** Two related but separable
   changes: requesting JSON/tool-call output from the Claude API call (a prompt/parsing change,
   no new dependency, `anthropic` already pinned), and a post-generation step that extracts
   numbers from the read and cross-checks them against the card's own metric values before
   storing it (new code, modest scope, directly closes the hallucination gap named in point 4).
5. **Outlier-aware metric-range scaling (point 5).** Compress or cap extreme values in
   `benchmark_range()`'s positioning (e.g. a log scale past some threshold, or clamping the
   *displayed* extreme while still labeling the true value) rather than linear min-max. Purely a
   display change; doesn't touch verdict computation.
6. **Early-stage classification review (point 2).** Check whether 4DMedical (and similar small-
   revenue-against-large-cap companies) should classify as `pre_revenue` rather than `operating`,
   or whether `_verdict_operating` itself needs an early-stage carve-out. Smallest-scoped of the
   set if the answer is "adjust the classification threshold"; larger if it requires a new
   verdict path.

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
- `tests/tooling/test_assessment_rules.py`'s `test_operating_supporting_weakness_blocks_green`:
  the existing test that already demonstrates point 6/8's behavior directly.
- `docs/north_star.md`'s existing rule against naive sector-relative rankings, distinct from but
  adjacent to point 9.
