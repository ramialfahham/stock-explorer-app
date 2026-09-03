# Review

diff_sha256: 890f4dae61e05ea7b804fad0a389cf961edd1f52a982ed4f94dd7979a8cc5c2b

Five reviewers required per `.claude/review_routing.json`: `scope-auditor` (always),
`cto-reviewer` (`scripts/*`, `tests/*`, `frontend/*`), `analytics-engineer-reviewer` (`*.sql`,
`dbt_analytics/*.yml`), `equity-analyst-reviewer` (`docs/data_contract.md`), and
`data-engineer-reviewer` (`supabase/*` -- initially missed since `*.sql` and `supabase/*` both
match the new migration file and route to two different reviewers; the commit gate caught the
gap and it was dispatched separately). All dispatched as cold, blinded `general-purpose`
subagents reading their role file verbatim, against the staged diff (hash
`5a41302a6c5c0d0623fd57748b39b75fe35e0a13d4b3f3aa4b387b4d494eed37`, before
`.claude/active_work.md`'s handover entry was added -- that file is `artifact_only` per the
routing config and adds no new reviewer requirement; the hash above is the final staged state).

## scope-auditor
VERDICT: PASS
risks_checked:
- Every changed/added file falls inside `scope_paths` exactly; `scripts/assessment_rules.py`
  and `dbt_analytics/seeds/metric_catalogue.csv` (verdict-computation surfaces the `impact_map`
  claims are untouched) confirmed zero diff by direct inspection, not by trusting the contract.
- All three `decisions_reserved` amendment defaults verified actually shipped, not silently
  upgraded to a real decision: words row still says "min"/"max" unchanged; the off-scale arrow
  has no tooltip/`title` attribute; the glyph is the mockup's `◂`/`▸` verbatim.
- `forward_pe` exclusion honored end-to-end: no `sector_q1_forward_pe`/`sector_q3_forward_pe` in
  the SQL, either YAML file, the migration, or `EXPORT_COLUMNS` -- confirmed by direct diff
  inspection plus an explicit negative-assertion test.
- No em/en-dash on any added line, scanned programmatically across the full staged diff.
- Migration `016_sector_benchmark_quartiles.sql` is the correct next sequential number and
  matches `012_sector_benchmark_min_max.sql`'s exact pattern.
- Ran the actual test/build commands rather than trusting the diff's own narration: `pytest`
  (105 relevant tests) and `dbt build --select int_stock__sector_benchmarks+` (22/22) both
  green on the staged code.
- Minor observation (not blocking): `.claude/active_work.md` wasn't yet updated with a handover
  entry at review time -- added afterward, see the note above about the hash.

## cto-reviewer
Two attempts. First attempt failed with a transient API 500 error (server-side, no findings
produced) -- relaunched against the identical staged diff.

VERDICT: PASS
risks_checked:
- Independently hand-recomputed all three `benchmark_range()` fence scenarios (no-op case,
  real-outlier clamp, outlier-as-self) against the code and the tests -- formula, clamp
  direction (`max(minimum, fence_low)` / `min(maximum, fence_high)`), and the off-scale
  boundary semantics (strict `<`/`>`) all correct, with no shared-bug risk between
  `position_pct`'s clamp and the `low_off_scale`/`high_off_scale` flags.
- Confirmed by inspection (not just test) that `_metric_cell_html()`'s value row is a completely
  separate, unchanged code path from `benchmark_range()` -- the raw value cannot be affected by
  this change, satisfying the contract's explicit "verify by inspection" requirement.
- CSS: `.ss-metric-range-track` has `position: relative`; no `overflow: hidden` ancestor in the
  range-mark subtree that would clip the new off-scale arrow; reuses the existing `--ss-muted`
  token rather than introducing a new color.
- Test coverage: all four contractually required `benchmark_range()` scenarios present with
  literal hand-computed numbers, not derived from the formula under test (the exact anti-pattern
  `docs/ui/card_metric_cell.md` warns against).
- Full suite green: 481 passed.

## analytics-engineer-reviewer
VERDICT: PASS
risks_checked:
- Ran `dbt build --select int_stock__sector_benchmarks mart_stock_cards` against the staged
  code -- all 3 unit tests and both extended expression tests passed. Independently verified
  the new `sector_benchmarks_computes_quartiles_with_real_spread` fixture's hand-computed values
  (Q1=13.5, Q3=20.5) actually match DuckDB's live `quantile_cont` output, not just asserted.
- Traced the extended `min <= q1 <= median <= q3 <= max` expression against the SQL's CASE
  gating -- all 5 aggregates per metric share the identical `sector_peer_count >= 8` gate, so
  the `coalesce()` fallback terms are dead code for reachable states but harmless.
- Layer placement matches `docs/layering.md`: the aggregation lives at `4_intermediate`,
  `mart_stock_cards.sql` does a pure passthrough, no grain change, no new `ref()`.
- Migration matches `012_sector_benchmark_min_max.sql`'s exact pattern; `forward_pe` confirmed
  excluded across the model, both YAML files, the mart, and the migration.
- No em/en-dash on any added line in the reviewed files.

## equity-analyst-reviewer
VERDICT: PASS
risks_checked:
- The Tukey-fence framing ("standard box-plot outlier-bound convention, not a value picked to
  fit any one card") is accurate and not overclaimed as a formal outlier hypothesis test.
- Confirmed the fence can only narrow, never widen, the displayed range beyond the raw sector
  min/max, matching the doc's "no-op for a sector with no real outlier" claim.
- Confirmed the pre-existing `sector_min_*`/`sector_max_*` columns remain literal, unclamped
  aggregates in dbt -- the clamp is frontend-only, computed at render time, never stored, so
  those existing doc rows did not need amendment.
- `forward_pe` exclusion confirmed across the SQL, migration, and doc's export-schema table.
- Peer-threshold gating for the new columns confirmed identical to the existing min/median/max
  gate -- no new invented threshold.

## data-engineer-reviewer
VERDICT: PASS
risks_checked:
- Sequencing dependency between `apply_supabase_migrations.py` and `export_to_supabase.py` (a
  PostgREST upsert would fail on unknown columns if the migration hadn't run first) -- checked
  `.gitlab-ci.yml`'s job ordering directly; migration always runs before export, the same
  established pattern migration `012` already relies on, not newly introduced.
- Production DDL safety/idempotency of `ADD COLUMN IF NOT EXISTS ... numeric` against a live
  `mart_stock_cards` table -- nullable, no default, metadata-only operation, no lock/rewrite
  concern; re-run safety additionally backed by the `schema_migrations` tracking table.
- Migration numbering correct (next sequential after `015_nl_ch_es_markets.sql`, no gaps or
  collisions); traced the full column-name chain (dbt model -> mart -> migration ->
  `EXPORT_COLUMNS`) and confirmed exact match at every hop, no mismatch.
