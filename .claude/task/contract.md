# Task contract
> DISPOSABLE. **Owner:** THIS task's objective, `scope_paths`, reserved decisions and
> `done_when`.
> **Never:** anything that outlives the task. Overwritten by the next task.

objective: Works #82 (FE-3 defect 17, FE-2 defect 18, FE-1 defect 21 of the second quality-baseline audit re-run). One
  rule per defect: every metric a filter preset checks is a column of the deck rows; every `.ss-*` class and `--ss-*`
  custom property in the stylesheet is used; a snapshot date prints with no leading zero on the day.

scope_paths:
  - frontend/supabase_cards.py
  - frontend/styles.py
  - frontend/card_copy.py
  - tests/frontend/test_supabase_cards.py
  - tests/frontend/test_styles.py
  - tests/frontend/test_card_copy.py
  - tests/frontend/test_overflow_menu.py
  - .claude/active_work.md
  - .claude/task/contract.md
  - .claude/task/review.md

decisions_reserved: Both owner calls are answered (2026-10-28). Defect 17: answer A, load `net_margin_pct` so the High
  margin pill works as written for financial cards. Defect 21: answer A, the day prints without a leading zero, as the
  wireframe in `docs/ui/saved_list.md` already shows. No preset cutoff, label or card face changes.

changes:
  - `DECK_COLUMNS` gains `net_margin_pct`. The High margin pill now filters financial cards (net margin above 20); before,
    the value was never loaded, so the check passed every financial card.
  - `frontend/styles.py`: deletes the rules for `.ss-saved-fresh`, `.ss-header-pool`, `.ss-market-breakdown` (with its
    summary and body), `.ss-metric-sources`, `.ss-benchmark-compare` (with its summary), `.ss-benchmark-note` (selector),
    `.ss-explain-all` (with its parts), `.ss-explain-list` (with dt, dd), `.ss-card-footer`, and the custom property
    `--ss-bottom-nav-h`; two comments that named a deleted class are shortened.
  - `format_snapshot_date` returns `June 8, 2026` (no `%d` padding, no platform-specific `%-d`).
  - Tests: every metric in `METRIC_PRESETS` is in `DECK_COLUMNS`; every stylesheet class is emitted by a frontend module
    and every custom property is read; `format_snapshot_date` is pinned with literal strings; the About-menu test asserts a
    literal date instead of repeating the code's own format call.

done_when:
  - Removing `net_margin_pct` from `DECK_COLUMNS`, adding a stylesheet rule for an unused class, declaring an unused
    `--ss-*` property, and restoring the `%d` format each fail a test (mutation-checked).
  - `git grep -n -E "ss-saved-fresh|ss-explain-(all|list)|ss-market-breakdown|ss-header-pool|ss-bottom-nav-h|ss-benchmark-compare|ss-metric-sources|ss-benchmark-note|ss-card-footer([^-]|$)" -- frontend tests docs` finds nothing.
  - `pytest tests -q` passes; `python scripts/check_context_budget.py` passes.

known_limits:
  - The class test reads the frontend source for the literal class name, so a class built from a prefix and a variable
    would count as unused. None is built that way today.
  - The class test counts a class name found anywhere in the other frontend `.py` files, a comment or docstring included,
    so a dead rule whose name is only mentioned there would pass.
  - The High margin pill's effect on the live deck is not measured here; no browser run, the deck needs Supabase.

regression_checklist:
  - Other presets and their checks are untouched; `_card_matches_preset` is unchanged.
  - The deck query selects one more column, `net_margin_pct`, which exists in `mart_stock_cards` and in migration 008.
  - No other rule in `frontend/styles.py` changes.
