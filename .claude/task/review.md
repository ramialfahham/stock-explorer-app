# Review

diff_sha256: a8e0e45812153e02a5a1a1daef10d96dd5c4f95d2639e4c0beba3fc8d54cdf1c

Six rounds. Required by routing: scope-auditor (always) and cto-reviewer (`frontend/*`,
`scripts/*`, `tests/*`). equity-analyst-reviewer was added voluntarily beyond the routing,
because this branch changes financial wording on a live product surface — and it produced
the two most important findings of the cycle, so the addition earned itself.

**Reviewer dispatch:** the plugin's reviewer agent types are not registered as dispatchable
in this session, so each ran as a general-purpose agent instructed to read its own role
definition verbatim first. Same role text, same cold blinded input
(`.claude/task/review_input.patch`), read-only.

**The two findings worth remembering:**

1. **The AI label sat above the rules-computed verdict badge** (equity-analyst, round 1).
   The verdict is decided by fixed rules and never by the model — the code, the data
   contract and north_star all say so — yet the card was about to head that badge with
   "AI-written", crediting the one auditable part of the assessment to a language model.
   Worse, a verdict can be stored with a null `ai_read`, which would have rendered the
   heading over zero AI-written words. Fixed: badge renders first, the label heads the
   prose only and is omitted entirely when there is no prose. Both pinned by tests.
2. **The restored direction cue's justification was factually wrong** (equity-analyst,
   round 5). It cited `current_ratio` as a metric whose BAR needs the cue;
   `current_ratio_stmt` is `benchmarkable: false` and has no bar. The claim had been copied
   into three files. Corrected to the true and still-sufficient version: only 5 of 16
   metrics are benchmarkable, so for the other 11 the cue is the only direction signal
   anywhere on the card face.

**Round history:** r1 all three FAIL (stale rename prose; `sys.path` hack duplicating
conftest; untested CSS ancestry; two false contract claims; the AI-label placement; a style
rule readable as licence to trim the required bank caveat). r2 scope-auditor FAIL (the
badge/label reorder is §6 composition, resolved on a reviewer finding rather than owner
authority — now recorded as agent-initiated and awaiting veto). r3 both FAIL (UX gate item 2
falsely discharged as "no metric-cell change" when the gloss IS the metric cell; missing
acceptance criteria; undocumented line-height change; stale handover). r4 cto FAIL (the
`INPUT_HASH_VERSION` bump does not guarantee every read rewrites — a failed Haiku call keeps
the new hash without new prose). r5 both FAIL (a fourth unqualified instance of that claim
survived in `done_when`). r6 all PASS.

**Accepted non-blocking notes, not fixed** (raised in the final round, recorded rather than
triggering a seventh cycle): `.claude/active_work.md` puts quotation marks around two
catalogue sentences that are near-paraphrases rather than verbatim (meaning preserved in
both), and `frontend/card_copy.py`'s docstring says the cue applies "on EVERY metric" when
two value-aware branches suppress it — exceptions the same docstring states ten lines above.

## scope-auditor
VERDICT: PASS
risks_checked:
- All nine staged paths inside `scope_paths`; `scripts/generate_assessments.py` confirmed
  genuinely untouched, so the stale docstring it carries was flagged rather than fixed.
- `docs/ui/card_metric_cell.md`'s addition to scope audited specifically: confined to the
  element this branch restyles, descriptive of what shipped, not a wider spec rewrite.
- The deferred sector-relative band rework is genuinely not started — no threshold, band,
  sector or peer logic touched anywhere in the diff.
- The agent-initiated badge/label ordering is disclosed as agent-initiated in the contract,
  in the handover as an open question, and in the MR — surfaced, not slipped.
- Contract self-consistency: `done_when` now matches `impact_map` and both match the code.

## cto-reviewer
VERDICT: PASS
risks_checked:
- Both CSS bug classes this repo has shipped six times: `.ss-block-label` is written only as
  `.ss-card-identity .ss-block-label`, the new guard discriminates bare from scoped, and the
  ancestry is asserted through the real `build_card_html` rather than the helpers alone.
- `metric_gloss()` body byte-identical to HEAD after the cue was removed and restored, so
  the pre-existing cue tests exercise unchanged logic.
- The `INPUT_HASH_VERSION` bump traced end to end: idempotent on re-run, and the one
  non-idempotent edge (a failed read carrying the new hash) is stated at all four sites and
  escalated as an owner call rather than fixed in-branch.
- No new mechanism, dependency, CI step, hook, permission or secret; the new guard fails
  closed and carries a vacuity assertion.
- Cost disclosed and owner-approved: roughly 907 Haiku calls on the next run.

## equity-analyst-reviewer
VERDICT: PASS
risks_checked:
- Healthy/Mixed/Fragile describe company finances, never the share; Strong/Weak was rejected
  for exactly that reason, and `VERDICT_MEANING` keeps its "on these figures" qualifier.
- Badge and prose pinned in step by test, so a one-sided rename fails CI instead of shipping
  a card whose paragraph contradicts its own badge.
- The new style rule's carve-out verified to protect the financial-company capital-strength
  limit, which is the one place the rubric's own blind spot is disclosed to a reader.
- The restored cue's justification re-checked against the catalogue rather than accepted:
  5 of 16 metrics benchmarkable, and the 11 without a bar have no other direction signal.
- Gloss typography measured for contrast, not eyeballed: roughly 7.3:1, up from 6.2:1, at a
  larger size — legibility improved.
- **Open owner question raised, not resolved:** three `higher_better` metrics
  (`dividend_yield_pct`, `current_ratio_stmt`, `revenue_growth_yoy_pct`) carry "Higher is
  better." on the card face while their own catalogue copy warns against reading the axis
  naively. Pre-existing, not created or widened here; the counter-caveat is one tap away.
