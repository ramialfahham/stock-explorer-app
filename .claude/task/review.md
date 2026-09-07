# Review

diff_sha256: 551594b48ce08429cedbecbaf2879bbae25e8a4e5d99a31054a64b7fbb73728a

## scope-auditor
Round 1 FAILED (two findings, both disclosure-accuracy problems, not code defects)
- `decisions_reserved` cited MR !101 as an "already-documented decision" not to add a
  fetch-timestamp column to `yf_daily_prices`. Verified false: MR !101's own scope (an
  ingestion-side `.checkpoint` sidecar file for same-day refetch skipping) never touched
  `yf_daily_prices`'s schema or dbt source freshness, which didn't exist before this task --
  citing it misclassified a live decision as an already-settled one, self-classified by
  analogy rather than owned as this task's own call.
- This task's "item 3" label collided with `.claude/active_work.md`'s own existing use of
  "item 3" for the already-merged MR !100 (confirmed via `git show 411c45a0`). The source
  5-item portfolio-readiness list text no longer exists anywhere in the repo (repo-wide grep
  for "4-persona"/"5-item": zero hits) -- lost in an earlier compaction pass -- so the correct
  number for this task can't be reconstructed.

Everything else in round 1 held (scope_paths matched the staged diff, 80 data_type additions
counted and confirmed with no name/description drift, `mart_stock_eligibility_gaps` confirmed
untouched, impact_map's reviewer routing verified against the live routing file).

Resolution: put the `yf_daily_prices` question back to the owner directly (leave uncovered,
documented, vs. add an `ingested_at` column now) -- owner chose to add the column, closing the
gap fully rather than just fixing the disclosure wording (see the scope_paths/done_when
expansion in `contract.md`). Dropped the "item 3" label entirely rather than assert an
unverifiable number.

Round 2 (re-check against the fully updated diff -- both findings, plus everything the scope
expansion touched, nothing else in scope):
VERDICT: PASS
risks_checked:
- Finding 1 (MR !101 mis-citation) verified actually resolved, not reworded: every remaining
  `!101` reference narrates in explicit past tense that the citation was "verified false" and
  the `yf_daily_prices` question was put to the owner directly and answered. No line re-asserts
  !101 as covering this decision.
- Finding 2 (colliding "item 3") verified dropped, not reasserted: the only remaining "item 3"
  occurrence is `active_work.md`'s pre-existing, untouched MR !100 entry, plus new prose
  explicitly narrating that this task's own label was dropped because of the collision.
- `_marts.yml`: exactly 80 `data_type:` additions, all within `mart_stock_cards`, zero leakage
  into `mart_stock_eligibility_gaps` (0 data_type, 0 contract block there). No `constraints:`
  added; existing `data_tests:` untouched.
- Em/en dash scan re-run correctly (explicit UTF-8 file-open, not stdin): 0 hits across both
  `review_input.patch` and the true staged diff including `review.md` itself.
- `ingest.py`'s "stamped once per fetch batch" claim traced structurally: `fetch_time` sits
  inside the per-batch loop, and `_current_combined()` really does re-run
  `_normalize_price_frame` over all accumulated frames on every flush -- confirming the
  documented bug-avoidance is real, not just asserted.
- `docs/data_contract.md` and `.gitlab-ci.yml` placement claims verified against live line
  numbers, both match `done_when` exactly. `sources.yml`'s asymmetry (prices gets a new
  `ingested_at` column, fundamentals correctly falls back to pre-existing `snapshot_date`)
  confirmed consistent with what's disclosed.
- `impact_map`'s reviewer-routing claims cross-checked against the live routing file, all
  accurate; two immaterial gaps noted (not false statements, no reviewer actually skipped).

## analytics-engineer-reviewer
Round 1 FAILED (two findings)
- The `loaded_at_query` SQL (`sources.yml`) was genuinely new executable logic with zero
  pre-merge verification path anywhere -- not `validate:full` (deliberately excluded at the
  time), not sqlfluff (lints `.sql` files, not YAML-embedded query strings), not `dbt
  parse`/`dbt build` (freshness queries only execute under the dedicated freshness runner), not
  any pytest test. Independently convergent with cto-reviewer's finding below -- both reviewers
  found this in parallel, without seeing each other's work.
