# Task contract
> DISPOSABLE. **Owns:** THIS task's objective, `scope_paths`, reserved decisions and
> `done_when`.
> **Never:** anything that outlives the task. Overwritten by the next task.

objective: Closes #35 -- the seed guard catches a Wikipedia marker mid-name
  (`Kalmar [fi] B`), not only at the end.

scope_paths:
  - tests/ingestion/test_market_onboarding.py
  - .claude/task/contract.md
  - .claude/task/review.md
  - .claude/task/review_input.patch

decisions_reserved: settled by the owner in-thread before implementation (option B) --
  `_clean_company_name` is unchanged and keeps stripping trailing markers only; the seed
  guard flags a mid-name marker; the guard checks the override-applied name (the name the
  card renders), so a `company_name_overrides.csv` row clears a flagged seed name. No seed
  or override data change.

done_when:
  - The bracket half of the seed guard matches a short bracket anywhere in the name.
  - The guard checks the override-applied name per (market_code, resolved ticker).
  - A test fails if the bracket half is re-anchored to the end of the name.
  - The fi_omxh25 guard fails if the override lookup is removed (Kalmar's seed name).
  - A unit test fails if the guard skips override names instead of checking them.

known_limits:
  - Any seed artifact with an override row now passes the guard, in all three halves; the
    override is the accepted human decision.

regression_checklist:
  - Every active market's seed still passes the guard on the committed data.
  - An override name carrying an artifact still fails the guard.
  - The writer's own tests (`tests/ingestion/test_constituent_seeds.py`) are untouched.
