# Active work — handover

_The next session is handed exactly this file. Keep it current._

## Current task

**Reshaping the dashboard into a beginner financial-literacy tool** — sector-aware metrics + AI "reads"
+ a health verdict. The keystone is the **Sector/Lifecycle Router**, built in slices. This session
brought a **major correction — "do it right":** compute from **period-matched financial statements,
not Yahoo `info` scalar shortcuts**, and design per-type metric sets from an explicit **metric-assignment
matrix** (below). **Slices 1–2b are all MERGED** (#139 classifier · #140 balance sheet · #141 statements)
— **the entire raw data foundation is in.** Slice 3 (the compute) is built in two PRs: **Slice 3a
(statement enrichment) MERGED (#142)** and **Slice 3b (per-type metric compute) PR'd (not merged).**
**Slice 4 — the Router mechanism (per-type sets + eligibility rework + display) — is the clear next step.**
This session locked the metric DEFINITIONS, adjudicated an external review, and discovered + fixed the
yfinance dividendYield percent-scale bug (see Decisions).

## Status

- **Metric layer + all data-only `info_*` metrics MERGED** (#131–137: ROE, four ratios, FCF yield —
  computed in `int_stock__card_metrics`, still nothing rendered).
- **Sector Router — Slice 1 (`company_type` classifier) MERGED (#139).** `financial` (info_sector =
  'Financial Services'), `pre_revenue` (stmt_total_revenue present & ≤ 0; null → operating), else `operating`.
- **Sector Router — Slice 2 (balance-sheet foundation) MERGED (#140).** 6 raw balance-sheet lines,
  data-only: `stmt_stockholders_equity` (excl. minority interest), `stmt_total_debt`, `stmt_current_assets`,
  `stmt_current_liabilities`, `stmt_cash_and_equivalents` (narrow), `stmt_tangible_book_value`. New module
  `ingestion/yfinance/balance_sheet.py` (mirrors `quarterly.py`; point-in-time, latest annual, no TTM).
- **Sector Router — Slice 2b (statement completion) MERGED (#141).** 6 raw fields, data-only:
  `stmt_operating_cash_flow`, `stmt_capital_expenditure` (negative = outflow), `stmt_interest_expense`
  (positive), `stmt_net_income`, `info_dividend_yield`, `info_payout_ratio`. Inline extractions (no new
  module — canonical labels; income/cashflow already fetched). **The three-statement raw data foundation is
  now complete.**
- **Sector Router — Slice 3a (statement enrichment) MERGED (#142).** 2 raw fields, data-only:
  `stmt_total_assets` (balance sheet `Total Assets` → ROA) and `stmt_net_income_common` (income `Net Income
  Common Stockholders` → the correctly-attributed ROE numerator, fixing the #141 mismatch). Probe
  (`scripts/probe_roa_total_assets.py`, JPM/BAC/HSBA.L/MSFT): labels 100% incl. non-US; gap 2.4–5.3% banks, 0% operating.
- **Sector Router — Slice 3b (per-type metric compute) PR'd, NOT merged** (branch
  `feat/statement-metric-compute`, commit `d80b447`; 3 blinded reviewers PASS). 13 data-only computed columns
  in `int_stock__card_metrics` (debt_to_equity, interest_coverage [abs-guarded], current_ratio_stmt,
  working_capital, price_to_tangible_book, net_margin_pct, roa_pct, statement_roe_pct, dividend_yield_pct,
  computed_fcf, cash_runway_months, burn_rate_monthly, net_cash_to_ev) + 4 unit tests. Coexist with the
  info-scalars; eligibility/mart/export untouched (baseline 25, export 100%).
- **UI redesign mock: approved look** (cohesive card, scan→deep tiers, one disclosure, label chips,
  words-not-arrows). NOT implemented — waits on the Router.

## Decisions locked (the important ones)

- **"Do it right" (this session):** stay on yfinance, **but compute from period-matched financial statements,
  not `info` scalars.** yfinance exposes the full balance sheet + cash flow (incl. Operating Cash Flow, Capex)
  + income statement; the balance sheet was the missing third — landed in #140.
- **The metric-assignment MATRIX (design frame, this session).** Perspectives (valuation · profitability ·
  growth · solvency · liquidity · cash · returns) are semi-universal *lenses*; the metric filling each is
  **type-specific**; some lenses are **honestly EMPTY** — do NOT fill with a weak proxy.
  - **operating** — fills all seven (the challenge is *curation* for a scannable card, not validity).
  - **financial** — valuation (**P/B → P/TBV**, P/E), returns (**ROE**, dividend yield), profitability (margin),
    growth. **NO sound solvency/liquidity/cash metric** — the real ones (CET1/Tier 1/NIM/asset quality) are
    unsourceable from yfinance → leave the solvency slot **honestly blank**, don't fake it.
  - **pre_revenue** — a balance-sheet **survival** story: cash, burn, runway, net cash vs EV, working capital.
- **Metric definitions locked (this session, §6):** (1) **statement ROE computed correctly** — ingest
  `Net Income Common Stockholders` so ROE = common income ÷ common equity (fixes the #141 attribution
  mismatch; landed in Slice 3a). (2) **ROA adopted into the financial column** — the one sourceable,
  bank-relevant metric from the external review; compute `net income ÷ total assets` from statements (the
  `returnOnAssets` scalar is a probe cross-check only). (3) **cash_runway = cash ÷ FCF-burn, in months**
  (FCF-burn = OCF + Capex when negative). (4) **coexist, don't replace** — new computed columns sit alongside
  the existing info-scalar `current_ratio`/`roe_pct`/`fcf_*`; Slice 4 picks per-type display.
- **External metric review adjudicated (this session):** an outside review (Gemini) proposed CET1/Tier 1/
  LCR/NIM/ROIC/ARR/NRR/TAM etc. — all rejected as **unsourceable from yfinance** and/or too advanced for a
  beginner card (the honest-blank ceiling stands). Only **ROA** survived both filters (sourceable +
  beginner-legible) → adopted. Filter every future metric suggestion through: (1) sourceable from yfinance?
  (2) legible to a true beginner?
- **yfinance `dividendYield` is PERCENT, not a fraction (discovered in 3b, verified live):** MSFT 0.94 =
  0.94%, JPM 1.78, KO 2.56, O 5.15 — so `dividend_yield_pct = info_dividend_yield` (NO ×100), and the stale
  "(decimal)" docs were corrected to "(percent)". `payoutRatio` IS still a fraction (MSFT 0.21);
  `returnOnEquity`/`returnOnAssets` are fractions (so `roe_pct`/`roa_pct` ×100 stay correct). **Slice 4 must
  add a persisted scale-regression guard** — a future yfinance version reverting dividendYield to a fraction
  would ship a 100× error.
- **Corrected: debt-to-equity + interest coverage are OPERATING-company solvency metrics, NOT bank metrics**
  (interest coverage is meaningless for a bank — interest is its cost of funds; debt-to-equity is weak for
  banks). The earlier "build the bank debt measures" framing was mine and was wrong; the matrix reassigns them
  to operating companies (complementing net-debt/EBITDA).
- **Outlier magnitudes are REAL** (mis-applied to the wrong type) — route to the right lens, don't clip.
- **Cataloguing a metric RENDERS it** (catalogue → metrics.json → card_copy → card_ui, uniform). New metrics
  stay **data-first** (compute, no catalogue row) until the Router owns per-type cataloguing/display.
- **Authoring metric copy/caveats is §6.** Data-only PRs keep `data_contract.md` strictly factual.
- **Plan-mode spine** (EnterPlanMode → ExitPlanMode → plan_implement_gate); no prose plan-back. Ask the owner
  in PLAIN language, with a recommendation, sparingly (see `ask-questions-plain-language`).
- **AI assessments:** educational, NEVER advice; true-beginner language; reason only from the given numbers;
  end with a health verdict (🟢/🟡/🔴).

## Next concrete actions (the sliced Router — corrected)

Approved plans: `~/.claude/plans/noble-forging-beaver.md` (parent: "do it right" + matrix);
`~/.claude/plans/logical-roaming-brook.md` (Slice 3a/3b: enrichment + compute). Don't land it in one PR.

1. **Slice 1 — company-type classifier: MERGED (#139).**
2. **Slice 2 — balance-sheet foundation: MERGED (#140).**
3. **Slice 2b — statement completion: MERGED (#141).**
4a. **Slice 3a — statement enrichment: MERGED (#142).** 2 raw fields (`stmt_total_assets`, `stmt_net_income_common`).
4b. **Slice 3b — per-type metric compute: PR'd, NOT merged** (`feat/statement-metric-compute`, `d80b447`;
   3 reviewers PASS). Built (data-only) in
   `int_stock__card_metrics` (existing `CASE WHEN <inputs> AND <denom> != 0` guard idiom; coexist naming;
   eligibility gate lines 156-177 untouched). Metrics: `debt_to_equity`, `interest_coverage`
   (= `eff_stmt_op` ÷ **`abs(stmt_interest_expense)`** — landed unsigned), `current_ratio_stmt`,
   `working_capital` (from BS); `price_to_tangible_book` (= `info_market_cap` ÷ `stmt_tangible_book_value`);
   `net_margin_pct`; `roa_pct` (= `stmt_net_income` ÷ `stmt_total_assets`); `statement_roe_pct`
   (= `stmt_net_income_common` ÷ `stmt_stockholders_equity`); `dividend_yield_pct`; `computed_fcf` (= OCF +
   Capex, **Capex NEGATIVE**); `cash_runway_months` + `burn_rate_monthly` (pre-rev, when computed_fcf < 0);
   `net_cash_to_ev` (pre-rev; needs a computed EV — include if clean else defer). Plan:
   `~/.claude/plans/logical-roaming-brook.md`.
   - **3b review notes (from the 3a equity-analyst — carry in):** (a) **lock the ROA/ROE numerator asymmetry
     explicitly** — ROA uses total NI ÷ total assets while ROE uses common NI ÷ common equity (each internally
     consistent, but state it when computing); (b) statement ROE/ROA use **period-end** denominators (no
     averaging, per #140) → differ from Yahoo's averaged/TTM scalars by design; document when catalogued.
   - Add dbt **unit tests** per metric guard (null → null; zero denom → null; interest-coverage sign;
     runway/burn only when burning). Full 5-reviewer cycle; the equity-analyst scrutinises the formulas.
5. **Slice 4 (← START HERE) — the Router mechanism.** Per-type metric sets (the matrix); **eligibility rework**
   (the hardcoded five-metric AND in `int_stock__card_metrics.sql` — now the `eligibility` CTE, shifted down by
   the 3b columns — can't express sector-varying sets; likely a per-type required-set config); carry
   `company_type` into `mart_stock_cards`; per-type `card_ui`/`card_copy` display; **catalogue rows +
   owner-approved applicability/beginner copy**; recalibrate the eligibility baseline. Sub-split operating
   (parity) → financial → pre-revenue.
   - **Copy the Router must author (§6, reviewer-flagged):** ROE (negative/thin equity → spuriously positive;
     breaks for financials); **FCF yield — NEGATIVE for cash-burners** (#137 flag); EV/EBITDA & P/B financials
     caveats.
   - **Carry-ins from the 3b review (non-blocking there — address in Slice 4):** (a) **dividendYield scale
     guard** — add a persisted assertion/fixture check so a future yfinance version reverting `dividendYield`
     to a fraction is caught (else a 100× error); (b) **ROA/ROE numerator asymmetry** — ROA uses total NI,
     statement ROE uses common NI; surface in the catalogue copy so beginners aren't confused that two
     "return" metrics use different income lines; (c) **period-end vs Yahoo-averaged denominators** — statement
     ROE/ROA/P-TBV use period-end balances, differing from Yahoo's scalars by design; add an applicability caveat.
6. **Slice 5 — AI assessment generator** (Python after dbt/export; Claude; store to Supabase; not-advice).
7. **Slice 6 — UI redesign** in Streamlit, consuming all of the above.

## Do NOT

- Commit/push `main`; `gh pr merge`. Agent commits need `gitleaks` on PATH (it is — WinGet Packages dir).
- Emit buy/sell/hold/price-target/advice anywhere — educational only.
- Reword OR AUTHOR metric copy/definitions/caveats without owner sign-off (§6) — bit us on #135.
- Add a catalogue row for a new metric before the Router — it renders an un-valued "—" cell.
- Hand-roll the plan-back in prose — use plan mode.
- Ask the owner cryptic/jargon questions — plain language, context, a recommendation, rarely.
- Use ROIC / Tier 1 / CET1 / NIM / NPL / ARR / multi-year metrics — yfinance can't source them (this is the
  real ceiling on the financials card; leave solvency honestly blank rather than fake it).
- Clip or hide outlier magnitudes — route to the correct lens.
- Compute from `info` scalars where a period-matched statement line exists — that's the shortcut #140 corrects.

## Context / open items

- **Review mechanics (keep — reused every slice):** active gate is the **plugin** `commit_review_gate.py`
  (no in-repo `.claude/hooks/git_discipline.py`, so it does NOT stand down). `diff_sha256` = `sha256(git diff
  --staged --no-renames --no-abbrev)`; get it via `commit_review_gate.py <plugin-root> --staged-hash`. Reviewer
  agents are NOT registered as subagent_types in this frontend — run them as **general-purpose** agents with the
  role `.md` inlined (definitions in the plugin `agents/` dir + `.claude/agents/equity-analyst-reviewer.md`).
  review.md + active_work.md are a **separate artifact-only commit** after the reviewed one.
- **New raw `stmt_*` field footprint (learned #140):** ingestion module/wiring + staging cast +
  staging/base/core yml docs + **`sources.yml` declaration** + **`scripts/audit_mart_vs_yfinance.py`
  `FUNDAMENTALS_COLUMNS`** + `seed_ci_raw_fixtures.py` + `data_contract.md`. The **two schema mirrors**
  (sources.yml + FUNDAMENTALS_COLUMNS) are easy to miss — the scope-auditor blocks on them (it did on #140).
- **yfinance canonicalises balance-sheet row labels** (camel2title of a fixed `const.py` key set) — labels do
  NOT vary by market (unlike the quarterly income statement). Single canonical label per line; only equity has a
  real alternate (`Stockholders Equity`/`Common Stock Equity`). Probe: `scripts/probe_balance_sheet_labels.py`.
- **Deferred hygiene (reviewer-flagged, out of #140 scope — do separately):**
  (a) `sources.yml` + `FUNDAMENTALS_COLUMNS` also omit the #135/#136 `info_*` data-only fields
  (`info_return_on_equity`, `info_current_ratio`, `info_price_to_book`, `info_price_to_sales`,
  `info_ev_to_ebitda`, `info_free_cashflow`, `info_market_cap`) — a pre-existing mirror gap, own cleanup PR.
  (b) `_numeric_columns`' `pd.Timestamp` sort is unguarded in BOTH `balance_sheet.py` and `quarterly.py` —
  optional try/except hardening (do both). (c) add a "first-wins when both equity labels present" unit test.
- **Test-architecture cleanup: PR'd, NOT merged** (branch `chore/test-architecture-cleanup`, commit `fa55d4d`;
  scope-auditor + cto PASS). Reorganized `tests/` into domain subdirs (`ingestion/`/`frontend/`/`tooling/`) +
  centralized `tests/conftest.py` (sys.path) + wrote the taxonomy (`tests/README.md` + `engineering_standards.md`
  §3 pointer). Behavior-preserving (pytest stays 80). **The seed→dbt / export→mart migration ideas were verified
  NON-issues** (seed already dbt-tested; export-health is a real pipeline gate) → not done. Optional deferred: 4
  non-empty seed tests + explicit not_null on mart metric cols (coverage; tiny future PR). Memory:
  `test-architecture-cleanup-planned`.
- Run dbt via the repo `.venv` (global dbt broken). `storage/raw` is gitignored — CI regenerates fixtures from
  `scripts/seed_ci_raw_fixtures.py`; **local raw = the CI fixture set (25 rows, all Technology → all
  `operating`)**, so financial/pre_revenue only surface on the full pipeline, not locally. Verify set: build +
  doc/layer/structure/sqlfluff + eligibility-baseline + export-health + pytest.
- **Backend (track B):** free-tier Supabase pauses after ~7 days idle → "Could not load cards" (real bug in
  `_ensure_all_cards`). Decide keep-alive vs paid tier.
- `docs/refresh-june-2026` is unrelated in-flight docs work (other chat) — leave it.
- **README/shopfront MERGED (#138).** Owner's manual steps may still be pending: `docs/media/swipe-demo.gif`
  (+ uncomment the README line) and an optional social-preview image (Settings → Social preview, 1280×640).
- Hygiene: `.venv/` is untracked and NOT gitignored — `git add -A` times out. Stage explicit paths, or add
  `.venv/` to `.gitignore` in a future PR.
- Keep this handover current after each PR.
