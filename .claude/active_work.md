# Active work — handover

_The next session is handed exactly this file. Keep it current._

## Current task

**Project evaluation → redesign.** Owner's lead complaint was a cluttered/inconsistent UI; digging in
revealed the bigger truth: **it's a dashboard, not a learning tool.** The work now is reshaping the
product into a beginner **financial-literacy** tool — sector-aware metrics + AI-written, plain-language
"reads" with a health verdict — on top of the metric layer we built. In flight: **adding the new
sector-aware metrics**, starting with **ROE (data-only)** — PR #135 open.

## Status

- **Metric layer: Phases 1 + 2 MERGED** (#131, #132). `metric_catalogue` seed = single source →
  `metrics.json` → `card_copy.py`; dbt model is the only place metrics compute; no Python mirror.
- **equity-analyst-reviewer: MERGED** (#133). Finance-domain blinded reviewer; routing sends
  `*metric_catalogue.csv`, `docs/metric_layer.md`, `docs/data_contract.md` to it.
- **Catalogue enrichment: MERGED** (#134). Renamed `metric_group → perspective`
  (quality→profitability, momentum→growth); added `calculation` / `interpretation` / `applicability`;
  populated the 5 existing metrics. Seed `perspective` accepts the full 7-value taxonomy
  (valuation · profitability · growth · solvency · liquidity · cash · returns).
- **ROE (data-only): PR OPEN — [#135](https://github.com/ramialfahham/stock-swipe-app/pull/135)**
  (branch `feat/roe-metric-data`). Raw `info_return_on_equity ← returnOnEquity` flows
  ingestion → staging → base → core; `roe_pct = info_return_on_equity * 100` computed once in
  `int_stock__card_metrics`. **Data-only**: NOT in eligibility, the catalogue, `metrics.json`, the card,
  or the Supabase export — ROE's cataloguing / display / per-sector eligibility / applicability copy are
  deferred to the Router. Verified (dbt build 90; doc/layer/structure/sqlfluff gates; eligibility 25 +
  export 100% unchanged; pytest 73; `roe_pct=18.0` end-to-end; card byte-identical). Review:
  scope-auditor + analytics-engineer + data-engineer + cto PASS; equity-analyst ESCALATE → owner DEFER.
- **UI redesign mock: approved look** (one cohesive card, scan→deep tiers, one disclosure pattern,
  label chips for basis, words-not-arrows benchmarks). NOT yet implemented — waits on the metric model.

## Decisions locked this session (the important ones)

- **Stay on yfinance** (no paid data source). Accept its limits: no ROIC / Tier 1 / Net Interest Margin /
  ARR / multi-year history. Use **ROE not ROIC**; financials get **ROE + P/B + margin**; pre-revenue get
  **cash runway**. (Verified in yahoo `info`: returnOnEquity, priceToBook, profitMargins, marketCap,
  freeCashflow present everywhere incl. banks; debtToEquity/currentRatio/EV missing-or-garbage for financials.)
- **The nonsense magnitudes are REAL data, not corrupt** — metrics mis-applied to the wrong company type
  (financials, pre-revenue, loss-makers, near-zero denominators). **Do not clip/hide** — route to the
  right lens. Applicability is a first-class property of a metric (now a catalogue column).
- **Cataloguing a metric currently RENDERS it** (catalogue → metrics.json → `card_copy.ALL_METRICS` →
  `card_ui` renders a cell for every metric, value or "—"; `test_frontend_metrics_match_catalogue` forces
  ALL_METRICS == catalogue ids). So new metrics land **data-first** (compute in dbt, NO catalogue row)
  until the Router owns cataloguing + display + per-sector eligibility. Catalogue rows for new metrics
  wait for the Router.
- **ROE shipped data-only** (#135): `roe_pct` computed, not displayed/catalogued/gated/exported. ROE's
  applicability copy (negative-equity → spuriously positive ROE; leverage/DuPont; breaks-for-financials)
  **deferred to the Router** with owner sign-off there. (A one-line caveat was added mid-review then
  reverted — owner chose DEFER; authoring metric wording is §6 and belongs with the Router's copy work.)
- **Architecture: a Sector/Lifecycle Router** — operating company / financial / pre-revenue — each with
  yfinance-available metrics, its own eligibility, rendering, and AI prompt.
- **Perspective taxonomy:** valuation · profitability · growth · solvency · liquidity · cash · returns.
  Two perspectives still to USE with the new metrics: **Returns (ROE)** and **Liquidity (current ratio)**;
  fix brittle metrics (net-debt/EBITDA → **debt-to-equity + interest coverage**; P/E + loss-proof
  **P/S, EV/EBITDA, FCF yield**).
- **AI assessments:** educational, **NEVER advice** (no buy/sell/price-target); true-beginner language;
  reason only from the given numbers; end with a financial-health verdict (🟢/🟡/🔴).

## Next concrete actions (in order)

1. **Remaining new metrics, data-only** (same pattern as ROE #135): current ratio, P/B, P/S, EV/EBITDA,
   FCF yield, cash runway — raw fields (yahoo info: `currentRatio`, `debtToEquity`, `priceToBook`,
   `marketCap`, `sharesOutstanding`) + dbt compute in `int_stock__card_metrics`. NO catalogue rows /
   display / eligibility yet. Each field ≈ ~11 files: ingestion `INFO_FIELDS` + staging cast + core select
   + compute + **4 layer-yml column docs** (doc gate requires every output column documented) + a unit
   test + the CI fixture (`seed_ci_raw_fixtures.py`; `storage/raw` is gitignored, regenerated each CI run)
   + a `data_contract.md` note.
2. **Sector/Lifecycle Router** — classify company type → per-sector metric set + eligibility + rendering +
   AI prompt. **This is where the new metrics get catalogue rows + owner-approved applicability copy +
   display** (cataloguing renders, so it must land with the Router). Likely needs an eligibility rework:
   today's all-five-required gate won't fit sector-varying metric sets.
3. **AI assessment generator** (Python step after dbt/export; Claude; store to Supabase; not-advice).
4. **UI redesign** implemented in Streamlit, consuming all of the above.

## Do NOT

- Commit/push `main`; `gh pr merge`. Agent commits need `gitleaks` on PATH (export from the WinGet
  Packages dir if a commit hook can't find it).
- Emit buy/sell/hold/price-target/advice anywhere — the app and the AI reads are educational only.
- **Reword or AUTHOR metric copy/definitions/caveats without owner sign-off (§6)** — this bit us on #135
  (a self-authored ROE caveat was correctly flagged by the scope-auditor and reverted). New metric wording
  must be owner-approved and quoted in the contract.
- Use ROIC / Tier 1 / NIM / ARR / multi-year metrics — yfinance can't source them reliably.
- Clip or hide outlier magnitudes — route to the correct lens instead.
- Add a catalogue row for a new metric before the Router — it would render an un-valued "—" cell on every card.

## Context / open items

- **Backend (track B):** free-tier Supabase pauses after ~7 days idle → app shows repeated
  "Could not load cards" (rendered 4× — a real bug in `_ensure_all_cards`). Restored earlier.
  Decide keep-alive vs paid tier.
- Run dbt via the repo `.venv` (global dbt is broken). For a seed/schema column change use
  `dbt --no-partial-parse ... --full-refresh`; local profile writes to `storage/stock_data.db`.
- `docs/refresh-june-2026` is unrelated in-flight docs work (other chat) — leave it.
- Keep this handover current after each PR.
