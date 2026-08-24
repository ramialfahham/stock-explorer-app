# Review

diff_sha256: 7b18e60ec33d02c05cb66ca402f1032e0b80d7d3dd4bcc8e0e12dfaf6b339fde

Covers the full cumulative diff for `feat/metric-cell-groups-and-range-redesign`
(24 files vs. `main`; matches `.claude/task/contract.md`'s `scope_paths` exactly).
This review cycle ran 7 rounds — the round-by-round finding/fix history is recorded
in full in `contract.md`'s `amendments` section, not repeated here. Each section
below is that reviewer's most recent verdict against a diff whose scope has not
changed in that reviewer's specific domain since.

## scope-auditor

VERDICT: PASS
risks_checked:
- Full file-list match: all 24 diffed files map 1:1 to `scope_paths`, verified both
  directions (nothing extra, nothing missing) against the actual `git diff --staged`
  output, not just the contract's own claim.
- Catalogue structural-column integrity: independently column-diffed all 16 rows of
  `dbt_analytics/seeds/metric_catalogue.csv` against the pre-task base state —
  `numerator_expr`/`denominator_expr`/`base_relation`/`format`/`direction`/
  `perspective`/`benchmarkable`/`applies_to`/`importance_tier`/`display_order`/
  `basis_column` byte-identical on every row; only the prose columns
  (`description`/`interpretation`/`applicability`/`gloss`/`analogy`/`learn`/
  `calculation`) changed, matching the writing-voice-pass claim exactly. Em-dash
  count 46 → 0, confirmed by direct character count.
- `dbt_analytics/models/4_intermediate/_intermediate.yml`'s corrected model
  description ("Swipe-card metrics and per-company-type eligibility per ticker
  snapshot") verified to grammatically attach the per-type qualifier to
  "eligibility" only, matching `int_stock__card_metrics.sql`'s actual CTE split.
- Repo-wide "five metrics"/"hero" staleness sweep (multiple phrasings, all tracked
  files): every remaining hit resolves to an already-verified, correctly-scoped
  instance (operating-type eligibility gate references stated alongside their
  financial/pre_revenue siblings; the 5-benchmarked-metrics references in
  `data_contract.md`'s sector-column table and `card_metric_cell.md`; the archival
  `product_roadmap_2026-06.md` status log and `handover_2026-08-18.md`; the scoped
  `ux_principles_finanz_lern_apps.md` playground-porting note; a test-file code
  comment naming a data concept, `importance_tier`, that still exists). Nothing new
  introduced by this round's own edits.
- Owner-authorization completeness: `decisions_reserved` cross-checked against every
  user-visible/permanent change actually in the diff, including the 2 self-found
  `overflow_menu.py` strings that initially shipped without the same prior review as
  their 3 siblings — flagged by this reviewer round 6, resolved by presenting the
  same before/after table directly to the owner and recording their explicit "yes,
  go ahead" before finalizing (not just documenting after the fact).
- (This review file itself was the reviewer's one substantive round-7 finding —
  stale, still pointing at the prior, already-merged MR #22 branch's closing record.
  Resolved by this rewrite; not restated as an open finding since the fix is this
  file's own correction, not a pending action.)

## cto-reviewer

VERDICT: PASS
risks_checked:
- `.ss-metric-group-heading`/`.ss-metric-analogy`'s CSS-specificity fixes (Streamlit's
  emotion-cache `<hash> p { margin-top: 0; font-size: inherit; ... }` silently beating
  a bare single-class selector): verified selector specificity (0,2,0) vs (0,1,1) math
  directly, and confirmed the HTML actually renders the claimed ancestor nesting for
  both card-face and learn-panel contexts — not a hypothetical fix.
- `debt_to_equity`'s negative-equity value-aware branch: traced both new end-to-end
  tests against the real `build_card_html()`/`build_learn_panel_body_html()` functions
  (no mocking), confirmed doubly-robust assertions (specific text present + default
  text absent), ran them directly.
- `.ss-metric-range-number`'s `max-width: 5rem; overflow: hidden; text-overflow:
  ellipsis` overflow-protection fix: verified the ellipsis mechanism is unconditional
  (not just tuned to today's data), and correctly distinguished it from the
  `<span>`-based `.ss-metric-range-number`/`-word` elements, which are structurally
  immune to the Streamlit `<p>`-margin bug (confirmed via their actual HTML source).
- All 5 new/changed `frontend/overflow_menu.py`/`brand.py`/`landing.py` user-facing
  strings traced to their real render call sites; confirmed none introduces a new
  claim beyond dropping a stale metric count.
- `test_menu_metrics_line_has_no_stale_metric_count()`: confirmed it imports the real
  production constant (not a duplicate), pins the exact current string, and would
  fail against the documented pre-task value (hand-verified by substitution) as well
  as against a hypothetical future regression with a different hardcoded count.
- `frontend/metrics.json` vs `dbt_analytics/seeds/metric_catalogue.csv`: cross-checked
  every changed field by hand across both the round-3 voice pass and the round-4/5
  follow-up fixes; every structural column unchanged, every prose-column edit
  propagated correctly.
- Full test suite run directly where shell access was available: 206-207 passed
  (207 after the `MENU_METRICS_LINE` regression test was added), 0 failed, across
  every round this reviewer was dispatched.

## analytics-engineer-reviewer

VERDICT: PASS
risks_checked:
- Catalogue seed structural integrity: independently re-parsed
  `dbt_analytics/seeds/metric_catalogue.csv` with `csv.DictReader` at every dispatch
  (rounds 2, 3, 4, 6, 7) — 16/16 rows, correct column count, well-formed
  `direction`/`applies_to`/`importance_tier` enums throughout, including immediately
  after both in-task CSV corruption incidents (caught, in both cases, by this
  project's own `applies_to`-enum test before this reviewer's own pass even ran).
- `frontend/metrics.json` regeneration: ran the real
  `scripts/export_metric_definitions_json.py` against the current seed and
  byte-diffed against the committed file at every dispatch — identical every time,
  confirming it is mechanically regenerated, never hand-edited.
- The `csv.DictReader`/`DictWriter` programmatic round-trip (used for the round-3
  writing-voice pass, touching 14-15 of 16 rows) verified structurally safe against
  the round-2 raw-text-edit corruption class, and its CRLF working-tree side effect
  independently verified inert at the byte level (`core.autocrlf=true` normalizes to
  LF on `git add`; staged blob confirmed identical to `HEAD`'s convention).
- `dbt_analytics/models/4_intermediate/_intermediate.yml`'s model description fix
  ("Swipe-card metrics and per-company-type eligibility per ticker snapshot")
  verified grammatically unambiguous and factually correct against
  `int_stock__card_metrics.sql`'s actual `metrics`/`eligibility` CTE split (only the
  eligibility CTE branches on `company_type`).
- `dbt_analytics/seeds/_seeds.yml`'s `importance_tier` column description fix
  verified accurate against real production call sites (`frontend/card_ui.py`) — no
  tier-based filtering happens in the shipped rendering path, confirming the retired
  hero/tier visual split framing needed correcting.
- Live `dbt seed --full-refresh` + `dbt test` run against local DuckDB (round 3):
  16 rows load, all 18 schema tests pass, no CR contamination in any text field.
- Confirmed no dbt model `.sql` file, schema-test file, or `dbt_project.yml` setting
  changed anywhere in the cumulative diff — the blast radius is the seed's prose
  columns plus two schema-doc `description:` fields, exactly as claimed.

## equity-analyst-reviewer

VERDICT: PASS
risks_checked:
- Direction-cue generalization content, all 16 metrics: independently checked every
  metric's `interpretation`/`applicability` text against its catalogued `direction`
  for an oversimplification risk the universal ". Higher/Lower is better." cue might
  create. Found and the builder fixed 4 (`debt_to_equity`, `statement_roe_pct`,
  `revenue_growth_yoy_pct`, `current_ratio_stmt`); found 2 more already correctly
  handled pre-existing (`dividend_yield_pct`, `price_to_tangible_book`, both already
  carrying the caveat in `learn` text, matching the established gloss-flat/
  learn-carries-caveat pattern).
- `debt_to_equity`'s value-aware branch: confirmed self-detecting from the ratio's
  own sign is financially sound (debt is a balance-sheet magnitude, always ≥ 0, so a
  negative ratio structurally requires negative equity — no false positives), and
  that cue-suppression on that branch is correct (the ratio isn't monotonic in
  "leverage badness" once equity goes negative, so no flat directional claim would be
  reliable there).
- `statement_roe_pct`'s narrower learn-text-only treatment (vs. `debt_to_equity`'s
  value-aware branch): verified the technical claim that it isn't self-detecting the
  same way — both `stmt_net_income_common` and `stmt_stockholders_equity` can
  independently be signed, and only the ratio reaches the frontend, so a positive
  value is genuinely ambiguous between "profit ÷ positive equity" and "loss ÷
  negative equity" without an independent signal the pipeline doesn't currently
  expose.
- Full catalogue writing-voice pass (round 3, ~110 field comparisons across all 16
  metrics × 7 text columns): confirmed overwhelmingly punctuation-only with meaning
  preserved; found and the builder fixed the one genuine content drift
  (`current_ratio_stmt.applicability` had lost its "is not automatically good"
  corrective clause during simplification — a never-rendered field, so it never
  reached a user, but a real meaning-drift caught and restored).
- `docs/data_contract.md`'s market-activation coverage-audit wording fix
  ("operating-type eligibility metrics") cross-checked against
  `int_stock__card_metrics.sql`'s actual `is_card_eligible` branch and against every
  market in `docs/market_registry.yml` — accurate and not a substantive narrowing of
  the checklist's actual enforcement.
- `docs/metric_layer.md`'s "computes every catalogued metric" fix cross-checked
  against `int_stock__card_metrics.sql`'s `metrics` CTE line-by-line for all 16
  `metric_id`s — each computed exactly once, formulas matching the catalogue.
