# Active work — handover

_The next session is handed exactly this file. Keep it current._

## Current task

**Reshaping the dashboard into a beginner financial-literacy tool** — sector-aware metrics + AI "reads"
+ a health verdict. The keystone is the **Sector/Lifecycle Router**, built in slices. This session
brought a **major correction — "do it right":** compute from **period-matched financial statements,
not Yahoo `info` scalar shortcuts**, and design per-type metric sets from an explicit **metric-assignment
matrix** (below). Slice 1 (the `company_type` classifier) is **MERGED (#139)**; Slice 2 (the
balance-sheet ingestion foundation — the missing third statement) is **PR OPEN
[#140](https://github.com/ramialfahham/stock-swipe-app/pull/140)**.

## Status

- **Metric layer + all data-only `info_*` metrics MERGED** (#131–137: ROE, four ratios, FCF yield —
  computed in `int_stock__card_metrics`, still nothing rendered).
- **Sector Router — Slice 1 (`company_type` classifier) MERGED (#139).** `financial` (info_sector =
  'Financial Services'), `pre_revenue` (stmt_total_revenue present & ≤ 0; null → operating), else `operating`.
- **Sector Router — Slice 2 (balance-sheet ingestion foundation) PR OPEN
  [#140](https://github.com/ramialfahham/stock-swipe-app/pull/140)** (branch `feat/balance-sheet-ingestion`).
  6 raw balance-sheet lines landed **data-only**: `stmt_stockholders_equity`, `stmt_total_debt`,
  `stmt_current_assets`, `stmt_current_liabilities`, `stmt_cash_and_equivalents`, `stmt_tangible_book_value`.
  New module `ingestion/yfinance/balance_sheet.py` (mirrors `quarterly.py`; point-in-time, latest annual, no
  TTM). Verified (build 93; all gates; eligibility 25 + export 100% unchanged; pytest 80). **5-reviewer cycle
  all PASS** (it caught real defects — see below).
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

Approved plan: `~/.claude/plans/noble-forging-beaver.md` (the "do it right" version + the matrix). Don't land
it in one PR.

1. **Slice 1 — company-type classifier: MERGED (#139).**
2. **Slice 2 — balance-sheet ingestion foundation: PR OPEN [#140](https://github.com/ramialfahham/stock-swipe-app/pull/140).** (Merge, then continue.)
3. **Slice 2b — complete the statements (data-only).** Cash flow: land **Operating Cash Flow + Capital
   Expenditure** (dbt computes FCF = OCF − capex, replacing the `info.freeCashflow` scalar). Income: **Interest
   Expense + Net Income**. `info`: **dividendYield, payoutRatio**. Cheaper than #140 — income/cashflow are
   already fetched; mirror the `stmt_*` footprint (incl. the two schema mirrors — see Context).
4. **Slice 3 — compute the correct per-type metrics, DATA-ONLY, from the statements.** `debt_to_equity`,
   `interest_coverage` (operating); current ratio + working capital (from BS); tangible book /
   `price_to_tangible_book` (P/TBV, financials); computed FCF; `cash_runway` (pre-revenue, from OCF/FCF burn);
   `dividend_yield`. **§6 owner confirmations here:** the equity (excl. minority interest) + cash (narrow)
   definitional choices baked into #140; the cash-runway definition (units + burn basis); whether to re-probe
   the full universe before computing (the #140 probe was n=5/market).
5. **Slice 4 — the Router mechanism.** Per-type metric sets (the matrix); **eligibility rework** (the hardcoded
   five-metric AND in `int_stock__card_metrics.sql:156-177` can't express sector-varying sets — likely a
   per-type required-set config); carry `company_type` into `mart_stock_cards`; per-type `card_ui`/`card_copy`
   display; **catalogue rows + owner-approved applicability/beginner copy**; recalibrate the eligibility
   baseline. Sub-split operating (parity) → financial → pre-revenue.
   - **Copy the Router must author (§6, reviewer-flagged):** ROE (negative/thin equity → spuriously positive;
     breaks for financials); **FCF yield — NEGATIVE for cash-burners** (#137 flag); EV/EBITDA & P/B financials
     caveats.
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
