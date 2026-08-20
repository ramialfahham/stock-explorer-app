# Task contract

objective: **Fix two real bugs discovered while recovering the Supabase database export
  path** (owner lost access to the old Supabase project via a cascading GitHub-suspension
  lockout; migrated to a fresh Supabase account/project this session). Both bugs block
  `scripts/export_to_supabase.py` from working at all against a fresh project.

scope_paths:
  - scripts/export_to_supabase.py           # ClientOptions -> SyncClientOptions fix
  - supabase/migrations/011_grant_roles.sql # new: explicit role grants
  - docs/supabase_setup.md                  # doc-sync: RLS-bypass claim, new toggle step, migrations table
  - docs/operations_guide.md                # doc-sync: same RLS-bypass claim, round 2
  - tests/tooling/test_export_to_supabase.py # round 2: regression test for the ClientOptions bug
  - .claude/active_work.md                  # handover: this session's full account-recovery story
  - .claude/task/contract.md

decisions_reserved (owner-approved this session, in conversation):
  - **Fresh Supabase project** (owner-created, email/password login, no GitHub OAuth
    dependency) replacing the old GitHub-OAuth-locked one — owner's own decision, executed
    live in this session (project creation, `render.yaml`'s `SUPABASE_URL`/`SUPABASE_ANON_KEY`
    env vars updated in Render's dashboard by the owner).
  - **"Automatically expose new tables" disabled at project creation** (owner's choice,
    following Supabase's own recommendation for deliberate access control) — this is the
    direct root cause of the missing grants this migration fixes; recorded here since it's
    the reason 011_grant_roles.sql exists at all, not an arbitrary new grants migration.
  - Both fixes were verified end-to-end against the live fresh project (schema migrated,
    40-tickers-per-market sample ingested, exported, confirmed rendering on the live Render
    deploy) before being written up as this contract — not applied blind.

technical_definition:
  - **`scripts/export_to_supabase.py`**: `from supabase.lib.client_options import
    ClientOptions` → `SyncClientOptions`, and the one call site
    (`ClientOptions(schema=schema)` → `SyncClientOptions(schema=schema)`). Root cause: a
    confirmed upstream `supabase-py==2.30.0` regression (tracked at
    github.com/supabase/supabase-py/issues/1306) — `Client.create()`'s sync path
    internally accesses `client_options.storage`, which the generic `ClientOptions`
    dataclass doesn't define (only `SyncClientOptions`/`AsyncClientOptions` do). Confirmed
    the frontend's own `get_anon_client()` (`frontend/supabase_client.py`) is NOT affected
    — it calls `create_client(url, key)` with no explicit `options=`, which takes a
    different internal path that doesn't hit this bug. Only this one call site needed
    the fix (grepped the whole repo for `ClientOptions` usage — confirmed no other hits).
  - **`supabase/migrations/011_grant_roles.sql`**: every prior migration (001, 002, 010)
    assumed `service_role` gets its table privileges implicitly ("service role bypasses
    RLS by default" — see 001's closing comment), which held true under Supabase's default
    project template (the now-disabled "automatically expose new tables" setting), but is
    NOT the case on a project created with that setting off. RLS policies restrict which
    *rows* a role can touch; the underlying table-level `GRANT` is a separate requirement
    Postgres always enforces regardless of RLS. Grants added exactly match each table's
    existing RLS policy scope — no broader access than what's already declared readable/
    writable in 001/002/010: `SELECT` for `anon`/`authenticated` on `markets`,
    `mart_stock_cards`, `card_assessments`; `SELECT, INSERT` for `authenticated` on
    `user_interactions`; `SELECT, INSERT, UPDATE` for `service_role` on `mart_stock_cards`
    (written by `export_to_supabase.py`) and `card_assessments` (upserted by
    `generate_assessments.py`), plus `SELECT` on `markets`/`user_interactions` for
    `scripts/check_supabase_connection.py` (the documented setup-verify step, which
    prefers `SUPABASE_SERVICE_ROLE_KEY` when set; its `REQUIRED_TABLES` reads exactly
    `markets`, `mart_stock_cards`, `user_interactions` — three tables, not `card_assessments`
    too) — added in round 1 of review after data-engineer-reviewer found the original grant
    set missed this real, documented consumer. (Round 2's analytics-engineer-reviewer and
    cto-reviewer both independently caught an earlier draft of this contract overstating
    this as "all four tables" — corrected here.)
  - **`docs/supabase_setup.md`**: added a step-1 note on the "automatically expose new
    tables" toggle and its consequence; corrected two places that stated "service role
    bypasses RLS" without qualifying that RLS bypass doesn't substitute for the underlying
    table `GRANT` — added in round 1 after scope-auditor found the doc still taught the
    exact assumption this diff proves wrong.
  - **`.claude/active_work.md`**: full session narrative (Supabase account lockout,
    recovery via a fresh project, both bugs found/fixed, Render deploy confirmed live) —
    added in round 1 after scope-auditor found the handover was stale for this session's
    actual events, and that the contract had cited it for a claim it didn't support.
  - **`docs/operations_guide.md`**: same RLS-bypass qualification as `supabase_setup.md` —
    added round 2 after scope-auditor found this sibling doc restated the identical
    disproven claim, outside `scope_paths` at the time.
  - **`docs/supabase_setup.md`**: "Migrations on disk" table extended with `007`-`011` (was
    stopped at `006`) — added round 2 after scope-auditor found `011`, the very file this
    diff creates, missing from the table in a file this diff was already editing.
  - **`tests/tooling/test_export_to_supabase.py`**: new
    `test_options_passed_to_create_client_is_the_sync_variant` — added round 2 after
    scope-auditor found the `ClientOptions`→`SyncClientOptions` fix had zero regression
    coverage (existing tests mock `create_client` and assert only `.schema`, which both
    classes define — only `.storage` distinguishes them). Verified the new test actually
    catches the regression: temporarily reverted the import, confirmed this one test fails
    while the other three still pass, then restored the fix.

explicitly_not_in_scope:
  - Any other Supabase-account-recovery work (contacting support about the old account,
    etc.) — separate, owner-only track, not a code change.
  - Running the full-scale (all-tickers) ingestion — a separate, currently in-progress
    background operation, not part of this diff.
  - `scripts/generate_assessments.py` — not run this session (deliberately skipped, real
    Anthropic API cost); its `create_client(url, key)` call was checked and confirmed NOT
    to hit the `ClientOptions` bug (no explicit `options=` passed), so no fix needed there.

done_when:
  - `scripts/export_to_supabase.py` runs cleanly against a project with "automatically
    expose new tables" disabled (already verified live this session — 188 rows exported
    successfully after both fixes).
  - `011_grant_roles.sql` is idempotent and safe to apply via
    `scripts/apply_supabase_migrations.py`'s existing discovery/apply mechanism (already
    verified — applied cleanly this session).
  - `tests/tooling/test_export_to_supabase.py` has a regression test for the
    `ClientOptions`→`SyncClientOptions` fix, verified to actually fail on the reverted code.
  - scope-auditor (always) + cto-reviewer (`scripts/*`) + data-engineer-reviewer
    (`supabase/*`) + analytics-engineer-reviewer (bare `*.sql` pattern in
    `.claude/review_routing.json`, matches across `/` per fnmatch — confirmed in round 1
    review this genuinely routes here despite its charter being dbt-shaped, not a raw-
    Postgres-grants shape; see amendments) all PASS on the final staged diff.

impact_map:
  - **Data-layer change**: new migration file grants table-level privileges — no schema
    shape change (no new/altered columns), no RLS policy change, matches existing policy
    scope exactly (see technical_definition). Required reviewers (per
    `.claude/review_routing.json`, corrected in round 1 — see amendments): **scope-auditor**
    (always) · **cto-reviewer** (`scripts/*`) · **data-engineer-reviewer** (`supabase/*`) ·
    **analytics-engineer-reviewer** (bare `*.sql` pattern). Equity-analyst-reviewer does not
    route (no `metric_catalogue.csv`, no `data_contract.md`/`metric_layer.md` touched).
  - This is a genuine production bug fix, not new functionality: the `service_role` grant
    gap would have blocked the *existing* `data-pipeline`/`supabase-migrate` CI jobs the
    moment their CI/CD variables were ever configured — checked GitLab Settings → CI/CD →
    Variables directly this session and confirmed **none were ever set at all** for the old
    project, so this defect was already latent on `main` regardless of the owner's
    project-recovery work, just never triggered because the credentials to trigger it were
    never wired up.

amendments:
  - **Round 1 review (scope-auditor FAIL, cto-reviewer ESCALATE, data-engineer-reviewer
    FAIL) — all three findings addressed:**
    1. data-engineer-reviewer: `011_grant_roles.sql` under-granted `service_role` — missed
       `scripts/check_supabase_connection.py`'s real, documented use of the service-role key
       against `markets`/`user_interactions`. Fixed: added `SELECT` grants for both,
       verified live (`check_supabase_connection.py` now runs clean against the real
       project — its own `REQUIRED_TABLES` (`markets`, `mart_stock_cards`,
       `user_interactions`) all report ok).
    2. scope-auditor: `docs/supabase_setup.md` restated "service role bypasses RLS" without
       the grants caveat this diff proves wrong, and never mentioned the "automatically
       expose new tables" toggle at all. Fixed: doc updated (see technical_definition),
       added to `scope_paths`.
    3. scope-auditor: contract cited `.claude/active_work.md` for a claim ("CI/CD variables
       confirmed never set") that file didn't actually support, and the handover itself was
       stale for this session's real events. Independently re-verified the CI/CD-variables
       claim directly against GitLab (Settings → CI/CD → Variables — none present), then
       fixed: added `.claude/active_work.md` to `scope_paths`, wrote the full session
       narrative there, corrected the citation above to point at the direct verification
       rather than a doc that never said it.
    4. cto-reviewer (independently, same underlying fact as scope-auditor's routing point):
       the diff's own `done_when`/`impact_map` incorrectly excluded analytics-engineer-
       reviewer, reasoning "no `*.sql` under `dbt_analytics/`" — a qualifier the actual
       `*.sql` pattern in `.claude/review_routing.json` doesn't have (fnmatch, matches
       across `/`, confirmed mechanically by both reviewers independently). Escalated to
       the owner as instructed (two options: run analytics-engineer-reviewer for this diff
       as the literal rule requires, or treat it as a separate pre-existing routing-config
       scoping bug to fix on its own). **Owner decision: run analytics-engineer-reviewer now
       for this diff, per the literal rule** — the routing pattern itself is not touched by
       this task; a possible future fix to scope `*.sql` to `dbt_analytics/*.sql` is a
       separate, deliberate change to `.claude/review_routing.json` (a guard file, its own
       cto-reviewer-approved diff), not folded in here.
