# Review

diff_sha256: 2837085e8b57b428253c193e21c65ad9d85299b09dde6a2397a80ab3d27f4a23

Three rounds. Documentation-only change: records a decision (not to calibrate verdict thresholds
by sector or size, Gemini feedback point 9) rather than implementing anything. Only scope-auditor
is required per `.claude/review_routing.json` -- the backlog doc doesn't route to any other
reviewer. An equity-analyst-reviewer pass was dispatched anyway, voluntarily, since the doc makes
analyst-grade financial claims and the entire point of the task was avoiding an unverified or
hallucinated conclusion.

Round 1: scope-auditor PASS; equity-analyst-reviewer (voluntary) PASS with two precision findings
(fixed). Round 2: scope-auditor FAIL on a claim introduced while applying those fixes (fixed).
Round 3: scope-auditor PASS.

## Round 1 findings and how each was resolved (equity-analyst-reviewer, voluntary pass)

1. **Overclaimed provenance.** Calling the `net_debt_to_ebitda` leverage threshold's 1.5x/3x
   band "lending-covenant conventions" overclaimed a specific source -- real loan covenants
   typically sit higher (4x-6x) for leveraged borrowers. Fixed: reworded to "rating-agency-style
   'low'/'aggressive' leverage tiers," a more accurate analogy, with the covenant-level distinction
   stated explicitly rather than silently dropped.
2. **Wrong mechanism named.** "Real analysts handle size effects through required-return
   premiums" named an equity-valuation discount-rate construct, not how credit/fundamental
   analysis actually treats issuer size, which is business-risk-profile overlays that TIGHTEN
   (not loosen) expectations for smaller, less-diversified issuers. Neither finding reversed the
   conclusion -- the corrected mechanism argues even more strongly against loosening thresholds
   for small caps than the original, imprecise one did. Fixed: reworded across
   `docs/backlog/gemini_verdict_feedback.md` and `.claude/task/contract.md`.

Also incorporated the reviewer's completeness note: the decision declines specifically the LIVE
sector-median mechanism Gemini's point 9 proposed, not every conceivable sector-aware design; a
deliberately-set, externally-anchored per-sector benchmark table (revised on a cycle, not live)
would sidestep the instability concern and is worth naming as the version to scope if this is
ever revisited.

## Round 2 finding and how it was resolved (scope-auditor)

3. **Unverified claim introduced while fixing the round-1 findings.** The completeness note
   added in round 1 included a phrase pulled from the reviewer's own suggestion --  "closer to
   how rating agencies publish industry benchmark tables" -- that was never propagated to
   `.claude/task/contract.md` (inconsistent across the two documents) and, more importantly, was
   never independently fact-checked the way the other two corrections were (both had explicit
   citations; this one didn't). This is exactly the failure mode the whole exercise exists to
   guard against: an unverified analyst-grade claim slipping into the document during what was
   meant to be a precision-only fix. Fixed: removed the specific "rating agencies" citation
   entirely, keeping only the self-evident structural point (deliberately set, revised on a
   cycle, not live) that needs no external precedent to be true.

## scope-auditor
VERDICT: PASS
risks_checked:
- Verified all four quoted threshold pairs (`net_debt_to_ebitda`, `ebit_margin_pct`,
  `current_ratio_stmt`, `cash_runway_months`) against the live `scripts/assessment_rules.py`
  source directly.
- Verified the `north_star.md` sector-ranking rule quote word-for-word against the actual file.
- Verified the AI-read's absolute framing claim directly against `VERDICT_MEANING` and
  `READ_SYSTEM_PROMPT` -- no sector/peer language anywhere in the prompt.
- Grepped the full diff for the round-2-flagged "rating agencies" phrase across all three
  rounds; confirmed genuinely absent from live content by round 3, not just reworded.
- Read the remaining completeness-note sentence fresh after the round-2 removal and confirmed it
  stays grammatically and logically complete without the removed clause.
- Confirmed via `.claude/review_routing.json` at every round that scope-auditor is the only
  reviewer strictly required for these three files, and that the equity-analyst-reviewer pass
  was correctly voluntary, not a skipped gate requirement.
- Scanned every added line across all three rounds for em/en dash characters -- zero matches
  throughout.
- Verified the three edited locations in `docs/backlog/gemini_verdict_feedback.md` (point 9
  Context, Open questions, candidate direction 3) state the same outcome and cross-reference
  each other correctly at every round, without contradicting the unmodified Summary/Related
  sections in the same file.

## equity-analyst-reviewer (voluntary, round 1 only)
VERDICT: PASS
risks_checked:
- Confirmed the verdict's "financially healthy on these figures" framing is genuinely absolute,
  not relative, by reading `VERDICT_MEANING` and `READ_SYSTEM_PROMPT` directly -- no "vs. peers"
  language anywhere.
- Confirmed the `north_star.md` analogy is fairly applied: Gemini's actual point 9 proposes using
  the mart's existing LIVE `sector_median`/`min`/`max` columns, exactly the same "grading on a
  live curve" mechanism the existing rule already warns against -- not a strawman version.
- Confirmed the biweekly refresh cadence is real (not an invented number) and that the sector
  benchmark floor (8 eligible peers) is small enough to make live medians genuinely volatile,
  strengthening the instability argument beyond what the diff itself claimed.
- Checked every specific threshold number against the live code rather than taking them on
  faith -- all four matched exactly, no invented thresholds, no false precision.
- Caught two precision issues in the stated reasoning (see Round 1 findings above) -- neither a
  fabrication, neither reversing the conclusion, both fixed.
