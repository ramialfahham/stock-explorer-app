# Task contract
> DISPOSABLE. **Owns:** THIS task's objective, `scope_paths`, reserved decisions and
> `done_when`.
> **Never:** anything that outlives the task. Overwritten by the next task.

objective: Closes #50 (repo hygiene from the quality audit, findings 49-55: logic copied across
  scripts and modules, and tracked files whose job is done). One rule per kind of problem, each with
  an exact search in `.claude/task/hygiene_sweep.py`; the sweep exits 0 when the work is done.

scope_paths:
  - scripts/probe_quarterly_op_labels.py
  - scripts/probe_roa_total_assets.py
  - storage/seeds/_imports/jp_nikkei225_starter.csv
  - .claude/task/dead_code_sweep.py
  - scripts/probe_balance_sheet_labels.py
  - scripts/check_export_health.py
  - scripts/check_eligibility_baseline.py
  - scripts/check_eligibility_gaps.py
  - scripts/check_pipeline_completeness.py
  - scripts/seed_ci_raw_fixtures.py
  - scripts/check_registry_var_sync.py
  - scripts/sync_dbt_vars.py
  - scripts/check_dbt_documentation.py
  - scripts/check_dbt_tests.py
  - scripts/dbt_models.py
  - ingestion/registry.py
  - frontend/card_ui.py
  - frontend/row_ui.py
  - frontend/html_text.py
  - frontend/card_copy.py
  - requirements.txt
  - .gitlab-ci.yml
  - tests/tooling/test_check_export_health.py
  - tests/tooling/test_check_registry_var_sync.py
  - tests/tooling/test_sync_dbt_vars.py
  - tests/tooling/test_seed_ci_raw_fixtures.py
  - tests/ingestion/test_registry.py
  - tests/frontend/test_html_text.py
  - tests/tooling/test_dbt_models.py
  - .claude/active_work.md
  - .claude/task/contract.md
  - .claude/task/review.md
  - .claude/task/hygiene_sweep.py

decisions_reserved: Answered by the owner in chat (2026-10-11): (1) delete
  `probe_quarterly_op_labels.py`; (2) delete the health check's own dedupe, the gate counts mart rows
  as they are (the mart is unique per market and ticker, a dbt test enforces it); (3) include the
  extra copies the rules found (`_esc`, `_sql_model_names`, the CI pytest pin, the old task sweep
  script; `governed_files` / `governed_docs` stay). Still the owner's: a GitLab replacement for the
  removed job summaries (none added); a permanent CI or pre-commit sweep (not built); the
  `GITHUB_ACTIONS` branch in `scripts/apply_supabase_migrations.py` (below).

changes:
  - Finding 49: `check_export_health.py` loses `dedupe_to_latest_snapshot`, `_snapshot_sort_key` and
    its unused `snapshot_date` read; its log wording drops "deduped" (`eligible=N`, "no card-eligible
    rows in mart_stock_cards", "required ticker missing from eligible cards: M:T", "(a/b eligible)").
    Thresholds and pass/fail rules are unchanged. The app keeps its own dedupe.
  - Finding 50: `_append_github_summary`, its 3 call sites and the markdown built only for it are
    removed from the three check scripts. Console output is unchanged.
  - Finding 51: `ingestion.registry.active_market_codes()` (sorted, active only) replaces
    `_load_active_markets` (5 scripts, one never called) and `_registry_active_codes` (2 scripts).
    The registry modules import only the standard library and PyYAML (the pre-commit hook has only
    PyYAML); a test pins that.
  - Findings 52, 53, 54: the one-time import CSV (and its folder), `probe_roa_total_assets.py` and
    `probe_quarterly_op_labels.py` are deleted; the balance-sheet probe's docstring no longer names
    its deleted companion.
  - Finding 55: `requirements.txt` drops the four pins `frontend/requirements.txt` already holds;
    the effective pinned set is identical before and after.
  - Extras: one `esc` in `frontend/html_text.py` (was `_esc` in `card_ui.py` and `row_ui.py`); one
    `sql_model_names` in `scripts/dbt_models.py`; CI reads the pytest pin from `requirements-dev.txt`
    like the pre-commit job does; the previous task's sweep script is replaced by this one. A comment
    in `card_copy.py` that named the removed `_esc` now names `esc`.
  - Stricter registry parsing, from using `load_markets`: a registry row without `market_code` or
    `index_name` now raises even when the row is inactive (the old copies skipped it). The real
    registry and `test_registry_entries_declare_every_required_field` already require both.

done_when:
  - `python .claude/task/hygiene_sweep.py` exits 0 (R1 copies, R2 unused scripts, R3 seed folders,
    R4 repeated pins, R5 GITHUB names in code, R6 removed names). Before the work it printed 50 hits.
  - `pytest tests -q` and `python scripts/bootstrap.py --verify` pass.
  - The effective pinned set of `requirements.txt` + `frontend/requirements.txt` is identical to HEAD's.
  - No change to `assessment_rules.py`, `generate_assessments.py`, the verdict rules, dbt, migrations
    or `export_to_supabase.py`.

keep_list (the sweep exempts these, each for a stated reason):
  - Same name, different job: `main`, `find_violations`, `render`, `_load_mart_rows` (three
    different queries), `_cell`, `_summarize`, and the gate's `_card_key` / `_has_business_summary`
    (mart columns only; the app's also read a raw yfinance field and keep raw key types).
  - Same body over different data: `governed_files` and `governed_docs` (different file patterns).
  - `scripts/apply_supabase_migrations.py` reads `GITHUB_ACTIONS` (a Management-API pooler lookup
    and a "GitHub secret" hint that never run on GitLab). It applies the Supabase migrations, which
    the owner froze during the production run, and a GitLab equivalent is a behavior change.

known_limits:
  - R1 finds identical bodies and shared names; a near-copy that differs in one statement and has a
    different name is not found.
  - R2 counts a mention in a doc, CI, hook config, test or another script's import; it does not
    check that the doc is accurate.
  - `ingestion.registry` must stay importable with PyYAML alone; `validate:pre-commit` in CI would
    catch a break, and `tests/ingestion/test_registry.py` pins the imports of the three registry
    files (standard library, PyYAML, `ingestion.paths`, `ingestion.registry` only).
  - Four scripts and two tests still build the active-code set inline from
    `load_markets(active_only=True)` (`refresh_constituents.py`, `refresh_yfinance_names.py`,
    `record_ingestion_fixtures.py`, `check_company_names_vs_yfinance.py`). They already use the
    registry loader the audit proposed, so R1 does not flag them.

regression_checklist:
  - `--write-baseline` and every script print markets in the same sorted order as before.
  - The health check still fails on: zero eligible rows, fill rate below the minimum, more missing
    than the maximum, a required ticker absent or with an empty summary.
  - The registry var sync and `sync_dbt_vars.py` behave as before on matching, differing and
    missing-block inputs (their tests now use realistic registry rows with `index_name`).
  - Every removed name returns no hit in the sweep's R6 search.
