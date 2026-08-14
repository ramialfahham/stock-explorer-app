# Active work — handover

_The next session is handed exactly this file. Keep it current._

## Current task

**Reshaping the dashboard into a beginner financial-literacy tool** — sector-aware metrics + AI "reads"
+ a health verdict. The keystone is the **Sector/Lifecycle Router**, built in slices. This session
brought a **major correction — "do it right":** compute from **period-matched financial statements,
not Yahoo `info` scalar shortcuts**, and design per-type metric sets from an explicit **metric-assignment
matrix** (below). **Slices 1–2b are all MERGED** (#139 classifier · #140 balance sheet · #141 statements)
— **the entire raw data foundation is in.** Slice 3 (the compute) is built in two PRs: **Slice 3a
(statement enrichment) MERGED (#142)** and **Slice 3b (per-type metric compute) MERGED (#143).** The
test-architecture cleanup (#144) also merged. **The Sector/Lifecycle Router (Slices 4a #145 · 4b #146 · 4c #147)
is fully MERGED — feature-complete.** Work has moved to **Slice 5 — the AI assessment generator**, split into
**5a (deterministic health verdict + storage, no LLM) — PR'd (awaiting merge)** and **5b (the Claude-written prose
read)**; then **Slice 6 (UI redesign)** renders it. The most recent session built Slice 5a: a per-type 🟢/🟡/🔴
financial-health verdict from deterministic rules + a new `card_assessments` Supabase table + pipeline wiring —
see Status + Next actions.

## Infra: GitHub → GitLab migration (separate track, not a product slice)

**Why this exists:** the GitHub account (`ramialfahham`) got suspended mid-session
(2026-08-14) — `git fetch`/`push`/`gh api` all 403 "Your account was suspended." Slice 5a's
PR has nowhere to be merged until either GitHub is restored or the repo moves. Ran
`/migrate-to-gitlab` at the owner's direction as a result; this is orthogonal to the
Sector Router / AI-assessment work below and does **not** change Slice 5b's plan.

**State:** `.gitlab-ci.yml` + `tests/tooling/test_ci_reachability.py` written, all three
reachability pins verified to fail against their deliberately-broken forms before being
kept (see commit `7ce0c78` on `chore/migrate-to-gitlab`, branched off `main` @ `0f182f7`).
Docs swept (README, CLAUDE.md, `docs/operations_guide.md`, `supabase_setup.md`,
`development_workflow.md`, `project_context.md`, `data_contract.md`, `market_registry.yml`,
two script docstrings) for now-stale GitHub Actions references — historical
`docs/handover_2026-05-24.md` deliberately left alone (point-in-time record).

New private GitLab project created: `rami.al-fahham/stock-swipe-app`
(https://gitlab.com/rami.al-fahham/stock-swipe-app). `main` pushed **before** the feature
branch (trap 9 — branch protection attaches to whichever ref arrives first, not to the
name "main"); confirmed via `protected_branches` API that `main` is the protected one
(Maintainer push/merge, no force-push), not the feature branch. MR #1 open:
https://gitlab.com/rami.al-fahham/stock-swipe-app/-/merge_requests/1.

**Blocked on:** the MR's own pipeline (`#2759956276`) failed instantly on all three jobs
with `failure_reason: "ci_quota_exceeded"` — the account's Free-plan shared-runner CI
minutes are exhausted (likely by the other two projects in this namespace:
`backtobayesics`, `football-data-pipeline`). This is **not** a `.gitlab-ci.yml` defect —
`workflow:` rules and the MR trigger fired correctly; no job ever got a runner. Confirmed
zero CI/CD variables are configured yet (`GET .../variables` → `[]`), which is expected —
I never had read access to the GitHub secret values.

**Owner-only, not decided:**
- CI minutes: buy more on the Free plan, or point this project at an existing self-hosted
  runner (`self-hosted-runner.md` in the skill) instead of GitLab's shared runners.
- Streamlit Community Cloud only deploys from GitHub — **the live app
  (stock-explorer.streamlit.app) has no deploy path from the new GitLab repo.** Options:
  keep a GitHub mirror alive just for Streamlit, or find another host. Not solved here.
- `dbt-agent-kit` (github.com/ramialfahham/dbt-agent-kit, the guardrail plugin this repo
  depends on) was **not** migrated — out of scope, and also currently unreachable (same
  account suspension). Links to it in this repo's docs were deliberately left pointing at
  GitHub.
- Repo visibility: created **private** by default (unlike the two public sibling repos) —
  flip it if that's wrong; this repo's docs reference production secret names.
- CI/CD variable values themselves (Supabase creds, `ANTHROPIC_API_KEY`) — names only in
  `docs/operations_guide.md` / `supabase_setup.md`, never values.
- Whether/when to restore `main` branch protection expectations once GitHub access (if
  ever restored) makes the old repo relevant again — two remotes now exist for a while.

**Next concrete action:** owner reviews MR #1, resolves CI-minutes (buy vs. self-hosted
runner), sets the CI/CD variables listed in `operations_guide.md`, creates the Mon 06:00
UTC pipeline schedule (project config — can't be committed), decides the Streamlit
question, then merges. Re-run the pipeline after variables exist to actually exercise
`supabase-migrate` / `data-pipeline` — neither has run yet.

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
- **Sector Router — Slice 3b (per-type metric compute) MERGED (#143).** 13 data-only computed columns
  in `int_stock__card_metrics` (debt_to_equity, interest_coverage [abs-guarded], current_ratio_stmt,
  working_capital, price_to_tangible_book, net_margin_pct, roa_pct, statement_roe_pct, dividend_yield_pct,
  computed_fcf, cash_runway_months, burn_rate_monthly, net_cash_to_ev) + 4 unit tests. Coexist with the
  info-scalars; eligibility/mart/export untouched (baseline 25, export 100%).
- **Sector Router — Slice 4a (Router mechanism + grown operating card) MERGED (#145).**
  Per-type display via a catalogue `applies_to` column → `frontend/card_copy.metrics_for_card(card, tier)`
  (renders a metric only when `company_type ∈ applies_to` AND value non-null → omit, never `—`). `company_type`
  + the 3 new operating metric VALUES (`debt_to_equity`, `current_ratio_stmt`, `statement_roe_pct`) carried
  int → mart → Supabase (migration `007_router_card_columns.sql`, export, `data_contract.md`). Operating card
  grown 5 → 8 (adds solvency-complement `debt_to_equity`, liquidity `current_ratio_stmt`, returns
  `statement_roe_pct`; owner-signed copy). **Eligibility untouched — five-metric AND stays, baseline 25.**
  Full 5-reviewer cycle all-PASS (3 cycles); dbt PASS=102, pytest 88. Deferred to 4b: value-aware
  negative-equity gloss for debt/equity + ROE (caveat already warns).
- **Sector Router — Slice 4b (financial/bank card + per-type eligibility) MERGED (#146).**
  4 bank metrics catalogued (`price_to_tangible_book`, `net_margin_pct`, `roa_pct`, `dividend_yield_pct`;
  `applies_to = financial`; owner-signed copy incl. the ROA/ROE numerator-asymmetry caveat); operating-only
  metrics narrowed off banks; `statement_roe_pct` extended to `operating|financial`. **Eligibility reworked to a
  per-type `CASE company_type`** (financial = `forward_pe + statement_roe_pct + net_margin_pct`; operating/
  pre_revenue keep the 5-AND) — the **first eligible-pool change** (5 assumption sites updated incl. 2 stale
  LLOY/HSBA unit tests). Values carried int → mart → Supabase (migration `008`). `metrics_for_card` now
  lens-sorts (bank card lens-grouped; operating byte-identical). Synthetic bank fixture per market → **CI
  baseline 25 → 30**; dividendYield scale-guard unit test. dbt PASS=104, pytest 91. Full 5-reviewer cycle all-PASS.
- **Sector Router — Slice 4c (pre-revenue/survival card + per-type benchmarks) MERGED (#147).**
  4 survival metrics catalogued (`net_cash_to_market_cap`, `working_capital`, `cash_runway_months`,
  `burn_rate_monthly`; `applies_to = pre_revenue`; owner-signed copy) + a **pre_revenue eligibility branch**
  (gates on `net_cash_to_market_cap is not null` → 3-branch `CASE company_type`; pre-revenue companies now enter
  the pool, **CI baseline 30 → 35**). New **`currency_compact`** display format ($/£/¥/€/A$, B/M/K) for the two
  dollar amounts. **`net_cash_to_ev` → `net_cash_to_market_cap`** (owner-approved §6 switch: the EV denominator
  sign-flips when net cash exceeds EV, contradicting higher_better; market cap is monotonic — `net_cash_to_ev`
  reverts to data-only). **`pre_revenue` excluded from `int_stock__sector_benchmarks` peers AND the mart benchmark
  join** (a pre-revenue card never shows a peer-count it isn't in). Synthetic pre_revenue Healthcare fixture;
  values carried int → mart → Supabase (migration `009`). dbt PASS=105, pytest 95, baseline 35. **Full 5-reviewer
  cycle, 4 rounds → all-PASS** (rounds 1–3 caught the metric sign-flip, the benchmark pollution, and an incomplete
  doc-sweep of the rename + the company_type-drives-eligibility fact; all fixed and re-verified).
- **Slice 5a (AI assessment — deterministic health verdict + storage, no LLM) PR'd (awaiting merge).**
  New pure `scripts/assessment_rules.py` — a per-type 🟢/🟡/🔴 **financial-health** verdict decided by
  deterministic rules (NOT the LLM): operating on leverage/profitability/cash, financial on ROE/margin/ROA
  (profitability-only — capital adequacy unsourceable from yfinance), pre_revenue on runway/net-cash/working-capital;
  conservative worst-axis-wins; **excludes valuation + growth** (no disguised buy signal). Stored to a new Supabase
  table **`card_assessments`** (migration `010`, RLS public read) with an `input_hash` (float-canonical) for 5b's
  regenerate-on-change; `ai_read`/`read_model` are null in 5a and omitted from the upsert so 5b can't be clobbered.
  `scripts/generate_assessments.py` (mirrors export) runs after export in the weekly pipeline + a no-secret CI
  dry-run smoke. **No `anthropic` dep, no API key, no cost.** pytest 117 (22 new); generator dry-run 35 cards.
  **Full 5-reviewer cycle, single round → all-PASS.**
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
`~/.claude/plans/logical-roaming-brook.md` (Slice 3a/3b: enrichment + compute);
`~/.claude/plans/dynamic-snuggling-truffle.md` (Slice 4a: mechanism + grown operating card). Don't land it in one PR.

1. **Slice 1 — company-type classifier: MERGED (#139).**
2. **Slice 2 — balance-sheet foundation: MERGED (#140).**
3. **Slice 2b — statement completion: MERGED (#141).**
4a. **Slice 3a — statement enrichment: MERGED (#142).** 2 raw fields (`stmt_total_assets`, `stmt_net_income_common`).
4b. **Slice 3b — per-type metric compute: MERGED (#143).** Built (data-only) in
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
5a. **Slice 4a — Router mechanism + grown operating card: MERGED (#145).** `applies_to` catalogue
   column → `card_copy.metrics_for_card(card, tier)` (render iff `company_type ∈ applies_to` AND value non-null →
   omit, never `—`); `company_type` + the 3 operating metric VALUES carried int → mart → Supabase
   (`007_router_card_columns.sql` + export + `data_contract.md`); operating grown 5 → 8 (`debt_to_equity`,
   `current_ratio_stmt`, `statement_roe_pct`; owner-signed copy). Eligibility untouched (five-metric AND,
   baseline 25). Plan: `~/.claude/plans/dynamic-snuggling-truffle.md`.
   - **Mechanism notes for 4b/4c:** the 5 existing metrics carry `applies_to = operating|financial|pre_revenue`
     (parity — **narrow them per-type in 4b/4c**); new metrics are DISPLAY-ONLY (not in the eligibility gate);
     frontend read is `select("*")` (auto-carries new Supabase columns — but the mart SELECT + `EXPORT_COLUMNS`
     + migration + `data_contract.md` are explicit); `applies_to` is pipe-delimited (`_seeds.yml` not_null +
     `test_metric_catalogue` subset check — `accepted_values` can't validate a compound cell); mart is
     SELECT-only, metrics computed once in `int_stock__card_metrics`.
5b. **Slice 4b — financial/bank card + per-type eligibility: MERGED (#146).** 4 bank metrics
   catalogued (P/TBV, net_margin, roa, dividend_yield; owner-signed copy incl. the ROA/ROE asymmetry + period-end
   caveats + a dividendYield scale-guard unit test); operating-only metrics narrowed off banks; per-type
   eligibility `CASE` (financial core three = forward_pe + statement_roe_pct + net_margin_pct); bank fixture →
   baseline 25 → 30; `metrics_for_card` lens-sort. **EV/EBITDA & P/B financial caveats were moot** (banks use
   statement P/TBV, not those info-scalars). Value-aware negative-equity gloss for debt/equity + ROE still
   deferred (caveat already warns). Owner **kept the P/E-based bank gate** (declined the P/TBV swap).
5c. **Slice 4c — pre-revenue/survival card: MERGED (#147).** 4 survival metrics catalogued
   (`net_cash_to_market_cap`, `working_capital`, `cash_runway_months`, `burn_rate_monthly`; owner-signed copy);
   pre_revenue eligibility branch (3-branch `CASE`, gates on `net_cash_to_market_cap`); `currency_compact` format;
   pre_revenue excluded from sector benchmarks (peer CTE + mart join); synthetic pre_revenue fixture (baseline
   30 → 35); migration `009`. Owner-approved §6 switch **`net_cash_to_ev` → `net_cash_to_market_cap`** (EV
   denominator sign-flips when net cash > EV; market cap is monotonic — `net_cash_to_ev` now data-only). 4-round
   review → all-PASS. Deferred (owner, out of 4c): the pre-existing "all five" / "data-only" doc boilerplate on
   now-catalogued metrics across `_intermediate.yml` + `data_contract.md` + `overflow_menu.py`/README/north_star.
6. **Slice 5 — AI assessment generator** (split 5a/5b; owner decisions: rules decide the verdict color / LLM
   writes prose only; generate-and-store data-only; Claude Haiku + regenerate-on-change).
   - **5a — deterministic verdict + `card_assessments` storage: PR'd (awaiting merge).** `assessment_rules.py`
     (per-type health verdict + `input_hash`), migration `010`, `generate_assessments.py`, pipeline + CI smoke,
     tests, `data_contract.md` §card_assessments. No LLM/dep/key/cost. Owner-signed per-type verdict rubric.
   - **5b (← START HERE) — the Claude read.** Add `anthropic` + `ANTHROPIC_API_KEY` secret; an owner-signed
     per-type prompt/voice (the beginner "read": reason only from the numbers, end on the verdict's meaning —
     "financially sturdy on these figures", never "a good buy"); the Haiku call gated on `input_hash` change
     (read the existing row, regenerate only when changed); fill `ai_read`/`read_model`; offline test mocking the API.
     Plan: repurpose `~/.claude/plans/dynamic-snuggling-truffle.md` (currently holds the 5a plan).
7. **Slice 6 — UI redesign** in Streamlit, consuming all of the above (the approved mock: cohesive card,
   scan→deep tiers, one disclosure, label chips, words-not-arrows).

## Do NOT

- Commit/push `main`; `gh pr merge`. Agent commits need `gitleaks` on PATH (it is — WinGet Packages dir).
- (GitLab migration) Don't buy CI minutes, register a self-hosted runner, set CI/CD variable
  *values*, or touch protected-branch settings — all owner-only (§6 cost/config). Don't merge
  MR #1 — same rule as GitHub PRs, the owner merges. Don't assume GitHub is gone for good;
  don't delete the GitHub remote or repo.
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
- **Test-architecture cleanup: MERGED (#144).** Reorganized `tests/` into domain subdirs (`ingestion/`/`frontend/`/`tooling/`) +
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
