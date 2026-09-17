# Review
> DISPOSABLE. **Owns:** verdicts + diff hash for THIS task's staged change.
> **Never:** narrative of how the round went. Overwritten by the next task.

diff_sha256: 3e2acd199cb42ef1fad438c91b3f547943efbacc7c4559beea9a209553160bae

## scope-auditor
VERDICT: PASS
risks_checked:
- All 10 touched files (frontend/explore_filters.py, frontend/app.py, frontend/overflow_menu.py,
  frontend/browser_storage.py, tests/frontend/test_explore_filters.py,
  tests/frontend/test_app_e2e.py, tests/frontend/test_app.py, tests/frontend/test_browser_storage.py,
  docs/ui/discover_header.md, .claude/task/contract.md) within `scope_paths`.
- Round 2 FAILED correctly: `frontend/app.py` was `MM` (staged + unstaged) -- the staged
  diff genuinely lacked `_save_card()` even though the working-tree file had it, because a
  `git add` after the browser_storage.py fix omitted re-staging app.py. Root-caused and
  fixed (`git add frontend/app.py`); round 3 confirmed the file is a clean single `M` and
  `_save_card()` is present in the staged diff, called from both Save buttons.
- Every `done_when` item verified against the diff: `skipped_keys_with_order()` via shared
  `_latest_action_keys()`, overflow menu count, panel list/detail/Save/Remove, tab-switch
  close, docs updated, test coverage for the round-1 fixes.

## cto-reviewer
VERDICT: PASS
risks_checked:
- **Round 1 FAILED, two real findings:** (1) `browser_storage.py` never persisted
  skip/unskip -- its own docstring documented that as deliberate, a premise this task
  overturns; the Not-now list would silently reset on every reload. (2) Only the Not-now
  panel's Save button was fixed to also unskip; Discover's own sticky Save button still
  only appended "save", so a skipped-then-saved-from-Discover card would end up saved AND
  stuck in Not-now.
- **Round 2: both fixed and verified.** `browser_storage.py`'s save-cookie machinery
  generalized to a second independent cookie namespace (`SKIP_COOKIE_PREFIX`), parameterized
  the same way `_latest_action_keys` was generalized in `explore_filters.py`. Confirmed
  byte-for-byte backward compatible: every pre-existing call site's `prefix=` defaults to
  the original `COOKIE_PREFIX`, `migration_script()` (save-only) correctly left untouched.
  `_save_card()` extracted and confirmed as the ONLY place "save" is appended in `app.py`
  (grepped), used by both Save buttons.
- Also found and fixed while fixing #1 (not a reviewer finding): `clear_interactions()`
  ("Clear saved") used to wipe the whole interactions list, including skip rows, without
  its own confirmation dialog ever mentioning that. Scoped to save/unsave rows only;
  verified the row-filter fails toward RETAINING an unrecognized future action string, not
  dropping it.
- `pytest tests/frontend/test_explore_filters.py` (skip persistence tests exercise both
  cookie namespaces together, not just independently) and the full suite run directly:
  330 passed.

## Verified independently

- `pytest tests/frontend/ -q` -- 330 passed (full suite, after the final re-stage).
- `python scripts/check_no_em_dash.py`, `check_context_budget.py` -- passed.
- Live-verified against a running dev server, real browser cookies (not just AppTest,
  which runs within one continuous session and can't exercise a real reload):
  - Full round trip: skip on Discover -> Not-now list -> open -> Save -> gone from
    Not-now, present in Saved.
  - Skip a company, confirm the `ss_skipped_` cookie is actually set in the browser,
    reload the page for real (not an AppTest rerun) -- still shows in Not-now afterward.
  - "Clear saved" (with its own confirm dialog) leaves an existing Not-now entry untouched.
