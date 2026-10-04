# Task contract
> DISPOSABLE. **Owns:** THIS task's objective, `scope_paths`, reserved decisions and
> `done_when`.
> **Never:** anything that outlives the task. Overwritten by the next task.

objective: Closes #30 -- the review cycle converges: delta review after round 1 against a
  fixed regression checklist, declared known limits, graded FAIL, a frozen diff per round,
  and a fixed exit past the round cap.

scope_paths:
  - .claude/working-agreement.md
  - docs/context_budget.yml
  - .claude/agents/platform-reviewer.md
  - .claude/agents/scope-auditor.md
  - .claude/agents/analytics-engineer-reviewer.md
  - .claude/agents/data-engineer-reviewer.md
  - .claude/hooks/commit_review_gate.py
  - tests/tooling/claude_hooks/test_commit_review_gate.py
  - .claude/active_work.md
  - .claude/task/contract.md
  - .claude/task/review.md
  - .claude/task/review_input.patch

decisions_reserved:
  FAIL criteria (owner: option A): a reviewer returns FAIL only for a concrete false block
  (a guard refuses legitimate work), a broken guarantee (a `done_when` item or documented
  behaviour that does not hold, including changed behaviour with no test that would catch
  its revert), or a design problem. Everything else is a follow-up or a wording fix.
  Round cap (owner): stays 3. Past the cap (owner: option A): a `CPO ANSWER:` naming the
  follow-up issue (`#N`) lets the commit through, remaining FAIL verdicts included; any other
  state past the cap is refused.
  Scope (owner): `analytics-engineer-reviewer.md` and `data-engineer-reviewer.md` included;
  `equity-analyst-reviewer.md` left out, filed as #31, exempted in working agreement §2.

known_limits:
  - `_files_the_rest` is a text match: any `#N` after `CPO ANSWER:` in the same paragraph
    counts as filing the rest, whatever the answer says.

regression_checklist:
  - The gate still blocks a commit whose review.md hash does not match, a missing required
    verdict, a FAIL, and an unanswered ESCALATE (existing tests stay green).
  - Every reviewer file's output block still parses with `_verdict` / `_sections`.
  - No rule in working agreement §2 contradicts a reviewer file.

done_when:
  - Working agreement §2 and the in-scope reviewer files state: delta review after round 1
    plus this checklist; `known_limits:`; option-A FAIL grounds with `follow_ups:`; frozen
    diff per round with the verdict naming its hash; the two exits past the cap.
  - The gate's past-cap behaviour matches the owner's decision, with tests.
  - `pytest tests/tooling` and `scripts/check_no_em_dash.py` pass; review cycle run under
    the new rules; MR opened. Not merged.

amendments:
  - Round 1: scope-auditor PASS; platform-reviewer FAIL [broken-guarantee]: the filed-answer
    exit opened only at `rounds: 4`, not after round 3. Fixed (opens at the cap, with tests),
    plus its wording fixes and two follow-ups (issue ref must follow `CPO ANSWER:`; the delta
    command excludes `.claude/task/review*`).
