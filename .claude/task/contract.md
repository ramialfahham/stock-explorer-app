# Task contract

objective: **Test-architecture cleanup — clarity of "what we test where" (behavior-preserving).** Organize the
  flat `tests/` dir into domain subdirs (`ingestion/`, `frontend/`, `tooling/`), centralize `sys.path` in a
  single `tests/conftest.py` (removing per-file boilerplate), and write the test taxonomy down
  (`tests/README.md` + a pointer from `engineering_standards.md §3`). No test logic changes; `pytest tests/`
  still passes 80. The dbt/seed/gate separation was already sound (the seed is dbt-tested; export-health is a
  legitimate Python gate), so no test was migrated. Approved plan: ~/.claude/plans/logical-roaming-brook.md.

scope_paths:
  - tests/conftest.py
  - tests/README.md
  - tests/ingestion/test_balance_sheet.py
  - tests/ingestion/test_quarterly.py
  - tests/frontend/ (11 Streamlit tests — git mv + stripped sys.path boilerplate)
  - tests/tooling/test_audit_mart_vs_yfinance.py
  - tests/tooling/test_check_export_health.py
  - tests/tooling/test_metric_catalogue.py
  - docs/engineering_standards.md
  - .claude/task/contract.md

review_artifacts (separate artifact-only commit after; review.md records the reviewed diff's hash):
  - .claude/task/review.md
  - .claude/active_work.md

decisions_reserved:
  - Owner-approved (this session): subdirs over pytest markers; the taxonomy as `tests/README.md` + a §3
    pointer; `test_metric_catalogue` grouped under `tooling/` (contract check).
  - DEFERRED (optional, out of this clarity PR): 4 non-empty `expression_is_true` seed tests + explicit
    `not_null` on the 5 mart metric columns — coverage, not clarity; a future tiny PR if wanted.
  - Not migrated (verified non-issues): the `metric_catalogue` seed is already dbt-tested
    (`dbt_analytics/seeds/_seeds.yml`); `check_export_health.py` is a genuine pipeline gate (aggregate
    fill-rate / dedup / required-ticker), not a dbt test.

technical_definition:
  - `git mv` 16 files into `tests/{ingestion,frontend,tooling}/` (history preserved; git shows R renames).
  - New `tests/conftest.py`: puts repo root + `frontend/` + `scripts/` on `sys.path` once (the union each file
    inserted). Per-file `sys.path`/`ROOT`/`FRONTEND`/`SCRIPTS` boilerplate + now-unused `import sys`/`Path`
    stripped — EXCEPT `test_audit_mart_vs_yfinance.py` (keeps `import sys`, used by `sys.modules`) and
    `test_metric_catalogue.py` (uses `REPO`/`sys`/`Path` for file I/O → `parents[1]`→`parents[2]`; inline
    frontend insert dropped since conftest covers it).
  - `tests/README.md` + `engineering_standards.md §3` pointer: the domain→what→where→runner taxonomy.
  - CI (`python -m pytest tests/ -q`) unchanged — pytest auto-discovers subdirs. No `pytest.ini`/`conftest`
    existed before; no hardcoded `tests/` paths.

done_when:
  - 16 files moved + stripped; conftest added; README + §3 pointer added.
  - `pytest tests/ -q` → **80 passed** (proves imports resolve from the new tree). No dbt change → dbt
    build/gates untouched. `git log --follow` preserves history.
  - After the reviewed commit (artifact-only): record review.md, advance active_work.md; PR to main (NOT merged).

impact_map:
  - Behavior-preserving test reorg. No production code, no dbt models/seeds/marts, no `scripts/` changed → CI's
    dbt/pipeline gates and the app are unaffected; only pytest's layout changes (still discovered by
    `pytest tests/`).
  - Required reviewers (per `.claude/review_routing.json`): scope-auditor + cto-reviewer (`tests/*`). No
    `dbt_analytics/*.yml` / `docs/data_contract.md` / `ingestion/` / `scripts/` touched → no analytics-engineer
    / data-engineer / equity-analyst.

amendments:
  - 2026-07-07 — supersedes the merged metric-compute contract (#143). Scope = test-architecture cleanup
    (behavior-preserving reorg + conftest + taxonomy doc) per approved plan logical-roaming-brook.md.
