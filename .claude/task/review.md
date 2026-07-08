# Review

diff_sha256: 02f810c7e0baaa18bd3ded9a85abd8313e60c1a505a1106fdb69629bfb84277f

_Sector/Lifecycle Router — **Slice 4b** (financial/bank card + per-type eligibility rework), branch
`feat/sector-router-slice4b`. Blinded reviewers (cold, read-only, per `.claude/review_routing.json`):
scope-auditor (always) · analytics-engineer (`*.sql`/`*.csv`/`dbt_analytics/*.yml`) · cto
(`frontend/*`/`scripts/*`/`tests/*`) · data-engineer (`supabase/*`) · equity-analyst
(`metric_catalogue.csv`/`data_contract.md`). **All five PASS.** Cycle 1: scope-auditor / analytics-engineer /
cto / data-engineer PASS; equity-analyst ESCALATE (2 owner-judgment items) + an analytics non-blocking nit.
Cycle 2 resolved both: (Q2) reworded `price_to_tangible_book` applicability ("meaningless or negative" -> "not
shown" — the model guards tangible book > 0, so it's omitted not rendered negative); (Q1) **owner kept the
P/E-based core three** (declined the P/TBV swap) via AskUserQuestion; fixed the stale "five-metric" prose in the
gaps mart; **owner §6 copy sign-off** obtained (AskUserQuestion "Approve — ship as-is", 2026-07-08). The final
diff `02f810c7` differs from the analytics/cto/data-engineer reviewed hash (`56eccecd`) only by copy/prose fixes
(the P/TBV applicability + the gaps description + the contract amendment) — no logic/mechanism/schema change in
their territories, so those PASSes stand. Verify: dbt build PASS=104, pytest 91, CI eligibility baseline 25->30,
bank card renders 7 lens-grouped metrics (no em-dash), export-health 100%.

## scope-auditor (cycle 2)
VERDICT: PASS
risks_checked:
- §6 copy sign-off is self-contained in the contract amendment (4 bank-metric copy presented via AskUserQuestion, owner selected "Approve — ship as-is", 2026-07-08) — not silent.
- Owner kept the P/E-based core three (declined the P/TBV swap) — documented in the amendment, not silently decided.
- Scope integrity: exactly 16 files, all in `scope_paths`; the five eligibility-assumption sites all updated (int model + int/mart expression tests + singular assertion + LLOY/HSBA unit tests); catalogue narrowing correct; `data_contract.md` per-type + export table synced.

## analytics-engineer (cycle 1)
VERDICT: PASS
risks_checked:
- Per-type eligibility consistency across all sites: the `eligibility` CTE's `missing_metrics` + `is_card_eligible` CASE are mirrored byte-for-byte in the `_intermediate.yml`/`_marts.yml` `expression_is_true` tests and `assert_eligible_mart_rows_have_all_metrics.sql`; `assert_mart_row_count_matches_card_metrics.sql` is symmetric (untouched). No site still hardcodes the 5-AND.
- Catalogue-vs-model formula fidelity: the 4 new rows' numerator/denominator_expr match `int_stock__card_metrics.sql` verbatim, all same-statement-window; the mart is a SELECT-only carry (no recompute); the 25->30 pool growth is hand-verified against the bank fixture's real inputs.
- (Non-blocking nit, now fixed:) stale "five-metric" prose in the `mart_stock_eligibility_gaps` description -> "per-type eligibility gate".

## cto-reviewer (cycle 1)
VERDICT: PASS
risks_checked:
- Operating-card parity: hand-verified the operating metrics' (perspective, display_order) pairs are monotonic in lockstep, so `metrics_for_card`'s new lens-then-order sort is provably identical to the old display_order sort for the operating card (corroborated by the unchanged `test_metrics_for_card_operating_includes_new_metrics_in_order`). Lens-sort reuses the existing CI-governed `perspective` vocabulary — no new column/renumber.
- Re-run/interruption safety: `seed_ci_raw_fixtures.py` rewrites each parquet fresh (no append) so a re-run yields one bank per market, not cumulative; `export_to_supabase.py` upsert key is independent of the 4 new columns; migration 008 applies before export in `data_pipeline.yml`.
- Fixture correctness: hand-verified the bank fixture's four metric values against the model SQL; `company_type='financial'` derives from `info_sector`; `debt_to_equity` excluded via `applies_to` (catalogue-driven), not null inputs. No dependency/workflow/secret change.

## data-engineer-reviewer (cycle 1)
VERDICT: PASS
risks_checked:
- Migration 008 idempotency/convention: `add column if not exists` on 4 nullable numeric columns, header comment verbatim-matches 007, no overlap with 007's columns, sorts/applies after 007, double-guarded by `apply_supabase_migrations.py` filename tracking.
- Export idempotency: `EXPORT_COLUMNS` extension is name-keyed (`{col: row[col] for col in EXPORT_COLUMNS}`), `on_conflict` unchanged and excludes the new columns; batch upserts re-runnable. Backfill null-safe (frontend `metrics_for_card` drops null metrics — no dash).
- Schema contract sync verified column-for-column: `data_contract.md` export table + per-type eligibility prose match `EXPORT_COLUMNS` and the dbt CASE; baseline 25->30 arithmetically consistent (5 active markets × 1 bank). No `ingestion/` change.

## equity-analyst-reviewer (cycle 2)
VERDICT: PASS
risks_checked:
- `price_to_tangible_book` copy now accurately describes ABSENCE (null when tangible book <= 0, per the model's `> 0` guard) with "zero or negative" attributed to the input, plain English, no `≤` symbol — mirrored identically in seed + metrics.json.
- Bank eligibility gate (P/E-based core three; P/TBV swap declined) is the owner's documented §6 call, not silently overridden.
- All 4 new formulas (P/TBV, net margin, ROA, dividend yield) match `int_stock__card_metrics.sql` line-by-line; `roa_pct` copy surfaces the ROA/ROE numerator asymmetry + period-end basis; dividend passthrough pinned by a unit test; no advice language anywhere.

## Non-blocking / deferred to follow-on slices
- **Slice 4c (pre-revenue card):** the survival set (`cash_runway_months`, `burn_rate_monthly`, `net_cash_to_ev`, `working_capital`, + a cash level), its `applies_to = pre_revenue`, a per-type eligibility branch (pre_revenue currently rides the else/5-AND, so it stays ineligible until 4c), cash-first ordering, and the FCF-yield-negative copy.
- **Full-pipeline baseline (843)** will rise as banks become eligible; `check_eligibility_baseline.py` fails only on drops, so it passes — refresh via `--write-baseline` on the next weekly pipeline (owner; not local).
- Value-aware negative-equity gloss for `debt_to_equity`/`statement_roe_pct` (from 4a) remains a candidate — the applicability caveat already warns.
