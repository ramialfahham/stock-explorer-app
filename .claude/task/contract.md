# Task contract
> DISPOSABLE. **Owns:** THIS task's objective, `scope_paths`, reserved decisions and
> `done_when`.
> **Never:** anything that outlives the task. Overwritten by the next task.

objective: The AI read prompt tells the model to avoid every word the advice guard rejects. The
  2026-10-11 production run rejected 13 of 223 new reads on "sells"/"selling" used about what a
  company does; each rejected card shows the fixed verdict line and is called again every run.

scope_paths:
  - scripts/assessment_rules.py
  - tests/tooling/test_assessment_rules.py
  - .claude/active_work.md
  - .claude/task/contract.md
  - .claude/task/review.md

decisions_reserved: the prompt wording is owner-signed content (section 6). The owner was shown
  the finding and the proposed rule in plain words and answered "sells rule yes". The guard is
  unchanged: a read that uses buy, buys, buying, sell, sells, selling or price is still rejected.

changes:
  - Prompt: one bullet after the advice rule says never to use those seven words anywhere, even
    about what the company does or charges, and to say "sales" or "revenue" or name what it makes.
  - A test pins the bullet and that every listed word is one the guard matches.
  - Handover: the 2026-10-11 run's results and what is still unchecked.

done_when:
  - `READ_SYSTEM_PROMPT` contains the new bullet and the test passes.
  - The advice guard and its tests are unchanged.
  - `INPUT_HASH_VERSION` unchanged (already pinned); `pytest tests` and
    `python scripts/bootstrap.py --verify` pass.

known_limits:
  - The prompt cannot be exercised without an API call (zero spend), so whether the rejection
    rate falls shows only in the next run's `read REJECTED` lines.
  - The bare-word guard also rejects "price" in a compound such as "price-to-earnings"; the new
    rule covers it by telling the model to avoid the word.
  - A read rejected for any reason leaves `ai_read` empty and is called again every run.

regression_checklist:
  - The other prompt rules and their tests are unchanged.
  - Stored reads and the frontend are untouched.
