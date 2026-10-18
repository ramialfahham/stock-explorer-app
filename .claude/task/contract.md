# Task contract
> DISPOSABLE. **Owner:** THIS task's objective, `scope_paths`, reserved decisions and
> `done_when`.
> **Never:** anything that outlives the task. Overwritten by the next task.

objective: Closes #55. Planning-phase labels ("Slice 5b", "Router 4a", bare "5a", "6b") remain in code
  comments, docstrings, migration headers and two doc lines. They are history, which
  `docs/engineering_standards.md` section 1.2 forbids in comments. One rule over every case: delete the
  label and keep the reason the comment gives; where the label is the only content, restate the current
  state (for example "null until the read is generated"). Comment and docstring text only.

scope_paths:
  - .env.example
  - frontend/styles.py
  - scripts/assessment_rules.py
  - scripts/generate_assessments.py
  - supabase/migrations/007_router_card_columns.sql
  - supabase/migrations/008_financial_card_metrics.sql
  - supabase/migrations/009_pre_revenue_card_metrics.sql
  - supabase/migrations/010_card_assessments.sql
  - dbt_analytics/models/4_intermediate/_intermediate_unit_tests.yml
  - docs/supabase_setup.md
  - docs/data_contract.md
  - tests/frontend/test_card_copy.py
  - tests/frontend/test_card_ui.py
  - tests/tooling/test_assessment_rules.py
  - tests/tooling/test_generate_assessments.py
  - .claude/active_work.md
  - .claude/task/contract.md
  - .claude/task/review.md

decisions_reserved: The owner answered A in chat: also fix the bare codes ("5b", "4c", "6a") and the two
  files the issue does not list (the dbt unit-test comments, the three `docs/supabase_setup.md` ledger
  rows that copy the migration headers). No behaviour, schema, verdict, prompt or export change.

done_when:
  - `git grep -n -i -E "slice[ -]?[0-9]|across slices|router [0-9][abc]" -- . ':!.claude/task' ':!.claude/active_work.md'`
    finds nothing.
  - `git grep -n -E "\b[3-6][abc]\b" -- scripts frontend/styles.py supabase dbt_analytics tests/frontend tests/tooling docs/data_contract.md .env.example`
    finds nothing (the version string `5a.6` is not matched by `\b5a\b`).
  - Keep list, untouched: the English word "slice" (`_discover_page_slice` in `frontend/app.py` and
    `tests/frontend/test_app.py`, `frontend/card_copy.py`, `frontend/metrics.json`,
    `dbt_analytics/seeds/metric_catalogue.csv`); the version string `INPUT_HASH_VERSION = "5a.6"` and the
    test pinning it; the section headings "3b" and "3c" in `docs/supabase_setup.md` and the anchor
    link to "3b" in `docs/operations_guide.md`; binary fixtures.
  - `git diff main --stat` shows only comment, docstring and prose lines changed; the full test suite and
    `python scripts/bootstrap.py --verify` pass.

known_limits:
  - The search is a text pattern: a label written in words ("the fifth slice") would not match. None was
    found by reading the matches.

regression_checklist:
  - Every comment still states its current reason; no code line, string literal used by a test, or SQL
    statement changed (the `--help` description of `generate_assessments.py` loses "(Slice 5)" and no
    test pins it).
  - The migration files change in comment lines only, so applying them gives the same schema.
