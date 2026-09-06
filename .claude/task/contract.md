# Task contract

objective: Add a dbt model contract on `mart_stock_cards` plus source freshness checks on all
  three raw yfinance tables. Fulfills an already-written, never-enacted standard
  (`docs/engineering_standards.md:223`: "Apply model contracts for stable `marts` outputs once
  schemas stabilise" -- zero use of `contract:`/`data_type:`/`freshness:` anywhere in
  `dbt_analytics/` today, confirmed by repo-wide grep).

  Note on numbering: earlier framing of this task called it "item 3 of the 5-item
  portfolio-readiness list." scope-auditor caught that this collides with `.claude/active_work.md`'s
  existing use of "item 3" for the already-merged MR !100, and that the source 5-item list text
  no longer exists anywhere in the repo (lost in an earlier archival/compaction pass, confirmed
  by repo-wide grep for "4-persona"/"5-item" -- zero hits). Dropped the number entirely rather
  than assert one that can't be verified; this contract and the handover both now describe the
  task by content only.

  The gap this closes: `scripts/export_to_supabase.py` selects via a hardcoded 79-column
  allowlist with no per-column validation -- a renamed column crashes it loudly, a type-changed
  column is invisible to it entirely. None of the three content gates
  (`check_pipeline_completeness.py`, `check_eligibility_baseline.py`, `check_export_health.py`)
  check schema shape, only row counts/fill rates. Postgres (via `supabase/migrations/`) is an
  implicit, late contract, but it's never exercised in the MR-gated `validate:full` job -- only
  in `data-pipeline` (schedule/manual only). `dbt build` runs before all three content gates
  and the export step, and runs on every MR -- a `contract: {enforced: true}` violation fails
  `dbt build` itself, catching schema-shape regressions in CI before they ever reach
  production.

  Full plan, including the dbt-source-code-level verification of contract requirements (traced
  directly against the installed dbt-core 1.11.11/dbt-duckdb 1.10.1, not assumed from general
  knowledge) and the schema-stability check done before proceeding, is in
  `C:\Users\Rami\.claude\plans\groovy-churning-scroll.md`, approved via `ExitPlanMode`. The plan
  originally scoped freshness to 2 of 3 sources; the amendments below record why and how that
  changed to all 3, after review.

  A load-bearing architecture fact found during planning, not assumed: this project's staging
  models never call `{{ source(...) }}` -- they read raw parquet through a custom
  `raw_parquet_union` macro. `sources.yml`'s three tables are pure documentation today with no
  real backing relation (confirmed: zero `source(` calls anywhere in `dbt_analytics/models/`).
  A bare `loaded_at_field` freshness config would fail at runtime with "relation does not
  exist" -- worked around with `loaded_at_query` (a first-class dbt config for exactly this
  case), which directly calls `{{ raw_parquet_union(filename) }}` itself (not a hand-rolled
  glob) so freshness inherits the exact same active-market scoping the rest of the project
  already uses, with no parallel implementation to drift out of sync.

scope_paths:
  - dbt_analytics/models/5_marts/_marts.yml (contract config + 80 data_type additions)
  - dbt_analytics/models/sources.yml (loaded_at_query + freshness for all 3 tables)
  - dbt_analytics/models/1_staging/yfinance/stg_yf__daily_prices.sql (pass through the new
    ingested_at column)
  - dbt_analytics/models/1_staging/yfinance/_yfinance_staging.yml (document it)
  - ingestion/yfinance/ingest.py (stamp ingested_at on daily-price rows, once per fetched batch)
  - scripts/seed_ci_raw_fixtures.py (stamp the same column on CI price fixtures, or
    validate:full's new freshness step would fail in a genuinely clean CI run)
  - .gitlab-ci.yml (dbt source freshness in both data-pipeline and validate:full)
  - docs/data_contract.md (contract-enforcement note + freshness-scope note)
  - .claude/active_work.md
  - .claude/task/contract.md
  - .claude/task/review.md

decisions_reserved: none outstanding now -- one entry below WAS a live decision put to the
  owner mid-task after scope-auditor caught it being mis-cited as already-settled (see
  amendments). Two remaining implementation-level choices, disclosed as agent-executable, not
  product content: (1) freshness thresholds (20-day warn / 30-day error, same for all three
  sources) are a technical default reasoned from the real schedule's worst-case gap (17 days in
  a long month), not a business/product number; (2) `ingested_at` on daily prices is stamped
  once per yfinance download batch (one API call), not once per row or once per market-run --
  matches the actual granularity of a "fetch event" and avoids re-stamping already-flushed rows
  on a later flush within the same run (a real bug avoided by stamping at batch-fetch time, not
  inside the already-existing `_normalize_price_frame`, which re-runs on every flush over all
  accumulated rows).

