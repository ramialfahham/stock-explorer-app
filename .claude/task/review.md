# Review

diff_sha256: 75f9ee293a755cd466d90f5964fa5f8705a0839c973cd97f4d34de4f85e9a1d1

_Statement enrichment (Slice 3a, DATA-ONLY), branch `feat/statement-enrichment`. Five blinded reviewers
(cold, read-only, per `.claude/review_routing.json`: scope-auditor always; analytics-engineer for `.sql`/`.yml`;
data-engineer for `ingestion/`; cto for `scripts/`+`tests/`; equity-analyst for `data_contract.md`). All five
PASS on this diff, first round. Lands 2 raw fields (`stmt_total_assets`, `stmt_net_income_common`) for the
Slice-3b ROA + corrected-ROE compute; no metric computed, eligibility / mart / export untouched._

## scope-auditor
VERDICT: PASS
risks_checked:
- Data-only holds end-to-end: both names grep to ONLY `stg_yf__fundamentals.sql` + `fct_fundamentals_snapshot.sql`;
  absent from `4_intermediate`/`5_marts`. `int_stock__card_metrics` admits them via `select *` but its `metrics` CTE
  re-projects an explicit list that drops them before `eligibility` → absent from `missing_metrics`/`is_card_eligible`;
  `mart_stock_cards` selects an explicit list without them. Baseline stays 25, export 100%.
- Both raw-schema mirrors in lockstep — `sources.yml` (+2) and `FUNDAMENTALS_COLUMNS` (+2); the
  `reindex(columns=FUNDAMENTALS_COLUMNS)` would silently drop the columns otherwise.
- Scope exact: all 15 staged files reconcile to the contract's non-artifact scope_paths — no drift, none uncovered.
- No new mechanism/cost: the new probe is read-only (prints only, import signature matches); `ingest.py`/`balance_sheet.py`
  add one extraction each on already-fetched frames — no new fetch/cadence/fan-out.
- No silent §6: ROA adoption + `Net Income Common Stockholders` numerator recorded as owner-locked in
  `decisions_reserved`; metric/eligibility/display consequences deferred to 3b/4 and absent here. (Non-blocking: fixture
  sets `net_income_common == net_income` — a legitimate no-minority-interest operating row.)

## analytics-engineer-reviewer
VERDICT: PASS
risks_checked:
- Re-projection boundary traced: `snapshot`/`resolved` `select *` admit both columns, but the `metrics` CTE (explicit
  projection) excludes them, so the downstream `eligibility` `select *` cannot resurface them; `mart_stock_cards` +
  `int_stock__sector_benchmarks` consume the post-projection model and are untouched. Grep confirms the names appear in
  no model at/below intermediate, nor in `frontend/`.
- Layer placement pure: cast-only in staging, `select *`+dedup in base, explicit passthrough in core; ingestion adds raw
  scalars only (no ratio).
- Doc gate satisfied: both columns documented at staging/base/core yml + `sources.yml` + `data_contract.md` +
  `intl-balance-sheet-row-labels.md`.
- Grain unchanged (no new fetch; dedup key + `latest` grain intact); tests extended (not deleted) — operating,
  financial-null, missing-sheet cases all assert `stmt_total_assets`; CI fixture carries both.

## data-engineer-reviewer
VERDICT: PASS
risks_checked:
- No new network fetch/cadence/fan-out/cost: `stmt_net_income_common` extracted from the already-fetched `income` frame;
  `stmt_total_assets` is one more `BALANCE_SHEET_FIELDS` entry over the already-fetched balance frame. Zero new
  `yf.Ticker`/statement accesses. The live probe is a standalone `__main__` diagnostic, not wired into `ingest_market`.
- Null-safety/idempotency: both extractors return honest null on an absent label (guarded `not in statement.index`); no
  crash on missing/empty/NaN; pure reads → deterministic re-runs; parquet full-snapshot shape unchanged.
- Mirror lockstep vs `.reindex` drop: `sources.yml` + `FUNDAMENTALS_COLUMNS` + CI fixture all updated; staging +2 casts,
  base `select *` propagates, core explicit select +2. Not in eligibility/mart.
- Canonical labels: `Total Assets` / `Net Income Common Stockholders` match the code constants, probe, and docs; the
  single-element total-assets tuple matches the "only equity keeps a 2nd fallback" pattern; intl doc records 100% across
  5 markets incl. financials.

## cto-reviewer
VERDICT: PASS
risks_checked:
- No new dependency/mechanism: the probe imports stdlib + `yfinance` (existing dep) + two internal modules that already
  exist (`latest_annual_value`, `call_with_retry`); no requirements/lockfile/hook/service change.
- Probe side-effect safety: whole-file check shows no open/write/to_parquet/subprocess — only `print`; yfinance reads
  wrapped in bounded `call_with_retry`; per-ticker exceptions caught, not raised; invoked by ZERO workflows → cannot alter
  CI posture/minutes.
- Re-run safety of fixtures: two constant dict entries; `mkdir(exist_ok=True)` + `to_parquet` overwrite → second run
  byte-identical, half-run self-healing; values consistent with field semantics.
- Mirror lockstep + CI cost: `FUNDAMENTALS_COLUMNS` matches `sources.yml` name/order; only read on the live-audit path
  (CI smoke runs `--offline`, never reads it). No workflow/secret/permission/sample-size change. `stmt_net_income_common`
  is a real produced column (not orphaned).

## equity-analyst-reviewer
VERDICT: PASS
risks_checked:
- Row-label canonicality: `Total Assets` and `Net Income Common Stockholders` are the exact canonical yfinance strings,
  matching `TOTAL_ASSETS_FALLBACK_ROWS` / `NET_INCOME_COMMON_ROW`, the probe, and every doc/yml/sources mirror — no drift.
- Attribution accuracy: the doc's "after minority interest & preferred dividends" is precise — `Net Income Common
  Stockholders` = NI − non-controlling interest − preferred dividends, the correct numerator for a common-attributed ROE.
  Cross-checked vs `stmt_stockholders_equity` (excludes minority interest via the deliberate `Stockholders Equity`/`Common
  Stock Equity` fallback), so the intended ROE is consistently common/parent on both sides — resolves the #141 mismatch.
- Probe reconciliation: the 2.4–5.3% (banks) / 0% (MSFT) minority-preferred gap is exactly `(NI − NI_common)/NI`;
  `computed_roe = net_income_common / equity` matches the documented pairing. No sign/magnitude anomaly.
- Sign/units + §6: both are currency levels, nullable, not clipped (no sign convention needed); docs strictly factual
  (one added token "ROA"), no metric defined/redefined, no threshold/direction/beginner copy; exact ROE pairing deferred to 3b.

## Non-blocking items recorded for Slice 3b (not defects here)
- **ROA vs ROE numerator asymmetry (equity-analyst):** ROA is documented as total net income ÷ total assets while the
  corrected ROE uses `stmt_net_income_common` ÷ common equity. Total-NI-over-total-assets for ROA is standard and
  defensible (return on the whole asset base funded by all capital providers), but the deliberate asymmetry should be
  locked explicitly with the equity-analyst when the ratios are actually computed in 3b.
- **Average vs period-end denominators (carried from the probe):** statement ROE/ROA use period-end balance-sheet values
  (no averaging), consistent with the #140 point-in-time methodology — so they differ from Yahoo's averaged/TTM scalars by
  design. Document this when the metrics are catalogued in 3b/4.
