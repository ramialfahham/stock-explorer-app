# Task contract
> DISPOSABLE. **Owns:** THIS task's objective, `scope_paths`, reserved decisions and
> `done_when`.
> **Never:** anything that outlives the task. Overwritten by the next task.

objective: Context debt, one task. The handover's `## Do NOT` rules move to durable homes and
  the section becomes an index; dead code-comment pointers to `.claude/task/contract.md` go;
  dates come out of code comments, the comments stay; `sources.yml` names the `data-pipeline`
  job instead of `data_pipeline.yml`. Issue #10 closed on GitLab (fixed by !130).

scope_paths:
  - .claude/working-agreement.md
  - .claude/active_work.md
  - docs/data_contract.md
  - docs/metric_layer.md
  - docs/operations_guide.md
  - docs/development_workflow.md
  - docs/context_budget.yml
  - dbt_analytics/models/sources.yml
  - dbt_analytics/models/2_base/yfinance/base_yf__constituents.sql
  - dbt_analytics/models/4_intermediate/int_stock__card_metrics.sql
  - frontend/card_copy.py
  - frontend/card_ui.py
  - frontend/explore_filters.py
  - frontend/row_ui.py
  - frontend/styles.py
  - scripts/assessment_rules.py
  - tests/frontend/test_styles.py
  - .claude/task/contract.md
  - .claude/task/review.md

decisions_reserved:
  - None new. Every rule moved is an owner rule already in force; the move records it where
    the thing it governs lives. Wording of moved rules is compressed, not changed in meaning.
  - `docs/data_contract.md`'s budget 59000 to 59500: the standing rules add about 800 bytes
    of contract text to a file that was 790 under its cap.
  - `supabase/migrations/*.sql` keep their dates: applied history, and `013`'s `COMMENT ON`
    literal is the text production already holds.

done_when:
  - `git grep -n "task/contract.md" -- '*.py' '*.sql'` returns nothing.
  - `git grep -nE "20[0-9]{2}-[0-9]{2}-[0-9]{2}"` over `frontend/`, `scripts/`, `ingestion/`,
    `dbt_analytics/models`, `dbt_analytics/macros`, `dbt_analytics/tests` and `tests/` returns
    only data (snapshot dates, fixtures), no comment or docstring.
  - Each former Do NOT rule has one durable home and the handover's `## Do NOT` lists where:
    spend and owner-only ops, plain questions (`.claude/working-agreement.md` §6, §8);
    statement lines over `info` scalars, no data-layer clipping, the yfinance ceiling
    (`docs/data_contract.md`); `applies_to` from the first row (`docs/metric_layer.md`);
    the snapshot gate (`frontend/explore_filters.py` docstring); performance and
    `DECK_COLUMNS` (`docs/operations_guide.md`); validate before push
    (`docs/development_workflow.md`). Rules already durable (no merge, no advice, plan mode,
    owner wording) are pointed at, not copied.
  - `sources.yml` no longer names `data_pipeline.yml`; `dbt parse` passes; `sqlfluff` passes
    on the two touched models.
  - Every budget in `docs/context_budget.yml` still passes; `pytest tests/ -q` green.

impact_map: Comments and docs only; no behaviour, no SQL logic, no test assertion changed.