done_when:
  - `dbt_analytics/models/5_marts/_marts.yml`: `mart_stock_cards` gets a `config: {contract:
    {enforced: true}}` block; all 80 existing `columns:` entries get `data_type:` matching the
    real DuckDB types (confirmed via `DESCRIBE marts.mart_stock_cards` against an actual
    build). Existing tests (5 column-level, 4 model-level) untouched. No new `constraints:`
    blocks (would duplicate existing `not_null` test coverage in a different mechanism, out of
    scope for "add a model contract").
  - `dbt_analytics/models/sources.yml`: all three tables (`yf_constituents`, `yf_fundamentals`,
    `yf_daily_prices`) get `loaded_at_query` (calling `{{ raw_parquet_union(...) }}` directly,
    not a hand-rolled glob) and a `freshness: {warn_after: 20 days, error_after: 30 days}`
    block.
  - `ingestion/yfinance/ingest.py`: daily-price rows get a new `ingested_at` column, stamped
    once per fetch batch. `stg_yf__daily_prices.sql`/`_yfinance_staging.yml` pass it through
    and document it. `scripts/seed_ci_raw_fixtures.py`'s price fixtures get it too.
  - `.gitlab-ci.yml`: `dbt source freshness` added to `data-pipeline` (between `dbt deps` and
    `dbt build`, real staleness detection against real data) AND `validate:full` (between `dbt
    deps` and `dbt parse`, query-correctness verification against CI fixtures only -- fixture
    data is always fresh, so this can never test staleness detection, only that the query
    itself still parses and references real columns before a break would otherwise first
    surface at the live production schedule).
  - Contract mutation-tested: temporarily break one column's `data_type`, confirm `dbt build
    --select mart_stock_cards` fails with dbt's contract-mismatch error shape specifically
    (not a generic error), restore, confirm clean build again.
  - Freshness mutation-tested twice: (a) an absurd `error_after` reports ERROR STALE and exits
    non-zero (checked via file redirect, not a `| tail` pipe, which reports the pipe's own exit
    code); (b) a typo'd/renamed column in a `loaded_at_query` fails with a clear DuckDB Binder
    Error, against BOTH real data and CI fixture data, proving the new `validate:full` step
    would actually catch this class of break pre-merge, not just log something and pass.
  - Verified against a genuinely clean, all-fixture environment (storage/raw/ fully cleared and
    reseeded), not just a locally-contaminated one -- an earlier verification pass appeared to
    pass only because leftover real local data was masking a real gap in the fixture seeder.
  - Full real `data-pipeline`-equivalent sequence sanity-checked locally against real raw
    parquet, including the real, production-relevant mixed-schema case (one market fetched
    with the new ingested_at column, others still on the pre-change schema) -- confirms
    `raw_parquet_union`'s `union all by name` tolerates the column appearing on some markets
    and not others without erroring, which is exactly the transitional state production will be
    in immediately after this deploys.
  - `docs/data_contract.md`: contract-enforcement note near the existing `## Supabase export
    -- mart_stock_cards` section; freshness-scope note (now all three sources, why, and that
    validate:full's copy of the check is query-correctness-only) near the existing
    `## Freshness` section.
  - `.claude/active_work.md`: item closed out, without an unverifiable item number.
  - No em dash or en dash on any added line.

impact_map:
  - No user-visible change (dbt config + CI + docs + ingestion internals only, nothing in
    `frontend/`).
  - `dbt_analytics/models/5_marts/_marts.yml` and `sources.yml` -- per
    `.claude/review_routing.json` (`dbt_analytics/*.yml` -> analytics-engineer-reviewer),
    requires analytics-engineer-reviewer.
  - `ingestion/*` touched -- requires data-engineer-reviewer.
  - `.gitlab-ci.yml` touched -- requires cto-reviewer.
  - `docs/data_contract.md` touched -- requires equity-analyst-reviewer.
  - scope-auditor always.

