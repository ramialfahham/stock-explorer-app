# Review — Sector/Lifecycle Router, Slice 4c (pre-revenue / survival card)

diff_sha256: 6819f55816bb338cb5a62ccaf18be9360d57329ef6bc0b897445042d2837c684

**Change under review (21 files):** the pre-revenue **survival card** — cash runway, monthly cash
burn, net-cash-vs-price, working capital — with a `pre_revenue` eligibility branch gating on
`net_cash_to_market_cap`; the 4 survival metrics catalogued; a new `currency_compact` display format
for the two dollar amounts; `pre_revenue` excluded from the sector-benchmark peer set (and from the
mart benchmark join, so a pre-revenue card never shows a peer-count it isn't part of); a synthetic
pre-revenue fixture (CI baseline 30 → 35); mart/export/Supabase carry + migration 009; docs.

**Required reviewers** (per `.claude/review_routing.json`, for the staged files): scope-auditor
(always); analytics-engineer-reviewer (`*.sql`/`*.csv`/`dbt_analytics/*.yml`); cto-reviewer
(`frontend/*`/`scripts/*`/`tests/*`); data-engineer-reviewer (`supabase/*`); equity-analyst-reviewer
(`metric_catalogue.csv`/`data_contract.md`).

**Review journey.** Cycle 1 — equity-analyst and analytics-engineer returned blocking verdicts: the
`net_cash_to_ev` EV denominator sign-flips when net cash exceeds enterprise value (contradicting
`higher_better`), and `pre_revenue` peers were polluting operating sector benchmarks. Resolved by an
**owner-approved (§6, AskUserQuestion, 2026-07-08) switch to `net_cash_to_market_cap`** (monotonic;
market cap ≥ 0, zero-guarded) and by excluding `pre_revenue` from `int_stock__sector_benchmarks`.
Cycles 2–3 — reviewers caught an incomplete prose sweep of the metric rename and the
`company_type`-drives-eligibility fact across `_marts.yml`, `int_stock__card_metrics.sql`,
`seed_ci_raw_fixtures.py`, `_docs.md`, the contract body, and finally `docs/data_contract.md`; the
mart benchmark-join asymmetry was fixed at the same time. Cycle 4 (this record) — the full blinded
panel re-reviewed the swept diff and all five returned PASS. Every reviewer independently confirmed the
executable eligibility/metric/benchmark logic is correct and internally consistent; the only residual
notes are two explicitly owner-deferred, pre-existing 4a/4b doc tags (`data_contract.md:75`
dividend-yield "(data-only)"; the EXPORT_COLUMNS/export-shape-table gap) — outside 4c scope.

Verification (repo `.venv`): `dbt build --no-partial-parse --full-refresh` PASS=105 / 0 errors;
`check_eligibility_baseline.py --baseline-path scripts/eligibility_baseline.ci.json` → 35;
export-health OK (100% fill); `pytest tests/` 95 passed; sqlfluff clean; layer-contract, sql-structure,
registry-sync, dbt-test-policy, dbt-documentation gates green. Survival smoke: `us_sp500:CIPRE` →
`net_cash_to_market_cap=0.4`, `working_capital=$2.1B`, `cash_runway_months=36`, `burn_rate_monthly=$58.3M`,
`sector_peer_count=None` (benchmark-join exclusion confirmed).

## scope-auditor
VERDICT: PASS
risks_checked:
- Staged set (21 files) is 1:1 with contract `scope_paths`; no out-of-scope file. Patch sha256 matches `6819f558…`.
- No new §6 owner decision this round; the `net_cash_to_market_cap` metric switch (cycle-1 amendment, AskUserQuestion 2026-07-08) and the survival-card copy (decisions_reserved, owner-signed) sign-offs are recorded.
- Incomplete-sweep failure mode closed: grep of live `data_contract.md` returns zero residual "does not affect / not part of is_card_eligible / not yet in / out of scope here" clauses; remaining `net_cash_to_ev` hits are data-only formula references.
- All deferred "five-metric framing" items (overflow_menu.py, test_overflow_menu.py, README.md, north_star.md, data_contract onboarding line) documented in the amendments, not silently dropped.

## analytics-engineer-reviewer
VERDICT: PASS
risks_checked:
- 3-branch per-type eligibility identical across all 5 sites (int `is_card_eligible` + `missing_metrics`, `_intermediate.yml` + `_marts.yml` expression tests, singular assertion); `pre_revenue` gates on `net_cash_to_market_cap` only, financial on the core three, operating on the five-metric AND.
- Metric switch fully swept: `net_cash_to_ev` survives only as the data-only computation, its column doc ("data-only … not in the catalogue or export"), the formula-reference list, and amendment history — never a gate; absent from the catalogue, `metrics.json`, mart SELECT, `EXPORT_COLUMNS`, migration 009.
- Benchmark exclusion consistent on both sides: `int_stock__sector_benchmarks.sql` peer CTE (`company_type != 'pre_revenue'`) and the `mart_stock_cards.sql` benchmark-join predicate mirror each other.
- Catalogue (4 pre_revenue rows, formats/perspective/direction/order, benchmarkable=false; five operating/financial metrics narrowed off pre_revenue) matches `metrics.json`; `_docs.md` + dbt-YAML column docs are per-type-correct.
- This round's `data_contract.md` prose (company_type block + export row + the two reworded headers) is factually correct; no new doc/code contradiction. Documented deferrals respected.

## cto-reviewer
VERDICT: PASS
risks_checked:
- `currency_compact` formatter (B/M/K, sign-aware, `_CURRENCY_SYMBOLS` map with code-prefix and no-currency fallbacks) matches its tests; `format_metric_value(metric, value, currency=None)` is backward-compatible (only the `currency_compact` path uses the new arg; all pre-existing 2-arg callers valid).
- Real render path: `_metric_cell_html` passes `card.get("currency")`, reached by `build_card_html` → `render_stock_card`; pre_revenue renders exactly the 4 lens-ordered survival metrics, no un-valued em-dash; currency reaches production cards via mart SELECT + `EXPORT_COLUMNS`.
- Fixture docstring names the real gate (`net_cash_to_market_cap = (2100-100)/5000 = 0.4`, runway 36, burn ≈58.3M, WC 2100M); no stale `net_cash_to_ev`/0.667.
- Tests exercise real code; no dependency/workflow/lockfile/secret changes anywhere in the patch. `frontend/*`/`scripts/*`/`tests/*` byte-identical to the prior green round.

## data-engineer-reviewer
VERDICT: PASS
risks_checked:
- Migration 009 adds exactly the 4 survival columns (`net_cash_to_market_cap`, `working_capital`, `cash_runway_months`, `burn_rate_monthly`) as nullable `numeric`, additive/idempotent (`add column if not exists`), sequential file number; uses `net_cash_to_market_cap`, not `net_cash_to_ev`.
- Three-surface consistency: `EXPORT_COLUMNS`, the `data_contract.md` export table, and the per-type eligibility section all name `net_cash_to_market_cap`; no `net_cash_to_ev` leaks into export/catalogue.
- Export idempotency/backfill unchanged (`on_conflict="market_code,ticker,snapshot_date"`, keep-last-good-snapshot on empty, NaN→None); new columns additive/nullable, so pre-migration rows read null.
- The two reworded `data_contract.md` headers (balance-sheet intro + "Additional computed metrics — formula reference") are factually accurate: the now-catalogued/exported metrics are grouped correctly and only genuinely data-only intermediates are named. The non-blocking item flagged last round is resolved.

## equity-analyst-reviewer
VERDICT: PASS
risks_checked:
- `net_cash_to_market_cap` definition/direction/format match the model; market cap ≥ 0 and zero-guarded ⇒ monotonic, no sign-flip/pole (the cycle-1 EV fix intact); `net_cash_to_ev` no longer gates anything.
- Survival copy for all 4 metrics: formulas match the model; beginner-appropriate; NO buy/sell/hold or imperative advice language (descriptive characterization only).
- `cash_runway_months` "assumes steady burn" caveat is present in the RENDERED `learn` copy (metrics.json ↔ seed identical; no `metric_learn_text` override), reaching the card.
- `company_type` "does not affect is_card_eligible" clause is gone from `data_contract.md` (grep-confirmed); the file is factual. Owner §6 sign-off of the metric switch recorded in the cycle-1 amendment; copy sign-off in decisions_reserved. Documented deferrals respected.