- The original `loaded_at_query`s used a hand-rolled `*` glob
  (`{{ var("raw_path") }}/*/filename.parquet`), unscoped to `active_market_codes` unlike
  `raw_parquet_union`'s explicit per-active-market loop -- confirmed via
  `docs/market_registry.yml`'s own schema comments that `ingest_active: false` is a real,
  supported, documented operation (pausing without deleting), and confirmed no cleanup
  mechanism exists for a paused market's `storage/raw/` directory. `MAX()` over the unscoped
  glob wouldn't cause a false PASS (a paused market's frozen file can never be the newest), but
  the freshness signal would silently shift from "are the markets we serve fresh" to "is any
  file anywhere matching this name fresh" -- latent, not triggered by today's registry (all 9
  markets currently active), but unguarded and undocumented as a divergence from the project's
  own established scoping pattern.

Also confirmed clean: dbt-core 1.11.11 + dbt-duckdb 1.10.1 fully support `contract: {enforced:
true}}`; independently ran `dbt build --select mart_stock_cards` and cross-checked
`DESCRIBE marts.mart_stock_cards` against all 80 declared types; confirmed no test/doc
convention in `docs/layering.md`/`docs/engineering_standards.md` expected more or less than
what was delivered for the untouched existing tests.

Resolution: `loaded_at_query` rewritten to call `{{ raw_parquet_union(filename) }}` directly
instead of re-deriving a parallel glob -- confirmed via the actual compiled SQL (the same
artifact the staging models compile to) that this expands to the identical per-active-market
UNION ALL, not a wildcard. The pre-merge-verification gap is the same one cto-reviewer found;
see that resolution below.

Round 2 (re-check against the diff after the owner's ingested_at decision and the round-1
fixes) FAILED (one finding, distinct from round 1):
- `ingested_at` has a non-obvious correctness property that nothing tested: it must be stamped
  once per fetch batch and never recomputed on a later flush, since `_normalize_price_frame`
  reruns over ALL of `frames` accumulated so far on every flush, not just the newest batch.
  Verified by trace that the code got this right, but `test_ingest_resume.py`'s existing
  multi-batch/multi-flush tests (`test_prices_no_duplicate_rows_when_batch_boundaries_shift`,
  `test_prices_skip_if_fresh_today`) never once inspected `ingested_at`. A regression moving the
  stamp into `_normalize_price_frame` (a natural-looking refactor) would be caught by nothing --
  not `dbt build` (schema/types unaffected), not `dbt source freshness` (values would look
  fresher, not staler -- `MAX()` would still find a recent-looking timestamp), not any other
  pytest test.
- Separately noted (not a defect): mid-review, unstaged changes were visible on top of the
  staged diff (the round-2 `PRICE_COLUMNS`/`_is_usable_checkpoint` fix, its regression test, and
  this file's own in-progress edits) -- flagged per the working agreement's rule that whatever
  ends up staged before commit must be re-checked against this review's diff, since it wasn't
  what was in the working tree. Correct and already the plan for round 3.

Resolution: added `test_prices_ingested_at_is_not_overwritten_by_a_later_batchs_flush` --
fakes a monotonically-increasing clock across two batches (2 tickers each) and asserts each
batch's rows keep their own batch's `ingested_at` after the second batch's flush completes.
Mutation-tested against the exact scenario described: moved the stamp into
`_normalize_price_frame`, confirmed the new test fails because both batches collapse to the
identical, later timestamp (`assert '...T12:07:00+00:00' < '...T12:07:00+00:00'`), restored,
confirmed clean (531 passed, up from 529).

Round 3 (narrow re-check of the round-2 fix only -- the new regression test and its fake-clock
mechanism; rest of the diff unchanged since earlier PASS/FAIL rounds, out of scope for this
pass):
VERDICT: PASS
risks_checked:
- Test genuinely proves the demanded property rather than passing for unrelated reasons --
  traced the exact `datetime.now()` call sequence against the fake clock's counter (accounting
  for `_atomic_write_parquet`'s own marker-timestamp write landing between the two batches'
  `fetch_time` calls) and confirmed the discriminating assertion (`stamps["AAA"] <
  stamps["CCC"]`) is the one that would fail under the regression, not the two same-batch
  equality checks (which hold vacuously either way).
- Independently mutation-tested (not just re-reading my account): reproduced the exact
  regression, watched the test fail with both timestamps collapsed to the identical final-flush
  value, reverted, confirmed byte-identical via MD5 hash (unchanged) and empty `diff`, `git diff
  --stat` unchanged from baseline, full file 13/13 pass again.
