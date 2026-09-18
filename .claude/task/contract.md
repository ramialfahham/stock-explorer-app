# Task contract
> DISPOSABLE. **Owns:** THIS task's objective, `scope_paths`, reserved decisions and
> `done_when`.
> **Never:** anything that outlives the task. Overwritten by the next task.

objective: Refs #22. Manually triggering the scheduled pipeline (recorded on that issue)
  dropped the ai_read null rate from 84% to 12.3%, and the remaining gap was overwhelmingly
  (87%) one single style check: "does not end on the verdict's meaning" -- a regex requiring
  the literal phrase "on these figures"/"on these numbers" to appear in the read.

  Owner asked to fix this. First attempt was to widen the regex to accept the phrase in
  either word order (confirmed live: Claude routinely writes "These figures show a healthy
  company" instead of "...healthy on these figures", both fully compliant with the prompt,
  only one recognized by the old check). Owner pushed back on a regex-based fix as
  unsystematic -- correctly: no amount of pattern-widening changes that this is a heuristic
  guessing at sentence structure to infer something the code cannot otherwise verify from
  free text. Switched approach instead: the write_card_read tool schema now has a third
  field, `verdict_meaning`, enum-constrained to "healthy"/"mixed"/"fragile" -- the model
  states which meaning its own closing sentence lands on as structured output, exactly the
  same pattern already used for `referenced_metrics` (the numeric hallucination guard). Two
  checks replace the old regex: (1) the reported word must match the verdict this row's
  rules already decided (never the model's own call), (2) the reported word must actually
  appear in the read text too, so the field can't be right while the prose is wrong.

  Verified against real production data three times, not simulated: a 20-card sample against
  the live API with the OLD schema (3 genuine verdict-ending failures, all the "leading form"
  word-order case) confirmed the root cause; a 20-card sample with the NEW schema (20 of 20
  passed, every verdict_meaning field agreeing with the real verdict) confirmed the fix works
  in practice; a further 5-card sample after fixing round 1's finding below (4 of 5 passed --
  the one rejection was the field-vs-text check correctly catching a genuine case where the
  model's structured self-report and its own prose disagreed, not a bug) confirmed nothing
  regressed.

  Round 1 review found two real gaps, both fixed before round 2: scope-auditor caught that
  READ_SYSTEM_PROMPT still told the model to call the tool "with two fields" after this task
  added a third (verdict_meaning) -- a factual field-count correction, not a voice/content
  change, so within scope despite the prompt otherwise being off-limits here. cto-reviewer
  noted `verdict_meaning`'s malformed-payload case (not isinstance(..., str)) had no dedicated
  test, unlike its sibling `referenced_metrics` check on the same line -- added.

scope_paths:
  - scripts/assessment_rules.py
  - scripts/generate_assessments.py
  - tests/tooling/test_assessment_rules.py
  - tests/tooling/test_generate_assessments.py
  - .claude/task/contract.md
  - .claude/task/review.md

decisions_reserved: none -- the owner asked for the fix directly, reviewed and rejected the
  first (regex) approach on the spot, and asked for the structured-field approach by name.

done_when:
  - `READ_TOOL_SCHEMA` requires `verdict_meaning`, enum-constrained to
    healthy/mixed/fragile.
  - `verdict_meaning_violation()` checks the reported word against the verdict already
    decided and against the read text itself; `find_read_style_violations()` no longer
    contains any verdict-ending logic (moved out, not duplicated).
  - `_generate_read()` rejects a mismatch the same way it already rejects a hallucinated
    metric or a style violation -- fail closed, self-heals next run.
  - `pytest tests/tooling/test_assessment_rules.py tests/tooling/test_generate_assessments.py`
    passes, including new coverage for the leading-word-order case (the exact real failure)
    and for a reported-word/verdict mismatch and a reported-word/text mismatch.
  - `pytest tests/` (full suite) passes.
  - `check_no_em_dash.py`, `check_context_budget.py` pass.
  - Live-verified against the real Anthropic API (not just unit tests) both before writing
    the fix (to find real failures) and after (to confirm the new field works) -- done, 20
    real cards each pass, documented above.

impact_map: scripts/assessment_rules.py (tool schema, one new function, one function's
  narrowed scope), scripts/generate_assessments.py (`_generate_read`'s validation sequence),
  matching test coverage. No schema/data/CI change; next scheduled or manually-triggered
  pipeline run is the first real-world exercise of this in production.
