# Active work — handover

_The next session is handed exactly this file. Keep it current._

## Current task

**Project evaluation → redesign.** Owner's lead complaint was a cluttered/inconsistent UI; digging in
revealed the bigger truth: **it's a dashboard, not a learning tool.** The work now is reshaping the
product into a beginner **financial-literacy** tool — sector-aware metrics + AI-written, plain-language
"reads" with a health verdict — on top of the metric layer we built. In flight: **adding the new
sector-aware metrics, data-only**. Done so far: ROE (#135 merged) + four ratios (#136 open). Remaining
data-only: FCF yield, cash runway. Then the **Sector Router**.

## Status

- **Metric layer: Phases 1 + 2 MERGED** (#131, #132). `metric_catalogue` seed = single source →
  `metrics.json` → `card_copy.py`; dbt model is the only place metrics compute.
- **equity-analyst-reviewer: MERGED** (#133). Finance-domain blinded reviewer.
- **Catalogue enrichment: MERGED** (#134). `metric_group → perspective`; added
  `calculation`/`interpretation`/`applicability`; 5 existing metrics populated; 7-value perspective taxonomy.
- **ROE (data-only): MERGED** (#135). `roe_pct = info_return_on_equity * 100` computed in
  `int_stock__card_metrics`; not carded/catalogued/gated/exported.
- **Ratio metrics (data-only): PR OPEN — [#136](https://github.com/ramialfahham/stock-swipe-app/pull/136)**
  (branch `feat/ratio-metrics-data`). `current_ratio`, `price_to_book`, `price_to_sales`, `ev_to_ebitda`
  — Yahoo `info` passthroughs (no ×100; they're ratios), keys verified live on AAPL. Same data-only
  pattern as #135. Verified (dbt build 90; doc/layer/structure/sqlfluff; eligibility 25 + export 100%
  unchanged; pytest 73; card byte-identical). Review: scope + analytics + data-eng + cto + equity-analyst
  all PASS. `data_contract.md` kept strictly factual (no §6 copy).
- **UI redesign mock: approved look** (one cohesive card, scan→deep tiers, one disclosure pattern,
  label chips for basis, words-not-arrows benchmarks). NOT yet implemented — waits on the metric model.

## Decisions locked this session (the important ones)

- **Stay on yfinance** (no paid data source). Use **ROE not ROIC**; financials get **ROE + P/B + margin**;
  pre-revenue get **cash runway**. (Yahoo `info` verified: returnOnEquity, currentRatio, priceToBook,
  priceToSalesTrailing12Months, enterpriseToEbitda all present.)
- **Outlier magnitudes are REAL data, not corrupt** — mis-applied to the wrong company type. **Do not
  clip/hide** — route to the right lens. Applicability is a first-class property of a metric.
- **Cataloguing a metric currently RENDERS it** (catalogue → metrics.json → `card_copy.ALL_METRICS` →
  `card_ui`). So new metrics land **data-first** (compute in dbt, NO catalogue row) until the Router owns
  cataloguing + display + per-sector eligibility. **Do not add a catalogue row for a new metric before
  the Router.**
- **Authoring metric copy/caveats is §6** (not just rewording) — a self-authored ROE caveat was flagged by
  the scope-auditor on #135 and reverted. New metric wording is owner-approved + quoted in the contract;
  data-only PRs keep `data_contract.md` strictly factual (field = Yahoo key).
- **Use the plan-mode Explore→Plan→Execute spine** (EnterPlanMode → ExitPlanMode). The dbt-agent-kit
  `plan_implement_gate` hooks on `ExitPlanMode`; hand-rolling a prose plan-back skips that gate. #136 ran
  through it correctly (plan file → approval → implement-gate checklist).
- **Architecture: a Sector/Lifecycle Router** — operating / financial / pre-revenue — each with its metric
  set, eligibility, rendering, AI prompt. **Perspective taxonomy:** valuation · profitability · growth ·
  solvency · liquidity · cash · returns.
- **AI assessments:** educational, **NEVER advice**; true-beginner language; reason only from the given
  numbers; end with a health verdict (🟢/🟡/🔴).

## Next concrete actions (in order)

1. **Finish the data-only metrics:** **FCF yield** (compute `freeCashflow / marketCap` → needs a new
   `marketCap` raw field) and **cash runway** (compute; pre-revenue-specific → likely do **with the
   Router**, which supplies the lifecycle classification). Pattern = ROE/#136 (~10 files: ingestion +
   staging/core columns + int compute + 4 layer-yml docs + unit test + CI fixture + data_contract note).
   (Also still pending from the metric plan: **debt-to-equity + interest coverage**, the brittle
   net-debt/EBITDA fix — near/with the Router.)
2. **Sector/Lifecycle Router** — classify company type → per-sector metric set + eligibility + rendering +
   AI prompt. **Where the data-only metrics get catalogue rows + owner-approved applicability copy +
   display.** Needs an eligibility rework (today's all-five-required gate won't fit sector-varying sets).
3. **AI assessment generator** (Python step after dbt/export; Claude; store to Supabase; not-advice).
4. **UI redesign** implemented in Streamlit, consuming all of the above.

## Do NOT

- Commit/push `main`; `gh pr merge`. Agent commits need `gitleaks` on PATH (export from the WinGet
  Packages dir if a commit hook can't find it).
- Emit buy/sell/hold/price-target/advice anywhere — the app and the AI reads are educational only.
- **Reword OR AUTHOR metric copy/definitions/caveats without owner sign-off (§6)** — bit us on #135.
- Add a catalogue row for a new metric before the Router — it would render an un-valued "—" cell on every card.
- Hand-roll the plan-back in prose — use plan mode (EnterPlanMode/ExitPlanMode) so the plan→implement gate fires.
- Use ROIC / Tier 1 / NIM / ARR / multi-year metrics — yfinance can't source them reliably.
- Clip or hide outlier magnitudes — route to the correct lens instead.

## Context / open items

- Run dbt via the repo `.venv` (global dbt is broken). For seed/schema column changes use
  `dbt --no-partial-parse ... --full-refresh`. Local profile writes to `storage/stock_data.db`.
  `storage/raw` is gitignored — CI regenerates fixtures from `scripts/seed_ci_raw_fixtures.py`.
- A data-only metric touches ~10 files because of the doc gate (every model output column needs a
  description) + the CI fixture generator.
- **Backend (track B):** free-tier Supabase pauses after ~7 days idle → repeated "Could not load cards"
  (a real bug in `_ensure_all_cards`). Decide keep-alive vs paid tier.
- `docs/refresh-june-2026` is unrelated in-flight docs work (other chat) — leave it.
- Keep this handover current after each PR.
