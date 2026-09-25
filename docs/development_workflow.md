# Development workflow -- Stock Explorer

> DURABLE. **Owns:** the branch, MR and CI flow, and the definition of done.
> **Never:** agent process -- that is `.claude/working-agreement.md`.

How to change this repo safely. Agent behavior: [`.claude/working-agreement.md`](../.claude/working-agreement.md) (UX PR gate: [`working_agreement.md`](working_agreement.md)).

---

## Branch and PR flow

1. `git checkout -b feature/short-description` from latest `main`
2. Implement; keep scope to the agreed task
3. Push and open an MR; wait for **validate** and review
4. Merge to `main`; scheduled pipeline picks up on next run
5. **Post-merge (agent):** `git fetch --prune`, `checkout main`, `pull`, delete merged local branches
   (`git branch -d` for each entry from `git branch --merged main` except `main`)

Never commit directly to `main`.

**One-time setup:** README "Getting started" (`python scripts/bootstrap.py`, proven by `--verify`). It installs the pre-commit hooks from [`.pre-commit-config.yaml`](../.pre-commit-config.yaml), including `no-commit-to-branch` and a staged gitleaks scan.

**GitLab (recommended):** branch protection on `main` — require MR, disallow direct push. Read
it back rather than assuming it's set: `glab api projects/<NAMESPACE>%2F<REPO>/protected_branches`
(a GitLab project can end up with an unprotected default branch -- see "trap 9" in
[`handover_2026-08-18.md`](handover_2026-08-18.md)).

---

## CI tiers

See [`.gitlab-ci.yml`](../.gitlab-ci.yml). The tier names are used across `docs/`.

### Tier A -- every pipeline except the schedule (`validate:full` job)

MR, push to `main` and web dispatch. No path rules: a docs-only MR runs the same steps as a
model change. In order:

1. `scripts/check_company_names_vs_yfinance.py`
2. `scripts/seed_ci_raw_fixtures.py` (synthetic raw parquet for every active market)
3. `dbt deps`, `dbt source freshness`, `dbt parse`, then `scripts/check_dbt_tests.py`
4. `sqlfluff lint dbt_analytics/models dbt_analytics/tests` (needs `profiles.yml`; CI copies
   `profiles.yml.example`)
5. `dbt build` (full, against the fixtures)
6. `scripts/check_eligibility_baseline.py` against `scripts/eligibility_baseline.ci.json`
7. `scripts/check_export_health.py` (fill rate 1.0, zero missing, `us_sp500:CI01` present)
8. `scripts/generate_assessments.py --dry-run`, then `scripts/check_eligibility_gaps.py`
9. `dbt docs generate`, then `scripts/check_dbt_documentation.py`
10. `pytest tests/ -q`
11. `scripts/audit_mart_vs_yfinance.py --offline --sample-size 5` (mart-side facts only, no fetch)

Beside it: `validate:pre-commit` runs the hooks in `.pre-commit-config.yaml` on all files except
gitleaks and `no-commit-to-branch` (the file checks from pre-commit-hooks, plus context budget,
narrative dates, em-dash, docs index, layer contract, dbt SQL structure, registry var sync), `validate:branch-guard` refuses an MR from `main`, and
`validate:secret-scan` runs gitleaks on the full history. `setup:clean-clone` is the one
path-triggered validate job: on MRs that change a setup file it runs `python scripts/bootstrap.py` twice
and `--verify` in a clean image.

### Tier C — production (`data-pipeline` job)

Scheduled full run:

1. Ingest all active markets
2. `dbt build` (full)
3. `check_pipeline_completeness.py` (fail if gates not met)
4. `export_to_supabase.py`

A GitLab pipeline schedule (CI/CD → Schedules — project configuration, not something a
commit can set) drives the scheduled run (1st and 15th of each month); a manual `web`
dispatch can trigger it on demand.

### dbt testing checklist (before PR)

1. Model-level `data_tests` on grain + business rules for the layer (see `engineering_standards.md` §3).
2. Unit tests for non-trivial intermediate logic (`unit_tests:` in layer YAML).
3. Singular tests in `dbt_analytics/tests/` for cross-model contracts (§1.1 SQL structure).
4. `python scripts/check_dbt_tests.py` — every model has coverage; ≥3 singular tests.
5. `dbt build` (or CI) — tests execute, not just declared.

**Tier C** (`check_pipeline_completeness.py`) runs only on scheduled/production pipeline; it does not replace dbt tests.

### Production pipeline verification

After CI/CD variables are configured on GitLab:

1. Manual `web` dispatch on **data-pipeline** (or wait for the 1st/15th 06:00 UTC schedule).
2. Confirm job steps: ingest → `dbt build` → completeness → export.
3. Optional local audit before activating a market: `python scripts/audit_yfinance_coverage.py`.

---

## Adding a market

See the **market activation checklist** in
[`data_contract.md`](data_contract.md#market-activation-checklist). It is the only copy.

A shorter list used to live here and had drifted into contradicting it: it said to start with
`ingest_active: false` (several steps read that flag and silently do nothing when it is unset),
it inverted two steps, and it said to "update Supabase `markets` row" inline rather than in a
numbered migration. That last one is not cosmetic. Nothing in the codebase upserts
`public.markets`, three tables foreign-key to it, and a missing row aborts the export for every
market on the next scheduled run with CI green throughout. France hit exactly that.

---

## Local setup

README "Getting started" is the only copy.

---

## Definition of done (features)

| Change type | Done when |
|-------------|-----------|
| Registry / market | Vars synced, seed exists, CI green |
| Ingestion | Raw parquet matches `data_contract.md` grain; no derived metrics in Python |
| dbt model | Layer folder correct, model + column descriptions (§2), model-level tests (§3), `check_dbt_tests.py`, `dbt build` + `check_dbt_documentation.py` pass |
| Export | Write path to Supabase documented (cards replace the snapshot in one transaction, assessments upsert); RLS unchanged for anon read |
| New market | Every step of the activation checklist done, including the `public.markets` migration. "Vars synced, seed exists, CI green" is NOT sufficient: that describes a market whose next production export fails on a foreign key |
| Docs | `north_star` / `data_contract` updated if behavior or schema changed |

Before pushing, run at least `python scripts/bootstrap.py --verify` (pytest, the pre-commit
hooks, sqlfluff, `dbt build` on fixtures), not `pytest` alone: a lint violation reaching CI is a
wasted round trip. The rest of Tier A when the change touches dbt or export.

---

## Ingestion skills

`.claude/skills/onboard-market/` covers adding or activating a market. It points at the
activation checklist in [`data_contract.md`](data_contract.md) rather than restating it, and
carries the traps that are recorded in no other document.

Still uncovered, and worth a skill when ingestion work resumes: the raw-only rule and parquet
paths.
