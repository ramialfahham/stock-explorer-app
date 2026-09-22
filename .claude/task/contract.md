# Task contract
> DISPOSABLE. **Owns:** THIS task's objective, `scope_paths`, reserved decisions and
> `done_when`.
> **Never:** anything that outlives the task. Overwritten by the next task.

objective: Follow-up from a manual dbt-layer audit (owner asked "is the repo consistent and
  clean", prompted by finding the `dbt-doctor` GitHub Action). The audit found the
  transformation layer clean against `docs/layering.md`/`docs/engineering_standards.md` --
  no layer-rule violations, full doc/test coverage, all mechanical gates pass -- but 8
  pre-existing files under `dbt_analytics/` still carry literal em-dash (U+2014) or en-dash
  (U+2013) characters, grandfathered by `check_no_em_dash.py`'s own design (it only checks
  diff lines, not the whole tree). Owner asked to start with this item.

  Fix: replace every em/en-dash with `--` (the written rule's literal form,
  `engineering_standards.md` SS1.3), with exactly one owner-approved exception: a numeric
  range (e.g. "0-100 scale") uses a plain hyphen, not `--`, since `0--100` reads as broken
  -- asked and answered live rather than assumed.

  Round-1/2 review findings, both fixed: (1) `_marts.yml`'s 14 em-dashes were converted to a
  colon with no genuine same-file precedent (confirmed via `git show HEAD`) -- an
  unauthorized extension of a colon exception. Reverted to `--`. (2) The colon exception
  itself was then found to have no basis in the written rule at all (SS1.3 says only "Use
  `--`", no colon carve-out anywhere in `docs/`) -- scope-auditor's point, not just a
  misapplication. Eliminated the colon exception entirely, but missed two lines the first
  pass: `_docs.md`'s two non-numbered bullet headers (`**operating**`, `**pre_revenue**`)
  still carried a colon -- fixed alongside the 4 numbered items already caught, all 6 now
  `--`. `_intermediate.yml`'s 11 touched instances also `--`. Full re-verification this round:
  zero remaining em/en-dash anywhere in scope, and the numeric-range hyphen (asked and
  approved) is the only non-`--` substitution left in the entire diff.

scope_paths:
  - dbt_analytics/README.md
  - dbt_analytics/dbt_project.yml
  - dbt_analytics/models/3_core/_core.yml
  - dbt_analytics/models/4_intermediate/_intermediate.yml
  - dbt_analytics/models/5_marts/_marts.yml
  - dbt_analytics/models/5_marts/mart_stock_cards.sql
  - dbt_analytics/models/_docs.md
  - dbt_analytics/seeds/_seeds.yml
  - .claude/task/contract.md
  - .claude/task/review.md

decisions_reserved: One -- the numeric-range plain-hyphen exception, asked and approved live
  (owner chose "0-100" over the literal-rule "0--100"). Everything else is the written rule
  applied with zero interpretation: `--` for every em/en-dash, no other exception.

done_when:
  - Zero U+2014/U+2013 characters remain anywhere under `dbt_analytics/` (excluding
    `dbt_packages/`, `target/`, and `logs/`, all vendored/generated/gitignored, not source).
  - No prose meaning changed -- every fix is a character swap, verified by reading the
    surrounding sentence before and after each edit.
  - `dbt parse` (or the project's existing dbt-based CI checks) still succeeds -- YAML
    stays valid, no description string was accidentally broken.
  - `check_no_em_dash.py`, `check_context_budget.py` pass on the staged diff.
  - `pytest tests/` passes in full (no Python file touched, included for completeness).

impact_map: Eight `dbt_analytics/` files (one SQL model comment, one `dbt_project.yml`
  comment, four YAML model-description files, one README, one shared docs-block file) --
  character-level dash substitution only. No model logic, no dependency, no CI change.
