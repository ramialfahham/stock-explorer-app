# Active work — handover

_The next session is handed exactly this file. Keep it current._

## Current task

**Project evaluation → redesign.** Owner's lead complaint was a cluttered/inconsistent UI; digging in
revealed the bigger truth: **it's a dashboard, not a learning tool.** The work is reshaping it into a
beginner **financial-literacy** tool — sector-aware metrics + AI-written plain-language "reads" with a
health verdict. The straightforward **data-only metrics are now essentially done** (ROE #135, four ratios
#136, FCF yield #137-open). **The clear next step is the Sector/Lifecycle Router** — it's what turns all
this inert metric data into per-company-type, displayed, owner-copy'd value.

## Status

- **Metric layer Phases 1+2 MERGED** (#131, #132); **equity-analyst-reviewer MERGED** (#133);
  **catalogue enrichment MERGED** (#134, `metric_group → perspective` + calculation/interpretation/
  applicability + 7-value taxonomy).
- **Data-only metrics (computed in `int_stock__card_metrics`, nothing rendered yet):**
  - **ROE MERGED** (#135) — `roe_pct = info_return_on_equity * 100`.
  - **Ratios MERGED** (#136) — `current_ratio`, `price_to_book`, `price_to_sales`, `ev_to_ebitda` (Yahoo info passthroughs).
  - **FCF yield PR OPEN — [#137](https://github.com/ramialfahham/stock-swipe-app/pull/137)** (branch
    `feat/fcf-yield-data`). `fcf_yield_pct = info_free_cashflow / info_market_cap * 100`, guarded division;
    owner chose Yahoo **trailing** `freeCashflow` / current `marketCap` (period-matched) — a 2nd FCF source
    vs the annual `stmt_free_cash_flow` used by `fcf_margin_pct`, documented factually. Verified (build 90;
    all gates; eligibility 25 + export 100% unchanged; pytest 73; card byte-identical). 5-reviewer cycle all PASS.
- **UI redesign mock: approved look** (one cohesive card, scan→deep tiers, one disclosure pattern, label
  chips for basis, words-not-arrows benchmarks). NOT implemented — waits on the Router + metric model.

## Decisions locked (the important ones)

- **Stay on yfinance.** Use ROE not ROIC; financials get ROE + P/B + margin; pre-revenue get cash runway.
- **Outlier magnitudes are REAL data** (mis-applied to the wrong company type). **Do not clip/hide** —
  route to the right lens. Applicability is a first-class property of a metric.
- **Cataloguing a metric currently RENDERS it** (catalogue → metrics.json → card_copy → card_ui). So new
  metrics land **data-first** (compute, NO catalogue row) until the Router owns cataloguing + display +
  per-sector eligibility. **Don't add a catalogue row before the Router** (it would render an empty "—").
- **Authoring metric copy/caveats is §6** (not just rewording). Data-only PRs keep `data_contract.md`
  strictly factual; the Router authors the owner-approved applicability/beginner copy.
- **Use the plan-mode Explore→Plan→Execute spine** (EnterPlanMode → ExitPlanMode → plan_implement_gate).
  Do NOT hand-roll a prose plan-back. (Also: ask the owner in PLAIN language, with context + a clear
  recommendation, and sparingly — see the `ask-questions-plain-language` memory.)
- **Architecture: a Sector/Lifecycle Router** — operating / financial / pre-revenue, each with its metric
  set, eligibility, rendering, AI prompt. **Perspective taxonomy:** valuation · profitability · growth ·
  solvency · liquidity · cash · returns.
- **AI assessments:** educational, NEVER advice; true-beginner language; reason only from the given numbers;
  end with a health verdict (🟢/🟡/🔴).

## Next concrete actions (in order)

1. **Sector/Lifecycle Router (the keystone).** Classify each company → operating / financial / pre-revenue
   (from `info_sector` + signals like revenue≈0 → pre-revenue). Then per type: the metric set, an
   **eligibility rework** (today's all-five-required gate can't express sector-varying sets), rendering,
   and the AI prompt. **This is where the data-only metrics (ROE, the four ratios, FCF yield) get their
   catalogue rows + owner-approved applicability copy + display.** Big step with real §6 calls (per-sector
   metric sets, classification rules) — run it through plan mode and escalate the owner decisions.
   - Fold in here: **cash runway** (pre-revenue-specific; needs the lifecycle classification) and the
     brittle-metric fix **debt-to-equity + interest coverage** (per-sector solvency, replacing net-debt/EBITDA).
   - **Applicability copy the Router MUST author** (reviewer flags, deferred): ROE — distorted by
     negative/thin equity (spuriously positive) + leverage/DuPont, breaks for financials; **FCF yield — can
     be NEGATIVE for cash-burners** (equity-analyst flag on #137); EV/EBITDA & P/B — financials caveats.
2. **AI assessment generator** (Python step after dbt/export; Claude; store to Supabase; not-advice).
3. **UI redesign** in Streamlit, consuming all of the above.

## Do NOT

- Commit/push `main`; `gh pr merge`. Agent commits need `gitleaks` on PATH (export from the WinGet Packages dir).
- Emit buy/sell/hold/price-target/advice anywhere — educational only.
- Reword OR AUTHOR metric copy/definitions/caveats without owner sign-off (§6) — bit us on #135.
- Add a catalogue row for a new metric before the Router — it renders an un-valued "—" cell on every card.
- Hand-roll the plan-back in prose — use plan mode so the plan→implement gate fires.
- Ask the owner cryptic/jargon questions — plain language, context, a recommendation, and rarely.
- Use ROIC / Tier 1 / NIM / ARR / multi-year metrics — yfinance can't source them reliably.
- Clip or hide outlier magnitudes — route to the correct lens instead.

## Context / open items

- Run dbt via the repo `.venv` (global dbt is broken). Seed/schema column changes: `dbt --no-partial-parse
  ... --full-refresh`. Local profile writes to `storage/stock_data.db`. `storage/raw` is gitignored — CI
  regenerates fixtures from `scripts/seed_ci_raw_fixtures.py`. A data-only metric ≈ 10 files (doc gate +
  fixtures). Verify set: build + doc/layer/structure/sqlfluff + eligibility-baseline + export-health + pytest.
- **Backend (track B):** free-tier Supabase pauses after ~7 days idle → repeated "Could not load cards"
  (a real bug in `_ensure_all_cards`). Decide keep-alive vs paid tier.
- `docs/refresh-june-2026` is unrelated in-flight docs work (other chat) — leave it.
- Keep this handover current after each PR.
