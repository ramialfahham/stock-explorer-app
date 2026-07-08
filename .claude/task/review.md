# Review

diff_sha256: d85a3630a67b604efff3e1d7d79c9d35e4d248e11b1ad5749a6fee61a386c269

_Sector/Lifecycle Router — **Slice 4a** (per-type card render mechanism + `company_type` carry + grown
operating card), branch `feat/sector-router-slice4a`. Blinded reviewers (cold, read-only, per
`.claude/review_routing.json`): scope-auditor (always) · analytics-engineer (`*.sql`/`*.csv`/`dbt_analytics/*.yml`)
· cto (`frontend/*`/`scripts/*`/`tests/*`) · data-engineer (`supabase/*`) · equity-analyst
(`metric_catalogue.csv`/`data_contract.md`). **All five PASS.** Three cycles: (1) analytics FAIL (mart/seed
test coverage) + equity FAIL (ROE copy: "two-year average" imprecision + "minority interest" jargon) +
data-engineer PASS (w/ a done_when wording note); (2) fixes applied → analytics ESCALATE (non-blocking: add a
negative-equity unit test), equity FAIL (residual jargon in the `description` field), scope ESCALATE (owner §6
copy sign-off), cto PASS; (3) negative-equity unit test added, `description` jargon dropped, owner sign-off
obtained (AskUserQuestion "Approve — ship as-is", 2026-07-08) → analytics/equity/scope PASS. The final diff
`d85a3630` differs from the analytics/equity/cto/data-engineer reviewed hash (`d73c25cb`) only by the contract's
self-contained sign-off wording — no code/content change. Verify: dbt build PASS=102, pytest 88, CI eligibility
baseline unchanged (25), export-health 100%._

## scope-auditor (final)
VERDICT: PASS
risks_checked:
- §6 owner sign-off for the `statement_roe_pct`/`debt_to_equity` copy reword is now self-contained in the contract amendment with the explicit AskUserQuestion approval ("Approve — ship as-is", 2026-07-08) — no longer merely deferred to merge.
- All 16 staged files remain inside `scope_paths`; no out-of-scope file modified; `seed_ci_raw_fixtures.py` correctly untouched (conditional path — fixtures already carry the balance-sheet inputs).
- `applies_to` pipe-delimited format is documented (technical_definition) and guarded (`_seeds.yml` not_null + `test_metric_catalogue.py` subset check) — an acceptable implementation choice, not a silent owner decision.

## analytics-engineer-reviewer (cycle 3)
VERDICT: PASS
risks_checked:
- `card_metrics_statement_metrics_negative_equity` feeds nonzero-negative `stmt_stockholders_equity` (-30000), distinct from the zero-equity→null test — exercises the sign-varying branch the `!= 0` guard allows through; arithmetic verified (debt_to_equity −0.5; statement_roe_pct +20.0 = loss ÷ negative equity → spuriously positive, the documented caveat).
- `applies_to` `not_null` in `_seeds.yml`; `mart_stock_cards_current_ratio_stmt_non_negative` (`>= 0 or null`) mart consistency test; `mart_stock_cards.sql` is a SELECT-only carry of the 3 metrics + `company_type` (no computation in the mart).
- Catalogue `numerator_expr`/`denominator_expr` for all three new metrics match the SQL over the same annual-statement row set (no cross-window mismatch).

## cto-reviewer (cycle 2)
VERDICT: PASS
risks_checked:
- `applies_to` reuses the existing catalogue→metrics.json→card_copy bridge (same seed/generator/loader); `metrics_for_card()` is one pure function; all three `card_ui.py` loops migrated off `ALL_METRICS` (import removed). No parallel mechanism.
- Fail-open verified by execution: missing/None `company_type` renders the full "operating" card (no silent suppression). `export_metric_definitions_json.py` idempotent (no-drift subprocess test); `export_to_supabase.py` upsert keys unchanged by the added nullable columns.
- New tests non-vacuous (per-type omission; null→no em-dash via literal `ss-metric-value">—<` absence; missing-type default; tier split disjoint+complete); no dependency/CI/secret change. (Minor non-blocking: the `tier` param is test-only, mirroring the pre-existing unused `VISIBLE_METRICS`/`DEEP_DIVE_METRICS`.)

## data-engineer-reviewer (cycle 1)
VERDICT: PASS
risks_checked:
- Migration `007_router_card_columns.sql` is additive + `add column if not exists` (matches the 004–006 convention); `apply_supabase_migrations.py` tracks applied files (no double-apply) and rolls back the whole file atomically on partial failure.
- Export upsert is name-keyed (`{col: row[col] for col in EXPORT_COLUMNS}`) — adding columns can't misalign values; `on_conflict="market_code,ticker,snapshot_date"` unchanged. Transient-null handled (frontend defaults a missing `company_type` → operating, precedented by 004/006); `data_contract.md` export table synced with `EXPORT_COLUMNS`.
- No `ingestion/` file in the diff — the loader territory is dormant; only the `supabase/*` path triggered this reviewer.

## equity-analyst-reviewer (cycle 3)
VERDICT: PASS
risks_checked:
- "minority interest" jargon removed from BOTH new-metric `description` fields (seed + `metrics.json` mirror; repo-wide grep clean), meaning preserved ("owners' stake" / "belonging to common shareholders"), no replacement jargon introduced.
- "two-year average" → "Yahoo averages equity across the year" — an accurate paraphrase of standard ROE methodology (average of beginning + ending equity within one period), no new false precision.
- All three new rows: `calculation` matches `int_stock__card_metrics.sql` exactly (with null/zero-equity guards), direction correct (debt_to_equity lower_better; current_ratio_stmt/statement_roe_pct higher_better), applicability complete (banks / negative-thin equity / near-zero denominators), no advice language.

## Non-blocking / deferred to follow-on slices
- **Value-aware negative-equity gloss** for `debt_to_equity`/`statement_roe_pct` (a "net cash"-style re-label when equity is negative, like `net_debt_to_ebitda`) — the applicability caveat already warns the beginner; a value-aware re-label is new §6 copy → deferred to 4b (analytics-engineer cycle-2 Q2).
- Per-type **eligibility** rework + **ROA/ROE numerator-asymmetry** copy (ROA joins ROE on the financial card) + the **dividendYield scale-regression guard** land in 4b/4c per the approved plan. 4a keeps the five-metric AND untouched (baseline stable).
