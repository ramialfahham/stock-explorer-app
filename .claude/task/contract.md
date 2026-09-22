# Task contract
> DISPOSABLE. **Owns:** THIS task's objective, `scope_paths`, reserved decisions and
> `done_when`.
> **Never:** anything that outlives the task. Overwritten by the next task.

objective: Follow-up from the dbt-layer audit (owner asked about model/column
  documentation quality). `scripts/check_dbt_documentation.py` only checks that a column
  description is non-empty; `docs/engineering_standards.md` §2's actual anatomy for
  core/intermediate/marts columns requires business meaning, unit/scale, and "Null when:
  ...". The "null when" half is mechanically checkable (a column without a `not_null` test
  can genuinely be null, so its description should say when); "unit/scale" is not
  (too varied to check without a flood of false positives) -- out of scope here, flagged
  to the owner, not silently attempted.

  Owner-approved scope: extend `scripts/check_dbt_documentation.py` with a new
  `check_null_when_documented` function (same file, same manifest-reading pattern it
  already uses -- no new script, already wired into `validate:full` via the existing
  invocation) that fails when a core/intermediate/marts column (a) has no `not_null` test
  (derived from `target/manifest.json`'s test nodes, not assumed) and (b) its description
  doesn't mention "null" (case-insensitive). Exempts columns whose name starts with
  `info_`/`stmt_`/`qtr_` -- this repo's own established naming convention for an
  unmodified raw-field passthrough (confirmed by reading `stg_yf__fundamentals.sql`: these
  prefixes are assigned once at staging and never renamed through base/core/intermediate/
  marts) -- their nullability is inherited from the raw source and already implicit ("the
  provider may not report this field"), not a computed condition worth restating 53 times.
  Owner picked this scope over writing 91 near-identical passthrough null-when sentences.

  Running the check against the real manifest before writing any fix found 32 real
  violations (all genuinely computed columns, not passthroughs) across `dim_stock`,
  `int_stock__card_metrics`, `int_stock__sector_benchmarks`, `mart_stock_cards`,
  `mart_stock_eligibility_gaps`. Each one's actual null condition is derivable directly
  from its model SQL's existing guard logic (already read in the prior audit session) --
  fixed by adding an accurate "Null when: ..." clause to each, describing existing
  behavior, not inventing a new rule. One real side-finding surfaced along the way, not
  fixed here (a different kind of gap, owner's call): `is_card_eligible` is a boolean that
  the model's own CASE logic never actually leaves null (every branch returns true/false),
  so its real fix is a missing `not_null` test, not documentation -- flagged, not silently
  added, since a new test assertion is closer to a data-contract change than a doc fix.

  Round-1 review found two real gaps, both fixed. (1) scope-auditor: the new
  `info_`/`stmt_`/`qtr_` exemption narrows what `engineering_standards.md` §2 actually
  enforces, but that doc was never updated to say so -- a reader would have no way to learn
  the exemption exists. Fixed: added a paragraph to §2 documenting it, mirroring
  `check_model_descriptions`' existing Grain/What/Source doc-sync precedent in the same
  file. (2) analytics-engineer-reviewer: four of the 32 "Null when" clauses
  (`dim_stock.sector`/`currency`, `mart_stock_cards.sector`/`currency`, and
  `mart_stock_eligibility_gaps.sector`) were factually wrong against the actual SQL --
  `dim_stock`'s sector/currency are straight passthroughs (`f.info_sector as sector`, no
  coalesce), so "no fundamentals row matched" was only half the real condition (a matched
  row's own field can also be null); `mart_stock_cards`' sector/currency actually
  `coalesce(snapshot_info, dim_stock_field)`, so "no fundamentals row matched" describes an
  impossible condition there (every row in this mart already has a fundamentals row by
  construction -- `int_stock__card_metrics` selects directly `from fct_fundamentals_snapshot`,
  no join). Re-derived each from the actual SQL and rewrote all five -- this was exactly the
  "wrong claim is worse than no claim" risk the task itself called out.

  Round-2 review (cto-reviewer) found one more: `cash_runway_months`'s description (in both
  `_intermediate.yml` and `_marts.yml`) already mentioned "null" before this task touched it
  -- so it never appeared in the 32-violation list -- but the claim itself was incomplete:
  `int_stock__card_metrics.sql`'s CASE guards on three conditions
  (`computed_fcf is not null`, `computed_fcf < 0`, `stmt_cash_and_equivalents is not null`),
  the old text named only the first two. Fixed in both files even though this column was
  never a mechanical violation, since the point of this task was accurate null
  documentation, not just satisfying the checker.

  Round-3 review (cto-reviewer) found one more small, precisely-scoped instance of the same
  pattern -- `ebit_margin_pct` (and its sibling `ebit_margin_basis`) omitted the revenue-
  denominator-is-zero guard alongside the input-completeness one -- fixed in both files, same
  as `cash_runway_months`. It also found a much larger family of the same pattern: ~50
  `sector_median/min/max/q1/q3_*` columns in `int_stock__sector_benchmarks`/`mart_stock_cards`
  all share "Null when: sector_peer_count < 8," which is incomplete for non-gating metrics
  (a metric can be null within an otherwise-large eligible peer group) and omits a
  code-commented known limitation on two of them. Asked the owner: fix now (much bigger
  diff, more review rounds) or defer as its own task. Owner chose defer -- filed as
  gitlab.com issue #23, not fixed here. Scope for THIS task ends at the 32 original
  violations plus the two small, isolated accuracy bugs (`cash_runway_months`,
  `ebit_margin_pct`) found incidentally while verifying them.

scope_paths:
  - scripts/check_dbt_documentation.py
  - docs/engineering_standards.md
  - dbt_analytics/models/3_core/_core.yml
  - dbt_analytics/models/4_intermediate/_intermediate.yml
  - dbt_analytics/models/5_marts/_marts.yml
  - tests/tooling/test_check_dbt_documentation.py
  - .claude/task/contract.md
  - .claude/task/review.md

decisions_reserved: The raw-prefix exemption (option 2: narrow the check rather than write
  91 near-identical passthrough sentences) was asked and answered live. Deferring the
  ~50-column sector-benchmark family to its own task (gitlab.com issue #23) instead of
  fixing it here was asked and answered live -- a scope/schedule call per
  working-agreement.md SS6. The `is_card_eligible` not-null-test gap is flagged, not
  decided -- adding a new test assertion changes what CI guarantees about the data, which
  is the owner's call, not bundled into a documentation task.

done_when:
  - `check_dbt_documentation.py`'s new `check_null_when_documented` function fails on any
    core/intermediate/marts column with no `not_null` test, no `info_`/`stmt_`/`qtr_` name
    prefix, and no "null" mention in its description. Already wired into `validate:full`
    via the script's existing invocation -- no `.gitlab-ci.yml` change needed.
  - All 32 real (non-exempt) violations found against the current manifest are fixed with
    an accurate "Null when: ..." clause reflecting the model's actual existing guard logic
    -- no invented business rules, verified against the SQL before writing each one.
  - The check passes clean against the current codebase once the 32 are fixed.
  - A unit test for the new check's logic (the raw-prefix exemption, the not_null-test
    lookup, the "mentions null" substring check, layer scoping, missing-description
    handling) using a small fake manifest fixture, not a full `dbt build`.
  - `pytest tests/` passes in full.
  - `check_no_em_dash.py`, `check_context_budget.py` pass.

impact_map: One function added to `scripts/check_dbt_documentation.py` (mechanical
  enforcement only, no new dependency -- reads `target/manifest.json`, the same pattern
  the file already uses), 32 column-description edits across 3 already-existing YAML files
  (`_core.yml`, `_intermediate.yml`, `_marts.yml` -- content additions, not corrections;
  nothing currently documented was wrong, just incomplete), one new test file (7 tests).
  No model SQL, no metric definition, no product-facing change, no CI file change.
