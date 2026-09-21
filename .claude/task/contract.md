# Task contract
> DISPOSABLE. **Owns:** THIS task's objective, `scope_paths`, reserved decisions and
> `done_when`.
> **Never:** anything that outlives the task. Overwritten by the next task.

objective: Refs #22. A manually-triggered production run (2026-09-21, pipeline 2867216473,
  after commit 8c53a75e's structured `verdict_meaning` field fix) confirmed the fix worked --
  no more of the old "does not end on the verdict's meaning" phrase-matching rejections. But
  4 of the run's 10 failures are a narrower version of the same brittleness:
  `verdict_meaning_violation`'s second check requires the exact literal word ("healthy"/
  "mixed"/"fragile") to appear in the read text, so a compliant read that expresses the same
  meaning with a different word (e.g. "financially strained" instead of "fragile") is
  wrongly rejected -- exactly the "different words, same meaning" brittleness the function's
  own docstring already describes as the thing being fixed, just moved from phrase-level to
  word-level.

  Owner-approved fix: `verdict_meaning_violation`'s second check accepts a small, fixed
  synonym set per meaning instead of only the exact word. Owner reviewed and approved this
  exact list (no adjustments requested):
  - healthy -> also accept: strong, solid, sound
  - mixed -> also accept: uneven, in between
  - fragile -> also accept: strained, weak, struggling

  The first check (reported `verdict_meaning` must match the verdict already decided by
  deterministic rules) is UNCHANGED -- that is the real safety guarantee and was not in
  question. This only widens what counts as "the sentence actually reflects the label."

  Round-2 review finding: a plain substring match on "solid"/"strained"/"weak" collides with
  ordinary financial vocabulary unrelated to the verdict's meaning ("consolidated" contains
  "solid", "constrained"/"restrained" contain "strained", "tweak" contains "weak") -- a more
  likely false-accept than the pre-existing "healthy"/"unhealthy" case. Fixed by matching on
  whole-word boundaries (`\bword\b`) instead of a bare substring, for every entry including
  the canonical word -- a mechanism fix, not a new word-choice decision, so not re-escalated.

scope_paths:
  - scripts/assessment_rules.py
  - tests/tooling/test_assessment_rules.py
  - .claude/task/contract.md
  - .claude/task/review.md

decisions_reserved: The synonym list itself is owner-reserved content (word choice/prompt
  content per working-agreement.md SS6) -- already answered live, the three lists above are
  verbatim what the owner approved. No further wording decision is open.

done_when:
  - `verdict_meaning_violation`'s second check passes when the read text contains the
    canonical word OR any of its approved synonyms, matched on whole-word boundaries
    (`\bword\b`), not a bare substring.
  - The first check (reported meaning vs. actual verdict) is untouched -- same behavior,
    same error message.
  - `test_verdict_meaning_violation_accepts_a_matching_report`,
    `test_verdict_meaning_violation_accepts_the_leading_word_order`, and
    `test_verdict_meaning_violation_catches_a_mismatch_against_the_actual_verdict` pass
    unmodified. `test_verdict_meaning_violation_catches_a_reported_word_missing_from_the_text`
    still passes but its fixture text changed ("Margins are strong and debt is low." ->
    "Margins are thin and debt is high.") because "strong" is now an accepted healthy-synonym
    and would no longer represent "meaning missing from the text" -- same intent, fixture
    updated to match.
  - New tests cover: a read using a synonym instead of the canonical word is accepted for
    each of the three meanings; a read using an unlisted near-miss word ("promising") is
    still rejected; a read using an unrelated word that merely CONTAINS a synonym as a
    substring ("consolidated" contains "solid", "constrained"/"restrained" contain
    "strained") is still rejected -- the word-boundary-match regression check.
  - `pytest tests/` passes in full.
  - `check_no_em_dash.py`, `check_context_budget.py` pass.

impact_map: `scripts/assessment_rules.py` (`verdict_meaning_violation`'s second check
  widened to a synonym set per meaning), matching test additions in
  `tests/tooling/test_assessment_rules.py`. No change to the first check, the prompt, the
  tool schema, or any other file. No new dependency, service, or CI change.
