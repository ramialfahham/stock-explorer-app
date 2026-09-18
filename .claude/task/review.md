# Review
> DISPOSABLE. **Owns:** verdicts + diff hash for THIS task's staged change.
> **Never:** narrative of how the round went. Overwritten by the next task.

diff_sha256: 01a5ca98b072178c6293a36fff49f910486e230c9450c8c8cf34a18e9f204534

## cto-reviewer
VERDICT: PASS
risks_checked:
- `_VERDICT_ENDING_RE` genuinely deleted, not left dead alongside the new check -- grepped
  the whole repo, zero hits outside contract/handover prose. `find_read_style_violations`'s
  docstring updated to say the verdict-meaning check moved out, not duplicated.
- `verdict_meaning_violation(verdict, read, reported_meaning)`: two independent checks,
  proven independent by the two dedicated tests (a mismatch-vs-verdict case passes even
  when the word IS in the text; a missing-from-text case fails even when the reported word
  matches the verdict) -- neither check can silently cover for the other. Compares against
  the DETERMINISTIC verdict (`record["health_verdict"] = compute_verdict(row)`, traced
  through the call chain to `_generate_read`), never anything derived from the model's own
  response.
- `_generate_read`'s new validation sequence: `verdict_meaning` extracted and type-checked
  in the same malformed-payload branch as `referenced_metrics`; a violation fails closed
  (`return None, None`) the same way every other rejection reason already does.
- Round 1 found two real gaps, both fixed before round 2: `READ_SYSTEM_PROMPT` still said
  the tool takes "two fields" after this task added a third (`verdict_meaning`) -- corrected
  to "three fields" in one isolated hunk, confirmed nothing else in the prompt's rules,
  company-type lens, or voice was touched. `verdict_meaning`'s malformed-payload case had no
  dedicated test (unlike its sibling `referenced_metrics` check on the same line) -- added,
  traced to confirm it actually catches removal of that specific clause (the rejection
  message changes from "malformed tool payload" to a verdict-meaning rejection otherwise).
- `pytest tests/tooling/test_assessment_rules.py tests/tooling/test_generate_assessments.py`:
  178 passed. Full suite `pytest tests/`: 841 passed. `check_no_em_dash.py`,
  `check_context_budget.py`: both pass (one round hit a session-local git-on-PATH artifact
  unrelated to the diff, confirmed clean by manual dash scan and by re-running with PATH
  fixed).
- Scope: exactly 5 files (scripts/assessment_rules.py, scripts/generate_assessments.py,
  tests/tooling/test_assessment_rules.py, tests/tooling/test_generate_assessments.py,
  .claude/task/contract.md), no dependency/CI/hook file touched.

## scope-auditor
VERDICT: PASS
risks_checked:
- `READ_SYSTEM_PROMPT` scope held: the contract explicitly puts this prompt's voice/content
  off-limits except the one factual field-count correction. Read the diff hunk line by line
  against the full prompt text -- only "two fields" -> "three fields" plus naming
  `verdict_meaning` changed; every other rule (tone, beginner-language, investment-advice
  ban, jargon rule, numbers-only reasoning, company-type lens) is unchanged context in the
  same hunk.
- Doc-sync: grepped `docs/` for every claim this change makes stale ("on these figures",
  "two fields", "VERDICT_ENDING", etc.) -- the only hits are the two frozen archive docs,
  correctly excluded, never edited for later changes. No live doc described the old
  mechanism, so nothing needed updating.
- `find_read_style_violations()` narrowed cleanly: the old regex and its violation-append
  block are fully removed, the equivalent check exists only in the new, separate
  `verdict_meaning_violation()` -- matches `done_when`'s "moved out, not duplicated."
- New test (`test_attach_reads_rejects_a_non_string_verdict_meaning`) stays inside
  `scope_paths`, mirrors its sibling test exactly, adds no unrelated coverage.
- `_generate_read()`'s fail-closed wiring confirmed: `verdict_meaning_violation` runs after
  the hallucination check and before the style check, rejects the same way every other
  reason already does.
- `pytest` (targeted + full suite), `check_no_em_dash.py`, `check_context_budget.py`: all
  pass (one round's failures traced to a session-local PATH artifact, not the diff --
  re-confirmed clean with PATH fixed).

## Verified independently
- Verified against real production data three separate times across this task, not
  simulated: a 20-card sample against the live API with the OLD schema (3 genuine
  verdict-ending failures, all the "leading form" word-order case -- confirmed the root
  cause before writing any fix); a 20-card sample with the NEW schema (20 of 20 passed,
  every `verdict_meaning` field agreeing with the real deterministic verdict -- confirmed
  the fix works in practice); a 5-card sample after the round-1 prompt-text fix (4 of 5
  passed -- the one rejection was the field-vs-text check correctly catching a real case
  where the model's structured self-report and its own prose disagreed, not a bug).
