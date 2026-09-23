# Task contract
> DISPOSABLE. **Owns:** THIS task's objective, `scope_paths`, reserved decisions and
> `done_when`.
> **Never:** anything that outlives the task. Overwritten by the next task.

objective: Slice 2 of the comment trim: bring `#` comments and docstrings under `frontend/`
  in line with `docs/engineering_standards.md` §1.2 (why not what, one sentence, no multi-line
  blocks, no history). Comments and docstrings only: no code and no user-visible string
  changes. `frontend/styles.py` is out of scope (its triple-quoted text is CSS, not prose).

scope_paths:
  - frontend/app.py
  - frontend/browser_storage.py
  - frontend/card_copy.py
  - frontend/card_ui.py
  - frontend/disclosure_html.py
  - frontend/explore_filters.py
  - frontend/live_quote.py
  - frontend/markets.py
  - frontend/metric_school.py
  - frontend/nav_pages.py
  - frontend/overflow_menu.py
  - frontend/row_ui.py
  - frontend/saved_news.py
  - frontend/settings.py
  - frontend/supabase_cards.py
  - frontend/supabase_client.py
  - frontend/timing.py
  - .claude/task/contract.md
  - .claude/task/review.md
  - .claude/active_work.md

decisions_reserved: none -- §1.2 already codifies the target; no copy, label or behaviour
  changes.

done_when:
  - No `#` block over two lines; every edited comment is one sentence stating why, with no
    history; docstrings keep a summary line plus only what a caller needs.
  - Each touched file's AST, docstrings removed, is identical to `main`'s.
  - `pytest tests/frontend`, `scripts/check_no_em_dash.py`, `scripts/check_no_narrative_dates.py`
    pass.
  - Review cycle run per `.claude/review_routing.json`, committed, MR opened. Not merged.