amendments:
- cto-reviewer (round 1) found a real gap: the new `loaded_at_query` SQL was genuinely new
  executable logic with zero pre-merge verification anywhere -- not `validate:full`
  (deliberately excluded at the time), not sqlfluff (lints `.sql` files, not YAML-embedded
  query strings), not `dbt parse`/`dbt build` (freshness queries only execute under the
  dedicated freshness runner), not any pytest test. A future break (a typo, an ingestion-side
  column rename) would first surface at the live 1st/15th production schedule and abort the
  whole job before `dbt build`/export/assessments ever ran. Fixed by adding
  `dbt source freshness` to `validate:full` too, scoped explicitly as a query-correctness check
  (not a staleness-detection one, which fixtures can't meaningfully exercise). Mutation-tested
  against the exact scenario described: typo'd a column name, confirmed the new `validate:full`
  step fails immediately with a clear Binder Error and non-zero exit, restored, confirmed clean.
- analytics-engineer-reviewer (round 1, dispatched in parallel, independently found the same
  core gap -- convergent confirmation) also found a second, distinct issue: the original
  `loaded_at_query`s used a hand-rolled `*` glob (`{{ var("raw_path") }}/*/filename.parquet`),
  unscoped to `active_market_codes`, unlike `raw_parquet_union`'s explicit per-active-market
  loop -- a real, if latent, divergence (a deactivated market's frozen directory would silently
  join the freshness signal). Fixed by calling `{{ raw_parquet_union(filename) }}` directly
  inside `loaded_at_query` instead of re-deriving a parallel glob -- confirmed via the actual
  compiled SQL that this expands to the identical per-active-market UNION ALL the staging
  models already use, not a wildcard.
- scope-auditor (round 1) found two disclosure problems, both fixed by owning the reasoning
  honestly rather than borrowing authority that wasn't there:
  1. `decisions_reserved` cited MR !101 as an "already-documented decision" not to add a
     fetch-timestamp column to `yf_daily_prices`. Verified false: MR !101's own scope (an
     ingestion-side `.checkpoint` sidecar FILE for same-day refetch skipping) never touched
     `yf_daily_prices`'s schema or dbt source freshness, which didn't exist before this task --
     citing it misclassified a live decision as an already-settled one. Put to the owner
     directly instead: leave `yf_daily_prices` uncovered by freshness (a documented gap), or
     add an `ingested_at` column now to close it. Owner chose to add the column -- see the
     scope_paths/done_when expansion above; this is why freshness now covers all three sources,
     not two.
  2. This task's "item 3" label collided with an already-used number -- see the objective's
     "Note on numbering" above.

  Both rounds of fixes above were re-verified together, not independently: full local
  `data-pipeline`- and `validate:full`-equivalent sequences re-run end to end after all
  changes landed, against both real data and a freshly-cleared, genuinely clean fixture
  environment (see done_when). Narrow re-checks dispatched to all four reviewers against the
  fully updated diff -- see review.md.
