# Review

diff_sha256: 4e78767c3d81fe8598fccdf4bff3ad7fe5c9f8420eb686aa7c65c742bca8c424

_Test-architecture cleanup (behavior-preserving), branch `chore/test-architecture-cleanup`. Blinded reviewers
(cold, read-only, per `.claude/review_routing.json`): scope-auditor always; cto-reviewer for `tests/*`. No
`dbt_analytics`/`scripts`/`ingestion`/`data_contract.md` touched → no analytics-engineer / data-engineer /
equity-analyst. Both PASS on this diff, first round. Reorganizes 16 tests into domain subdirs + a centralized
conftest + a taxonomy doc; `pytest tests/` stays 80 passed._

## scope-auditor
VERDICT: PASS
risks_checked:
- Scope discipline: enumerated all 20 staged paths (rename-aware) — every file is `tests/{conftest,README,
  ingestion/,frontend/,tooling/}`, `docs/engineering_standards.md`, or `.claude/task/contract.md`. Zero files
  under `dbt_analytics/`, `scripts/`, `ingestion/`, `supabase/`, `.github/`, or `frontend/` source → CI's
  dbt/pipeline gates and the Streamlit app are provably untouched.
- Behavior-preservation: diffed each deleted original against its staged destination (not just the R-header);
  every removed line is `import sys`/`Path`/`ROOT`/`FRONTEND`/`SCRIPTS`/`sys.path.insert` boilerplate — no
  assertion/fixture/import-target edit. The two contract-named exceptions are real & correct
  (`test_audit_mart_vs_yfinance` keeps `import sys` for `sys.modules`; `test_metric_catalogue`
  `parents[1]→parents[2]` for the deeper path + drops the redundant frontend insert).
- Import-resolution soundness: conftest's `parents[1]` = repo root and inserts root + `frontend/` + `scripts/`
  (the union every per-file block previously inserted), so stripping cannot break imports; no
  `__init__.py`/`pytest.ini`/`pyproject` added → discovery semantics unchanged; no residual flat `tests/test_*.py`.
- Routing correctness: required set = scope-auditor (always) + cto-reviewer (`tests/*`); `engineering_standards.md`
  matches no path rule (adds no reviewer); absence of `*.sql`/`dbt_analytics/*.yml`/`data_contract.md`/`ingestion/`/
  `scripts/` correctly excludes the other three reviewers. Matches the contract's impact_map.
- No silent decision / doc-sync: the contract rewrite records supersession of #143 under recorded plan authority
  and logs the layout choices as already owner-approved; the taxonomy is written in-branch (README + §3 pointer),
  no stale doc left describing the old flat layout.

## cto-reviewer
VERDICT: PASS
risks_checked:
- conftest sys.path correctness & load order: `tests/conftest.py` is anchored at the test-tree root above every
  subdir, so pytest imports it before collecting any subdir module; it idempotently prepends repo root (for the
  `ingestion.yfinance.*` package — `__init__.py` confirmed), `frontend/`, and `scripts/`. Traced every moved
  file's imports (card_copy, card_ui, disclosure_html, explore_filters, live_quote, metric_school, nav_pages,
  markets, saved_news, supabase_cards, check_export_health, audit_mart_vs_yfinance, export_metric_definitions_json,
  ingestion.yfinance.balance_sheet/quarterly) — all exist at an added path.
- Retained-symbol correctness in the partially-stripped tooling tests: `test_metric_catalogue` keeps `sys`
  (`sys.executable`) and `Path` (real file paths + `Path(tmp)`), and its `REPO parents[1]→parents[2]` is
  arithmetically correct from `tests/tooling/` = repo root (seed CSV / export script / metrics.json / int-model
  paths + `subprocess(cwd=REPO)` stay valid); `test_audit_mart_vs_yfinance` keeps `import sys` (used by
  `sys.modules`) and safely drops `Path` (only in `__future__`-stringized annotations, never evaluated).
- Discovery / collision safety: all 16 are `R` renames, no leftover flat `.py` (only the intentional new
  `conftest.py` sits directly in `tests/`); no `pytest.ini`/`pyproject`/`setup.cfg`/`tox.ini`/prior conftest/
  testpaths existed → CI's unchanged `python -m pytest tests/ -q` still auto-discovers subdirs under PEP 420; 0
  `__init__.py` + 16 globally-unique basenames → default `prepend` import mode cannot hit an import-file-mismatch.
- Platform-surface blast radius: diff touches only `tests/**`, `tests/README.md`, `docs/engineering_standards.md`,
  and the contract — no requirements/lockfile, no workflow step, no secret/permission, no dbt model/seed/mart/
  script — so CI dbt & pipeline gates, cost/run-frequency, and guardrail config are untouched; path inserts are
  guarded (`if _path not in sys.path`) → re-run/interruption safe. "80 passed" is consistent with the trace.

## Non-blocking (optional follow-up, not defects here)
- Optional dbt hardening deferred (coverage, not clarity): 4 non-empty `expression_is_true` seed tests on the
  `metric_catalogue` text columns (closes the empty-string gap `not_null` misses); explicit `not_null` on
  `mart_stock_cards`' 5 metric columns (currently implicit via `is_card_eligible=true`). A tiny separate PR if wanted.
