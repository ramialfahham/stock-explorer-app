# Review

diff_sha256: 22912387e1308d9e6a11261fcf3bf8ef9bad5ad08714b0a9f0572ace1b3e4bc2

_Balance-sheet ingestion foundation (Slice 2, DATA-ONLY), branch `feat/balance-sheet-ingestion`.
Five blinded reviewers (cold, read-only, per `.claude/review_routing.json`: scope-auditor always;
analytics-engineer for `.sql`/`.yml`; data-engineer for `ingestion/`; cto for `scripts/`/`tests/`;
equity-analyst for `docs/data_contract.md`). All five re-ran against this final staged diff and PASS._

_Iterative review — earlier rounds caught and fixed real defects, then all five re-reviewed this
committed diff:_
1. _equity-analyst: the equity fallback included `Total Equity Gross Minority Interest` (folds in
   non-controlling interest → would overstate common equity / understate debt-to-equity) — dropped it._
2. _equity-analyst: cash fell back to a broader "cash + short-term investments" line (conflation) —
   narrowed to `Cash And Cash Equivalents` only._
3. _scope-auditor: two raw-schema mirrors (`sources.yml`, `audit_mart_vs_yfinance.py`
   `FUNDAMENTALS_COLUMNS`, whose `.reindex` would silently drop the new columns) were stale — updated
   in lockstep._
4. _equity-analyst: three fallback labels were not real yfinance keys and the "varies by market" framing
   was inaccurate (yfinance canonicalises labels via camel2title) — tuples tightened to canonical keys,
   framing reconciled across all four surfaces (module, probe, both docs)._

## scope-auditor
VERDICT: PASS
risks_checked:
- All 15 diff files are inside `scope_paths`; the two schema mirrors (`sources.yml`, `FUNDAMENTALS_COLUMNS`)
  carry all 6 new columns. Hunted for other schema enumerations — `backfill_fundamentals_parquet_schema.py`
  (finished migration over gitignored parquet) and `audit_yfinance_coverage.py::FIELD_LABELS`
  (eligibility-only probe) confirmed NOT live doc-sync gaps.
- decisions_reserved respected: docs record sourcing only, never assign a metric to a company type
  (`intl-balance-sheet-row-labels.md` explicitly defers the per-type matrix to a later owner slice); the
  financials-solvency ceiling is not decided; `data_contract.md` stays factual. DATA-ONLY invariant holds
  (grep: 6 columns absent from marts + eligibility CTEs → baseline 25 / export 100% / card byte-identical).

## analytics-engineer-reviewer
VERDICT: PASS
risks_checked:
- Layer placement: staging = pure `cast(... as double)`; base = `select *`; core = 6 bare passthrough
  selects (no computation). No layer-contract pattern triggered; consistent with the `stmt_*`/`qtr_*`
  precedent.
- Reach traced, not asserted: the `metrics` CTE in `int_stock__card_metrics.sql` re-projects an explicit
  list that drops the 6 columns; `eligibility`/`missing_metrics` reference only the original five; grep of
  marts + `export_to_supabase.py` returns nothing. Doc gate satisfied (6 cols × sources/staging/base/core);
  nullable BS cols carry no `not_null` (correct — null for financials). Baseline 25 / export 100% hold.

## data-engineer-reviewer
VERDICT: PASS
risks_checked:
- Offline tests (no network) cover fallback order, null-skip-to-older-column, absent/None/empty statement,
  operating + financial (bank → null current items) + missing balance sheet. Completeness honest: absent
  line → honest null; cash narrow (no short-term-investment conflation); equity excludes minority interest.
- Idempotency unchanged (full-overwrite parquet, same grain; `row.update(...)` only); both raw-schema
  mirrors updated (the `FUNDAMENTALS_COLUMNS` `.reindex` would otherwise drop the columns). One extra
  `ticker.balance_sheet` fetch/ticker — free rider on the existing per-ticker loop, owner-authorised.

## cto-reviewer
VERDICT: PASS
risks_checked:
- No new dependency/service/hook/workflow step (grep of `.github` + requirements). Probe + module are
  faithful mirrors of `probe_quarterly_op_labels.py` / `quarterly.py`; `FUNDAMENTALS_COLUMNS` is a plain
  tuple extension; single-element fallback tuples commented as intentional.
- Re-run/interruption safe: probe read-only + seeded (exit 0, in no workflow); fixture generator
  deterministic full-overwrite. Fail-safe: the CI `--offline` audit path never touches `.reindex`; the
  live path now retains the 6 columns rather than silently dropping them. No secrets / CI-permission change.

## equity-analyst-reviewer
VERDICT: PASS
risks_checked:
- Cross-checked every canonical label against the installed yfinance `const.py` balance-sheet key list and
  the `camel2title` transform: `stmt_stockholders_equity` = common equity attributable to the parent
  (excludes `Total Equity Gross Minority Interest`); `stmt_cash_and_equivalents` = the narrow
  `Cash And Cash Equivalents` (no conflation); `Tangible Book Value` is a currency total (not per-share).
  "yfinance canonicalises labels" is literally accurate; all four surfaces are consistent (grep-clean).
- Point-in-time (latest annual, no TTM) correct for a balance-sheet stock; financials null current-split is
  honest (yfinance omits absent keys). Docs strictly factual — no advice/threshold/beginner copy, no
  per-type "primary metric" claim; coverage honestly caveated (sample n=5/market stated). Diff is RAW
  landing only — no metric defined/redefined (§6 owner content untouched).

## Non-blocking items recorded for later slices (not defects in this diff)
- **Slice-3 owner confirmation:** the equity (excl. minority interest) and cash (narrow) definitional
  choices, and whether to re-probe the full universe before computing on the fallback tuples (n=5 sample).
- **Optional hardening:** a "first-wins when both equity labels present" unit test; wrap the
  `_numeric_columns` `pd.Timestamp` sort in try/except (shared with `quarterly.py` — a non-regression;
  do both modules).
- **Pre-existing (not this slice):** `sources.yml` + `FUNDAMENTALS_COLUMNS` also omit the #135/#136
  `info_*` data-only fields — a separate cleanup.
