# Task contract

objective: **Dev-schema isolation for Supabase writes.** There is currently no safe place to test a
  migration or export change against a real Postgres database before it ships — the one Supabase
  project *is* production. Adds a `--target {prod,dev}` flag (default `prod`, unchanged behavior) to
  the two scripts that write to Supabase, so `dev` writes to a `dev` schema inside the *same*
  Supabase project — same URL, same credentials, no new CI/CD variables, no new project. Modeled on
  `football-data-pipeline`'s prod/ci/dev warehouse-target isolation (2026-07-08), adapted to this
  repo's actual architecture (ephemeral DuckDB + one Supabase project, not a shared warehouse dbt
  writes into directly). Approved plan: ~/.claude/plans/pure-juggling-frost.md. Stacked on the
  still-open GitLab-migration branch (`chore/migrate-to-gitlab`) because `.gitlab-ci.yml` doesn't
  exist on `main` yet and this task's CI job is a hard dependency of it.

scope_paths:
  - scripts/apply_supabase_migrations.py           # + --target flag, schema-qualified SQL substitution
  - scripts/export_to_supabase.py                  # + --target flag, ClientOptions(schema=...)
  - .gitlab-ci.yml                                 # + dev-schema-check job (web-manual-only, never automatic)
  - docs/supabase_setup.md                         # + "Testing against a dev schema" section
  - docs/operations_guide.md                       # + one-line pointer
  - tests/tooling/test_apply_supabase_migrations.py  # NEW: substitution + schema-selection unit tests
  - tests/tooling/test_export_to_supabase.py         # NEW: ClientOptions(schema=...) unit tests
  - .claude/task/contract.md

decisions_reserved (owner-approved this session; §6 — plan-approved):
  - **Scope excludes `scripts/generate_assessments.py`** — it writes to Supabase the same way but has
    uncommitted changes in flight on the parked `feat/ai-assessment-slice5b` branch. Deliberately left
    untouched; extend to it later once that work merges.
  - **A manual CI job is in scope**, not just a local CLI flag — reachable only via a deliberate `web`
    dispatch, same guarded shape as `supabase-migrate` / `data-pipeline`, never automatic.
  - **No formal multi-agent blinded-review cycle** for this change (consistent with how the GitLab
    migration itself was handled) — careful self-verification instead, called out explicitly.
  - **Branched off `chore/migrate-to-gitlab`, not `main`** — `.gitlab-ci.yml` is a hard dependency
    (working-agreement §3: "if the work is a hard dependency of an open PR ... commit to that branch
    instead"). This MR should target `chore/migrate-to-gitlab`, not `main`, until that one merges.

technical_definition:
  - **apply_supabase_migrations.py:** `schema = "public" if target == "prod" else target`.
    `MIGRATION_TABLE` becomes a value computed from `schema` (was a module constant), threaded through
    `_ensure_migration_table` / `_applied_migrations` / `_apply_file` / `_bootstrap_manual_initial_schema`;
    `_table_exists` takes `schema` as a parameter. Non-prod targets get `CREATE SCHEMA IF NOT EXISTS
    {schema};` then each migration file's SQL is regex-substituted (`\bpublic\.` → `{schema}.`) before
    executing — reuses the existing 10 migration files verbatim, no new SQL file. `target=prod` (default)
    stays byte-identical: no substitution. Does NOT touch `resolve_database_url`,
    `_fetch_pooler_host_port`, `_project_ref_from_supabase_url`, `_strip_env` — imported directly by
    `scripts/print_supabase_pooler_config.py`, which has no test coverage of its own.
  - **export_to_supabase.py:** same `--target` flag; `create_client(url, key,
    options=ClientOptions(schema=schema))`, always passed explicitly (`schema="public"` matches
    supabase-py's own default, so prod is unchanged). Prints which schema was written to. PostgREST only
    serves schemas in the Supabase project's exposed-schemas API setting — `dev` needs that added once,
    manually; migrations are unaffected (raw psycopg2, not PostgREST).
  - **.gitlab-ci.yml:** new `dev-schema-check` job, `stage: production`, rules `if: web, when: manual`
    then `when: never` (never reachable on MR/push/schedule). Reuses `validate:full`'s fixture-seed +
    dbt-build setup, then runs both scripts with `--target dev`. No new CI/CD variables. No changes
    needed to `tests/tooling/test_ci_reachability.py` — its existing `EXPENSIVE_COMMAND` regex and
    per-stage checks pick the new job up automatically.

done_when:
  - `pytest tests/tooling/test_apply_supabase_migrations.py tests/tooling/test_export_to_supabase.py -q`
    green: `target=dev` substitutes correctly and creates the schema; `target=prod` leaves SQL/client
    options untouched.
  - Full suite green: `pytest tests/ -q`.
  - `validate:full` still passes on GitLab (proven pipeline path, unchanged by this task).
  - `dev-schema-check` triggers correctly via manual web dispatch — the migrations half succeeds with
    zero manual Supabase steps; the export half either succeeds or fails with the documented, expected
    PostgREST exposed-schema error, not something silent.
  - `docs/supabase_setup.md` / `operations_guide.md` accurate; no new CI/CD variables; no new dependency.

impact_map:
  - New `--target` flag on two existing scripts, default-safe (prod unchanged). New manual-only CI job,
    same trust category as the existing prod-writer jobs. No dbt / mart / frontend / migration-file
    change (the 10 existing migration files are reused verbatim via runtime substitution, not edited).
    `scripts/generate_assessments.py` explicitly out of scope this pass.

amendments: (none yet)
