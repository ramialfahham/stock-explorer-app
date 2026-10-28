# Task contract
> DISPOSABLE. **Owner:** THIS task's objective, `scope_paths`, reserved decisions and
> `done_when`.
> **Never:** anything that outlives the task. Overwritten by the next task.

objective: Works #81 (DBT-5 defects 6 and 7 of the second quality-baseline audit re-run). `docs/engineering_standards.md`
  section 1.2 says "One sentence per comment, which may wrap onto more than one line"; `dbt_project.yml` has a
  three-sentence comment and `_intermediate_unit_tests.yml` has ten more multi-sentence comment blocks. One rule over
  every case: every comment block under `dbt_analytics/` is one sentence, and explanation that does not fit one
  sentence moves to the unit test's `description:` field (a dbt field for prose, not a comment).

scope_paths:
  - dbt_analytics/dbt_project.yml
  - dbt_analytics/models/4_intermediate/_intermediate_unit_tests.yml
  - .claude/active_work.md
  - .claude/task/contract.md
  - .claude/task/review.md

decisions_reserved: Answered by the owner in chat: a semicolon joining two clauses keeps a comment one sentence (answer A), so
  the seven semicolon-joined comments in five other dbt files stay as they are. The rule is written
  (`docs/engineering_standards.md` section 1.2); the audit's own proposed fix names `description:` as the home for the
  arithmetic. No test, fixture value, expectation or model changes.

changes:
  - `dbt_project.yml`: the three-sentence comment above `active_market_codes` is one sentence.
  - `_intermediate_unit_tests.yml`: for each of the ten multi-sentence blocks, the prose becomes the unit test's
    `description:` (worked quartile arithmetic, fixture shape, eligibility reasoning), or, for the boundary comment in
    `card_metrics_company_type_classification`, one sentence. The text states the same facts, reflowed.
  - `.claude/active_work.md`: current facts.

done_when:
  - A scan of every `#` and `--` comment block under `dbt_analytics/` (`.sql`, `.yml`, excluding `target/` and
    `dbt_packages/`) for two or more sentences reports zero blocks (it reported 11 before; the scan counts a period
    followed by a space and any letter, and a semicolon stays inside one sentence (owner answer A); it is a scratch script, not a
    committed check).
  - `dbt build` with the CI fixtures passes: 149 of 149, including all 29 unit tests.
  - `pytest tests -q` passes; `check_registry_var_sync.py` passes (it reads `active_market_codes`).
  - Every `description:` added sits directly under its `- name:` line, and no fixture row, `expect` row or model
    reference changed (the diff shows only comment removals and `description:` additions, plus the one reworded
    boundary comment).

known_limits:
  - The sentence scan is a heuristic (a period followed by a space and a letter); a comment it cannot see is not covered.
  - Comments outside `dbt_analytics/` (Python, docs) are out of this task; the audit named only these two files.

regression_checklist:
  - The unit tests keep their names, models, inputs and expectations; the `dbt build` count stays 149.
