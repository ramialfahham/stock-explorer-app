# Task contract
> DISPOSABLE. **Owns:** THIS task's objective, `scope_paths`, reserved decisions and
> `done_when`.
> **Never:** anything that outlives the task. Overwritten by the next task.

objective: The live site's cold start (after a deploy or Render's sleep) is 26 to 44 s, of
  which 20 to 33 s is Python importing the app on Render's box. yfinance is the largest
  piece the app does not need at start (4.3 s here, with pandas and numpy behind it) and
  only the Saved tab's headlines use it. Import it there, not with the app.

scope_paths:
  - frontend/saved_news.py
  - tests/frontend/test_import_cost.py
  - tests/frontend/test_saved_news.py
  - .claude/task/contract.md
  - .claude/task/review.md
  - .claude/active_work.md

decisions_reserved:
  - Owner chose this (A) over a faster host first (B), 2026-09-14. No behaviour change: the
    first Saved-news fetch pays the import once per process, inside a call already wrapped in
    try/except and cached for an hour.

done_when:
  - `import yfinance` lives inside `_fetch_news`; importing `app` loads neither yfinance nor
    pandas nor numpy (subprocess test; fails against HEAD).
  - `_fetch_news` runs against a fake `yfinance` in `sys.modules` in a unit test, so a
    deleted in-function import fails a test instead of being swallowed into "Could not load
    headlines" (mutation-proven).
  - Measured here, best of five: `import app` 6.72 s and 2,097 modules before, 5.26 s and
    1,572 modules after. Live cold-start numbers after the deploy go in the handover.
  - `pytest tests/ -q` green.

impact_map: One import moved; the Saved tab's first news fetch per process is slower by the
  import it now carries.