- Flakiness/vacuous-pass check: both batches unconditionally execute (no skip path reachable
  with a fresh tmp_path and an always-non-empty faked download); `call_with_retry`'s success
  path adds no hidden `datetime.now()`/sleep calls; no real wall-clock involved anywhere.
- One minor, explicitly non-blocking observation: the fake clock only implements `.now()`, so
  it would `AttributeError` if a code path ever reached `_is_fresh_today`'s
  `datetime.fromtimestamp(...)` call -- not reached in this test (no pre-existing checkpoint
  file), latent fragility for a hypothetical future edit only, not a defect in this test as
  written.

All four reviewers dispatched so far PASS against the diff as it stood at that point
(scope-auditor round 2, analytics-engineer-reviewer round 3, cto-reviewer round 3,
equity-analyst-reviewer round 2). See data-engineer-reviewer below: the commit gate then caught
that a fifth required reviewer had never been dispatched at all.

**Final state: all five required reviewers PASS against the current, fully-staged diff.**
scope-auditor round 2, analytics-engineer-reviewer round 3, cto-reviewer round 3,
data-engineer-reviewer round 3, equity-analyst-reviewer round 3 (the last two rounds each,
because docs/data_contract.md and active_work.md kept changing in response to later findings
-- each re-dispatched narrowly against only the new content once each reviewer's own required
path changed again).

## data-engineer-reviewer
Round 1 FAILED (two findings) -- dispatched only after the commit gate blocked the first commit
attempt, pointing out this task's own `impact_map` required data-engineer-reviewer
(`ingestion/*` touched) and it had never actually been run in any prior round. Genuine first
look at the full diff, not a narrow re-check.
- `dbt source freshness`'s `loaded_at_query` (`sources.yml`) takes `MAX()` over the union of
  ALL active markets (via `raw_parquet_union`), so the check passes as long as ANY one market
  has a recent timestamp. A single market's ingestion silently breaking forever -- a real,
  anticipated failure mode; the batch loop's own retry/rate-limit-warning code exists because
  partial failures happen -- would never trip `error_after` as long as other markets keep
  refreshing. Confirmed empirically: overwrote one real market's `yf_daily_prices.parquet` to
  simulate it stuck (dropped `ingested_at` entirely) while the other 8 markets stayed fresh,
  ran `dbt source freshness --select source:yfinance.yf_daily_prices` -- PASS. `MAX()`
  semantics make a non-NULL-but-90-days-old case (the more realistic failure) no different.
  `docs/data_contract.md` asserted "All three raw tables covered" with no caveat that this
  means table-level, not per-market -- overclaims what a reader would reasonably take it to
  mean, given this project's own market-partitioned architecture.
- The new `not_null` test on `stg_yf__daily_prices.ingested_at` can fail against a local dev's
  pre-existing `storage/raw/` that predates this column, until re-ingested. Confirmed
  empirically: overwrote one market's real parquet with itself minus `ingested_at` (the exact
  case `_is_usable_checkpoint` guards against on the ingestion side), ran `dbt build --select
  stg_yf__daily_prices` -- FAIL, non-zero exit, restored immediately (MD5-confirmed
  byte-identical), rebuild clean again. Traced why this is NOT a live-production risk: the CI
  runner uses the docker executor (container-isolated per job) and `data-pipeline` has no
  `cache:`/`artifacts:` on `storage/raw`, so every scheduled run starts from empty and
  populates every market uniformly with the new code in one pass -- this mixed-schema state
  cannot arise there. It IS immediately reachable in local development: anyone merging this
  branch and running `dbt build` against their own pre-existing local `storage/raw/` before
  re-running ingestion hits it. `validate:full` unaffected (fixtures always stamp
  `ingested_at`). Nothing in `ingest.py`, `docs/data_contract.md`, or `active_work.md` told a
  developer this step would be required post-merge.