- cto-reviewer (round 2) found a real gap in the round-1 fix itself: a fresh-today
  `.checkpoint`-marked parquet file can predate this task's own `ingested_at` column addition
  (e.g. a locally-run fetch from earlier the same day, before this code existed). Merging that
  file's rows with newly-fetched rows via `pd.concat` doesn't error on the mismatched columns --
  it silently outer-joins and NaN-fills the gap, and nothing (no dbt test, no freshness check,
  since `MAX()` ignores NULLs) would ever catch it. Fixed with a `PRICE_COLUMNS` constant (single
  source of truth for both `_normalize_price_frame`'s output and the new guard) and
  `_is_usable_checkpoint()`, which treats a same-day file with the wrong column set as NOT
  usable -- falling back to a full refetch, the same already-handled path as a stale checkpoint,
  instead of a mismatched-schema merge. Added a `not_null` test on
  `stg_yf__daily_prices.ingested_at` as defense-in-depth. Mutation-tested: reverted the guard,
  confirmed the new regression test fails with the exact NaN-fill symptom (a row that should have
  been excluded shows up in the combined frame), restored, confirmed clean.
- analytics-engineer-reviewer (round 2) found a second real gap, independent of cto-reviewer's:
  `ingested_at` has a non-obvious correctness property (stamped once per fetch batch, never
  recomputed on a later flush -- `_normalize_price_frame` reruns over ALL accumulated `frames` on
  every flush, so recomputing the stamp there would let a later batch's flush silently overwrite
  an earlier batch's already-flushed timestamp with its own, later one) that no test asserted.
  Existing multi-batch/multi-flush tests never inspected `ingested_at` at all. Fixed with a new
  regression test that fakes a monotonically-increasing clock across two batches and asserts
  each batch's rows keep their own batch's timestamp after the second batch's flush. Mutation-
  tested: moved the stamp into `_normalize_price_frame` (the exact regression described), confirmed
  the new test fails because both batches collapse to the identical, later timestamp, restored,
  confirmed clean.

  Both fixes re-verified together: full pytest (531 passed, up from 529), targeted and full
  `dbt build`/`dbt source freshness` against real local data (all pass, including the new
  `not_null` test against real data spanning a mixed old/new schema across markets) AND against a
  freshly-cleared, freshly-reseeded fixture-only environment (also all pass -- confirms the new
  `not_null` test is CI-safe under `validate:full`'s fixture data). sqlfluff and all four
  `check_*.py` gate scripts re-run clean. Em/en-dash scan re-run on the diff against HEAD
  (explicit UTF-8 file read, not stdin): 0 hits.

  Note on a stale reviewer notification: a `scope-auditor` task completion arrived mid-round-3-
  prep reporting the same two findings already resolved in round 1/round 2 above. Verified this
  was a delayed echo of the original round-1 dispatch, not a fresh check against current state --
  its cited line numbers for `decisions_reserved` (47-49) point at `scope_paths` entries in the
  current file, not `decisions_reserved`, which no longer starts near those lines after this
  round's amendments grew the file. No action taken; not a new finding.
- **Process miss, caught by the commit gate, not by me**: this contract's own `impact_map`
  correctly stated `ingestion/*` touched requires data-engineer-reviewer, but that reviewer was
  never actually dispatched across any round of this task -- the commit gate blocked the first
  commit attempt on exactly this. Dispatched as a full, cold, round-1 review (not a narrow
  re-check, since it was genuinely this reviewer's first look) once caught.

  data-engineer-reviewer (round 1) FAILED with two findings, both real, both verified
  empirically:
  1. `dbt source freshness`'s `loaded_at_query` takes `MAX()` over the union of ALL active
     markets, so the check passes as long as ANY one market has a recent timestamp -- a single
     market's ingestion silently breaking forever (a real, anticipated failure mode; the batch
     loop already has retry/rate-limit handling for partial failures) would never trip
     `error_after` as long as other markets keep refreshing. Confirmed by simulating a stuck
     market (dropped `ingested_at` from one real market's parquet, left the other 8 fresh) and
     observing `dbt source freshness` still PASS. `docs/data_contract.md` asserted "All three
     raw tables covered" with no caveat that this means table-level, not per-market.
  2. The new `not_null` test on `ingested_at` can fail against a local dev's pre-existing
     `storage/raw/` that predates this column, until re-ingested -- confirmed empirically
     (reproduced the exact `dbt build` failure, restored, confirmed clean). Confirmed
     NOT a CI or production risk: `validate:full`'s fixtures always stamp `ingested_at`
     unconditionally, and the scheduled `data-pipeline` job starts from an empty `storage/raw/`
     every run (docker executor, no cache/artifacts across jobs) -- this mixed-schema state can
     only arise in a local checkout that predates this change.

  Resolution: both are disclosure fixes, not new mechanisms -- added two paragraphs to
  `docs/data_contract.md`'s Freshness section (table-level-not-per-market caveat; a local-dev
  note on re-ingesting pre-existing `storage/raw/` before `dbt build`). Per-market freshness
  detection would be a new mechanism (e.g. a singular test grouped by `market_code`) -- flagged
  as a new open item in `.claude/active_work.md` rather than built here; owner's call whether
  it's worth it. Did not weaken the `not_null` test to `severity: warn` to route around the
  local-dev finding -- that would blunt the actual defense-in-depth it exists for in CI/production
  to avoid a one-time local inconvenience.

  Round 2 (re-check of the two disclosure fixes only) FAILED: the new open item 9's
  provenance note in `active_work.md` reintroduced the exact "item 3" label collision
  scope-auditor already caught and this task deliberately dropped everywhere else in this file
  -- ironic self-repeat of the earlier finding. Fixed by dropping the reference, describing the
  task by content instead, same pattern already used elsewhere in this file. Round 3 (narrow
  re-check of the one-line fix) PASSED.

  Separately: after adding the two `docs/data_contract.md` disclosure paragraphs above,
  recognized (before the commit gate had to, this time) that equity-analyst-reviewer's existing
  round-2 PASS on this same file's Freshness section predates those two new paragraphs --
  required per routing (`docs/data_contract.md` touched), not yet re-checked against the new
  content. Dispatched a narrow round 3; see review.md.
