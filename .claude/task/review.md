# Review
> DISPOSABLE. **Owns:** verdicts + diff hash for THIS task's staged change.
> **Never:** narrative of how the round went. Overwritten by the next task.

diff_sha256: 26ab153522b74b1b43804c0dfdb26427915cf5752f2fa5fb4f346ceec1790158

## cto-reviewer
VERDICT: PASS
risks_checked:
- `_discover_pool()` (frontend/app.py) is the single source of truth for Discover's row
  set: query set -> `_search_matches`, else -> `filter_pool`. No competing pool builder.
- `_render_discover_tab()` has no leftover search-specific branching: one row list
  (`key_prefix="discover_row"`), one focus-key lookup, one back row
  (`key="discover_back_to_list"`). Confirmed zero remaining references to
  `search_selected`, `_render_search_results`, `_render_search_focused_card`,
  `_select_search_row`, `_card_key` anywhere in frontend/app.py.
- Row keys and back-button keys rethreaded consistently across both test files, not a
  partial rename.
- Stale-focus-key revalidation is a single shared implementation: `_render_discover_tab`
  re-validates `discover_focus_key` against whatever `pool` `_discover_pool` returned that
  run, so a card falling out of a changed query resets exactly like one falling out of a
  changed filter -- same mechanism, not a new special case.
- Saved tab and Not-now panel use their own focus keys and row-key function, untouched by
  this diff; no accidental cross-tab state sharing introduced.
- Round 1 found a real defect: `_render_discover_scope_stats` hardcoded "N match your
  filters" and was now shown during an active search too, where the wording was factually
  wrong (no filters applied). Round 2 confirms the fix is complete: the function now
  branches on an explicit `query` param, the call site passes the current-run query with no
  staleness window (`_sync_search_query` already ran before `_discover_pool` is read), the
  whole label -- either branch -- is still wrapped in `html.escape`, and the new negative/
  positive test assertions are real regression guards (verified via exact codepoints, not
  terminal rendering), not tautologies.
- `pytest tests/frontend -q`: 329 passed. `pytest tests/ -q` (excluding the pre-existing,
  unrelated `tests/tooling/test_generate_assessments.py` collection error caused by a
  missing `anthropic` import when run outside `.venv`): 796 passed.
- `check_no_em_dash.py` and `check_context_budget.py` both pass against the staged diff.
- No new dependency, service, CI step, or hook. Net -34 lines in frontend/app.py.

## scope-auditor
VERDICT: PASS
risks_checked:
- Staged diff touches exactly `.claude/task/contract.md`, `frontend/app.py`,
  `tests/frontend/test_app.py`, `tests/frontend/test_app_e2e.py` -- all within
  `scope_paths`. `.claude/task/review.md` written after this verdict, as expected.
- `_search_matches` itself is untouched by this diff -- still matches against the full
  deck with no market/sector scoping, confirming search stays global per the prior
  AskUserQuestion decision (issue #20) and was not silently re-scoped alongside the
  state-machine unification.
- Tests assert the NEW behavior, not the old: search-opened cards now assert Save/Not-now
  ARE present (old read-only assertions removed), unified `discover_row_*`/
  `discover_back_to_list` keys used throughout.
- Round 1 finding (the scope-stats wording lying about "filters" during a search --
  User-visible wording is an owner decision per working-agreement.md SS6, and the contract's
  original `decisions_reserved: none` didn't actually cover this) is resolved in round 2:
  contract.md now explicitly documents the wording fix and that round 1 caught it. The new
  copy ("N match "query"") is not a fresh unilateral wording decision -- it reuses the
  exact curly-quote-around-the-raw-query convention already shipped on `main` in the
  adjacent empty-state message (`git log -S` traced to commit 5983794c, pre-existing), so
  it's precedent-following, not new-copy-inventing.
- `pytest tests/frontend -q`: 329 passed. `check_no_em_dash.py` / `check_context_budget.py`:
  both pass against the current staged diff.

## Verified independently
- Full suite: `pytest tests/ -q` (excluding the pre-existing, unrelated
  `tests/tooling/test_generate_assessments.py` collection error -- missing `anthropic`
  import when run outside `.venv`, not touched by this task) -- 796 passed.
- Live browser, full flow: typed "apple" -> list narrows to the one match, Filters popover
  hidden, stats line reads `1 match "apple"` (not the stale "matches your filters" claim).
  Clicked the row -> card opens directly with Save/Not now visible (the exact bug the owner
  screenshotted: "clicking on the field, apple content opens, but i'm not on a card").
  Clicked Back -> returned to the same one-match "apple" results, not empty or stale.
  Switched to Saved, back to Discover -> search cleared, Filters popover restored, full
  1021-company list showing again (the "and clicking on discover here does nothing" bug,
  now fixed).