Also confirmed clean, independently verified (not just re-reading prior reviewers' accounts):
`ingested_at` batch-stamping granularity is sound (traced `fetch_time` placement and flush
mechanics directly); `_is_usable_checkpoint` generalizes fine for future `PRICE_COLUMNS`
changes and doesn't warrant a bigger checkpoint-schema-versioning mechanism (would be a new,
currently-unneeded mechanism for a problem that hasn't recurred); freshness thresholds correct
against the real cron (`0 6 1,15 * *` UTC); `union all by name` mixed-schema safety confirmed
(own empirical test, matches ch_smi verification from earlier rounds) -- the crash/error-safety
is real, it's specifically the *tests'* behavior under that same mixed state that had gaps.

Resolution: both are disclosure fixes, not new mechanisms. Added a "Table-level, not
per-market" caveat and a "Local dev note" to `docs/data_contract.md`'s Freshness section.
Flagged per-market freshness detection as new open item 9 in `.claude/active_work.md` rather
than building it -- an owner-level scope call, not something to decide unilaterally. Did not
weaken the `not_null` test to `severity: warn` -- that would blunt its actual protective value
in CI/production to route around a one-time local inconvenience, matching the working
agreement's rule against weakening a safety check to unblock faster.

Round 2 (re-check of the two disclosure fixes only, nothing else in scope) FAILED (one finding,
on the open item, not the two doc paragraphs):
- `.claude/active_work.md`'s new open item 9 cited its own provenance as
  "found... while reviewing item 3" -- reintroducing the exact "item 3" label collision
  scope-auditor already caught and this task deliberately dropped everywhere else in this same
  file (see the "Not the number I first called this" note and `contract.md`'s "Note on
  numbering"). In this file "item 3" unambiguously means MR !100's already-merged
  capital-adequacy caveat, an unrelated task data-engineer-reviewer never reviewed --
  misattributed provenance in a handover file whose whole purpose is accurate orientation for a
  session with zero other context.

Also confirmed in this round: both new `docs/data_contract.md` paragraphs are disclosure-only,
not overclaiming a fix, verified directly against `sources.yml`/`raw_parquet_union.sql` (the
MAX()/union mechanism) and `.gitlab-ci.yml` (the no-cache/no-artifacts claim on `data-pipeline`,
default clean/clone semantics apply); `--force-refetch` and the plain-rerun path both confirmed
sufficient by reading `_is_fresh_today`/`_is_usable_checkpoint` directly; deferring per-market
detection to an open item (rather than building it) confirmed as an honest, non-evasive
close-out, consistent with working-agreement §6; nothing else in the diff moved since round 1
(cross-checked file mtimes).

Resolution: dropped the "item 3" reference, describing the task by content instead ("while
reviewing the dbt-contract-and-freshness task above") -- same fix pattern already used
elsewhere in this file for the identical collision.

Round 3 (re-check of the one-line fix only):
VERDICT: PASS
risks_checked:
- Provenance text verified verbatim against round 2's promised resolution ("while reviewing
  the dbt-contract-and-freshness task above") -- exact match, zero remaining "item 3"
  occurrences in the item 9 paragraph.
- Reference uniqueness/collision check: "the dbt-contract-and-freshness task above" matches
  exactly one task in the document (the pending MR positioned directly above item 9), and cites
  no item number, so it cannot collide with items 1-8's sequential numbering (verified
  unbroken, no duplicates/gaps).
- Full-diff scan for "item 3" confirms no stray collision anywhere else in the diff outside the
  legitimate MR !100 entry and review-history narrative describing the finding itself.
- Confirmed the other two hunks in `active_work.md`'s diff predate round 2, not new since it
  (one narrates round 1's own findings so necessarily written before round 2 ran; the other is
  the unrelated Sept 1-2 archival condensation, attributed to a 2026-09-03 pass, unconnected to
  this task).

## cto-reviewer
Round 1 FAILED (one finding)
- The `loaded_at_query` SQL had no pre-merge verification anywhere (see
  analytics-engineer-reviewer's identical, independently-found finding above for the full
  account). Confirmed empirically: `.gitlab-ci.yml` has zero `allow_failure`/`|| true` escape
  hatches, so a future break here would abort `data-pipeline` before `dbt build`/export/
  assessments ever ran, first surfacing at the actual production schedule -- a new CI-executed
  single point of failure shipped without durable coverage.

Also confirmed clean: `dbt deps` must precede `dbt source freshness` (reproduced directly by
temporarily removing `dbt_packages` -- exit 2 without it, exit 0 with it restored, confirming
the chosen placement is correct); `seed_ci_raw_fixtures.py` really does stamp fixture data with
`date.today()`/`datetime.now()` at CI run time (confirmed by reading the script), so the
original reasoning for excluding `validate:full` (no real staleness-detection value) held even
though the pre-merge-verification gap itself did not; full `pytest` suite run directly (529
passed); no secrets/scope issues; no em/en dash on any added line (scanned via explicit UTF-8
file-open, not stdin).

Resolution: added `dbt source freshness` to `validate:full`, between `dbt deps` and `dbt
parse`, with a comment explaining it's there for query-correctness verification specifically
(fixture data is always fresh, so it can never test staleness detection). Mutation-tested
against the exact scenario described: typo'd a column name in a `loaded_at_query`, confirmed
the new `validate:full` step fails immediately with a clear DuckDB Binder Error and non-zero
exit (against both real and CI fixture data), restored, confirmed clean.

Round 2 (re-check against the diff after the owner's ingested_at decision and the round-1
fixes) FAILED (one finding):
- A fresh-today `.checkpoint`-marked parquet file can predate this task's own `ingested_at`
  column addition -- e.g. a file written earlier the same day by a locally-run fetch, before
  this code existed. `_fetch_daily_prices`'s freshness path loads that file as `existing` and
  later concatenates newly-fetched rows (which DO have `ingested_at`) against it. `pd.concat`
  on mismatched columns doesn't error -- it outer-joins and silently NaN-fills the missing
  column on the old rows. Nothing catches this after the fact: not a dbt test (no test existed
  on `ingested_at` before this round), not `dbt source freshness` (`MAX()` ignores NULLs, so a
  partially-NULL column still reads as fresh from whatever real values exist). Confirmed via
  trace that this is a real, reachable path, not theoretical -- any same-day local re-run
  spanning this exact code change would hit it.

Also confirmed clean: the round-1 `validate:full` fix still behaves correctly after the
`raw_parquet_union` macro-reuse fix layered on top of it; no regression in the earlier mutation
coverage.

Resolution: added a `PRICE_COLUMNS` module-level constant (single source of truth for
`_normalize_price_frame`'s output column set) and `_is_usable_checkpoint(existing,
expected_columns)`, which returns `False` when a same-day file's columns don't exactly match
what a fresh fetch produces today. `_fetch_daily_prices` now checks this before trusting a
fresh-today file as `existing` -- a schema-mismatched file is treated the same as a stale one
(full refetch), never merged. Added `test_prices_ignores_a_fresh_today_file_with_an_old_schema`
and a `not_null` dbt test on `stg_yf__daily_prices.ingested_at` as defense-in-depth. Mutation-
tested: reverted the guard, confirmed the regression test fails with the old ticker surviving
in the combined frame (`assert 'ZZZ' not in ['ZZZ', 'AAA', 'BBB']`), restored, confirmed clean.
Verified the new `not_null` test against both real local data (which currently spans no schema
gap -- all 9 markets already carry `ingested_at`) and a freshly-cleared, freshly-reseeded
fixture-only environment (`validate:full`'s exact input) -- both pass 126/126, plus `dbt source
freshness` 3/3 in both environments.

Round 3 (narrow re-check of the round-2 fix only -- `_is_usable_checkpoint`, the new regression
test, the new not_null test; rest of the diff unchanged since earlier PASS/FAIL rounds, out of
scope for this pass):
VERDICT: PASS
risks_checked:
- Schema-mismatch detection completeness: `set(existing.columns) == set(expected_columns)`
  verified against all three real mismatch shapes (missing column, extra column, both) --
  all correctly fall back to full refetch. Column order is a non-issue since `pd.concat`
  aligns by label, not position.
- Regression test fidelity, independently mutation-tested (not just re-reading my account):
  bypassed the guard, confirmed the test fails with the exact predicted symptom, reverted,
  confirmed `git diff --stat` matched exactly (37/17), full 13-test file passes again.
- New-gap check on the fix itself: `set()` equality would collapse duplicate column labels in
  principle, but every real writer of `yf_daily_prices.parquet` (ingest.py's
  `_atomic_write_parquet`, `seed_ci_raw_fixtures.py`) builds its columns from a fixed
  unique-name list, so this is unreachable today. Non-blocking observation, not fixed:
  `sorted(list(...))  == sorted(...)` would be marginally tighter at zero cost -- left as-is
  rather than hardening against an unreachable case, consistent with this repo's
  no-unnecessary-complexity standard.
- CI safety of the not_null test independently re-confirmed by reading
  `seed_ci_raw_fixtures.py` directly: every price fixture row gets `ingested_at` stamped
  unconditionally.

## equity-analyst-reviewer
Round 1 PASS, against the ORIGINAL two-source freshness paragraph in `docs/data_contract.md`
(independently re-verified the 17-day worst-case-gap math, the "no auto-sync" claim about
`EXPORT_COLUMNS`, and the daily-prices timestamp-asymmetry claim -- all held). That paragraph's
content has since changed materially (now covers all three sources, not two, and adds a
sentence about `validate:full`'s query-correctness-only copy of the check) as a direct
consequence of the scope_paths expansion above -- this verdict no longer describes what's
actually staged.

Round 2 (re-check of the rewritten freshness paragraph specifically, nothing else in scope):
VERDICT: PASS
risks_checked:
- "All three raw tables covered" -- read sources.yml in full: all three carry both a
  `loaded_at_query` and a `freshness` block, none silently lacks it.
- "ingested_at on constituents and daily prices, snapshot_date on fundamentals" -- verified
  against the actual query SQL, not the prose gloss: exact column match, no drift.
- "daily prices... stamped once per yfinance download batch" -- checked against `ingest.py`:
  `fetch_time` is set once per batch-loop iteration and applied to every row of that batch, not
  recomputed inside the flush/normalize path. Literally true.
- "dbt source freshness... run in validate:full... against CI fixture data" -- confirmed
  present in both `validate:full` (between deps and parse) and `data-pipeline` (between deps
  and build), not silently added/omitted elsewhere.
- "fixture data is always fresh... can't test staleness detection" -- verified against
  `seed_ci_raw_fixtures.py`: every fixture stamps current time/date fresh each run, no
  mechanism to make it stale. Accurate, not overstated.
- Thresholds and the 17-day worst-case-gap claim re-confirmed unaltered and arithmetically
  correct; contract-enforcement paragraph and its 80 data_type/contract-enforced claims
  sanity-checked as not silently reverted since round 1.
- Style/register: same ASCII-dash convention, same technical vocabulary as the surrounding
  document -- no jargon spike, no beginner-facing claim implied or broken.

Round 3 (re-check of two more new paragraphs added after this PASS, in response to
data-engineer-reviewer's round-1 findings -- "Table-level, not per-market" and "Local dev
note"; caught proactively this time, not by the commit gate, since `docs/data_contract.md` is
in this reviewer's required path and had changed again since the round-2 PASS above):
VERDICT: PASS
risks_checked:
- "Table-level, not per-market" mechanism claim (`MAX()` over the union of active markets)
  verified against the actual `loaded_at_query` SQL and the `raw_parquet_union` macro's
  `active_market_codes` loop -- literally accurate, not an overclaim or a stale paraphrase.
- "Local dev note"'s "not a risk in CI or production" claim independently verified against
  `.gitlab-ci.yml` (no cache/artifacts on `storage/raw`) and `seed_ci_raw_fixtures.py` (every
  fixture row unconditionally stamps `ingested_at`) -- both premises hold.
- `--force-refetch`, the remediation instruction given to the reader, confirmed a real,
  existing flag (`ingestion/main.py`), not fabricated.
- Register/style: matches the bolded-label convention and technical density of the rest of the
  Freshness section; dbt vocabulary appropriate since this is the internal pipeline doc, not
  beginner-facing app copy. Zero em/en-dash in either paragraph.
- Cross-doc consistency: the "owner-level scope call" deferral matches `active_work.md` item
  9's framing verbatim in substance.

## Full suite
531 passed (up from 529 after round 2's two new regression tests). Re-run after every fix
round, including after the `ingested_at` column addition to `yf_daily_prices`, the
fixture-seeder fix, the schema-mismatch guard, and the batch-isolation test.

## Note on a stale reviewer notification
A `scope-auditor` task completion arrived during round-3 prep reporting the same two findings
already resolved above (the MR !101 mis-citation, the colliding "item 3" label). Verified this
was a delayed echo of the original round-1 dispatch, not a fresh check against current state:
its cited line numbers for `decisions_reserved` (47-49 in `contract.md`) point at `scope_paths`
entries in the file as it stands now, not `decisions_reserved` -- confirming it was checking an
earlier version of the file. No action taken; not a new finding.

## Mutation tests
- Contract: temporarily set `snapshot_date`'s `data_type` to `varchar`, confirmed `dbt build
  --select mart_stock_cards` fails with dbt's exact contract-mismatch error table (`definition_type:
  DATE`, `contract_type: VARCHAR`, reason "data type mismatch"), restored, confirmed clean
  build (13/13, then 125/125 full).
- Freshness threshold: set `error_after: {count: 0, period: hour}` on `yf_fundamentals`,
  confirmed `ERROR STALE` status AND a genuine non-zero process exit code (checked via file
  redirect, not a `| tail` pipe -- piping silently reports the pipe's own exit code, not
  dbt's), restored, confirmed PASS and exit 0. Repeated for `yf_daily_prices` after it gained
  freshness coverage -- same result.
- Freshness query correctness (the gap cto-reviewer/analytics-engineer-reviewer found):
  typo'd `ingested_at` to `ingested_at_TYPO` in a `loaded_at_query`, confirmed
  `dbt source freshness` fails with a clear Binder Error ("Referenced column... not found") and
  exit 1, against both real data and CI fixture data (the exact scenario the new `validate:full`
  step now guards). Restored, confirmed clean both times.
- Macro-reuse fix: re-ran the same query-typo mutation after switching from the hand-rolled
  glob to `{{ raw_parquet_union(...) }}` -- identical failure behavior, confirming the fix
  didn't regress the earlier mutation coverage.
- Schema-mismatch guard (cto-reviewer round 2): reverted `_is_usable_checkpoint`'s integration
  in `_fetch_daily_prices`, confirmed `test_prices_ignores_a_fresh_today_file_with_an_old_schema`
  fails with the old ticker surviving the merge (`assert 'ZZZ' not in ['ZZZ', 'AAA', 'BBB']`),
  restored, confirmed `git diff --stat` showed the exact intended diff back in place.
- Batch-isolation test (analytics-engineer-reviewer round 2): moved the `ingested_at` stamp
  from the batch loop into `_normalize_price_frame` (the exact regression the finding
  described), confirmed `test_prices_ingested_at_is_not_overwritten_by_a_later_batchs_flush`
  fails because both batches collapse to the identical, later timestamp, restored, confirmed
  the diff matched exactly (37 insertions, 17 deletions in `ingestion/yfinance/ingest.py`).

## Manual verification
Real `ch_smi` data: force-refetched to populate the new `ingested_at` column on daily prices,
while 8 other markets kept their pre-change parquet (missing the column) -- deliberately
constructed the real, production-relevant transitional scenario (some markets refreshed under
the new code, others not yet) rather than only testing a clean-slate case. Full `dbt build`:
125/125, confirming `raw_parquet_union`'s `union all by name` tolerates the column existing on
some markets and not others without erroring. `dbt source freshness`: 3/3 PASS, confirming
`MAX()` correctly finds the fresh real value from the one populated market despite the other
8 contributing NULL.

Separately caught and fixed by testing against a genuinely clean environment, not a locally-
contaminated one: an initial `validate:full`-equivalent freshness run appeared to pass, but was
actually masked by leftover real local data (from earlier manual verification) sitting
alongside CI fixtures. Fully cleared `storage/raw/` and reseeded fixtures from scratch, which
correctly exposed that `scripts/seed_ci_raw_fixtures.py` didn't stamp `ingested_at` on its own
price fixtures -- fixed, then reverified clean against the truly clean environment (all 3
sources PASS, full build 125/125).

sqlfluff, `check_layer_contract.py`, `check_dbt_sql_structure.py`, `check_registry_var_sync.py`,
`check_dbt_tests.py`, `dbt docs generate` + `check_dbt_documentation.py` all run locally and
passed clean after every round of changes, including round 2's schema-guard and not_null-test
fixes.

Round 2 fixes re-verified against real local data (`dbt build` 126/126, `dbt source freshness`
3/3 -- current real data already has `ingested_at` populated on all 9 markets, no schema gap
remains locally) AND, separately, against a freshly-cleared, freshly-reseeded fixture-only
environment matching `validate:full`'s exact input (`storage/raw/` moved aside, reseeded via
`scripts/seed_ci_raw_fixtures.py`, DuckDB file rebuilt from scratch -- `dbt build` 126/126,
`dbt source freshness` 3/3), then the real local data restored from the backup. Confirms the
new `not_null` test on `ingested_at` is safe under both real production data and CI's fixture
gate, not just one or the other.
