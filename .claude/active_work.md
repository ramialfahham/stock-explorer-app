# Active work — handover

_The next session is handed exactly this file. Keep it current._

## Current task

**Project evaluation → redesign.** Owner's lead complaint was a cluttered/inconsistent UI; digging in
revealed the bigger truth: **it's a dashboard, not a learning tool.** The work now is reshaping the
product into a beginner **financial-literacy** tool — sector-aware metrics + AI-written, plain-language
"reads" with a health verdict — on top of the metric layer we built. In flight: the
**equity-analyst-reviewer** (PR #133), then the **metric-catalogue enrichment**.

## Status

- **Metric layer: Phases 1 + 2 MERGED** (#131, #132). `metric_catalogue` seed = single source →
  `metrics.json` → `card_copy.py`; dbt model is the only place metrics compute; no Python mirror; the
  audit re-runs dbt on fresh raw.
- **UI redesign mock: approved look** (one cohesive card, scan→deep tiers, one disclosure pattern,
  label chips for basis, words-not-arrows benchmarks). NOT yet implemented — waits on the metric model.
- **equity-analyst-reviewer: PR #133 open** — a finance-domain blinded reviewer; routes
  `*metric_catalogue.csv`, `docs/metric_layer.md`, `docs/data_contract.md` to it.

## Decisions locked this session (the important ones)

- **Stay on yfinance** (no paid data source). Accept its limits: no ROIC / Tier 1 / Net Interest Margin /
  ARR / multi-year history. Use **ROE not ROIC**; financials get **ROE + P/B + margin**; pre-revenue get
  **cash runway**. (Verified in yahoo `info`: returnOnEquity, priceToBook, profitMargins, marketCap,
  freeCashflow present everywhere incl. banks; debtToEquity/currentRatio/EV missing-or-garbage for financials.)
- **The nonsense magnitudes are REAL data, not corrupt** — metrics mis-applied to the wrong company type
  (financials, pre-revenue, loss-makers, near-zero denominators). **Do not clip/hide** — route to the
  right lens. Applicability is a first-class property of a metric.
- **Architecture: a Sector/Lifecycle Router** — operating company / financial / pre-revenue — each with
  yfinance-available metrics, its own eligibility, rendering, and AI prompt.
- **Perspective taxonomy:** valuation · profitability · growth · solvency · liquidity · cash · returns.
  Two perspectives to ADD: **Returns (ROE)** and **Liquidity (current ratio)**; fix brittle metrics
  (net-debt/EBITDA → **debt-to-equity + interest coverage**; P/E + loss-proof **P/S, EV/EBITDA, FCF yield**).
- **AI assessments:** educational, **NEVER advice** (no buy/sell/price-target); true-beginner language;
  reason only from the given numbers; end with a financial-health verdict (🟢/🟡/🔴).

## Next concrete actions (in order)

1. Merge PR #133 (reviewer). Then sync main.
2. **Catalogue enrichment PR** (reviewed by equity-analyst): rename `metric_group → perspective`; add
   columns `calculation`, `interpretation`, `applicability`; populate the existing 5. **Drafted content
   is owner-reviewed (in the chat) — ready to write.** Update `_seeds.yml`, export script, tests, docs.
3. **Add the new metrics** (ROE, current ratio, P/B, P/S, EV/EBITDA, FCF yield, cash runway) — new raw
   fields in ingestion (yahoo info: returnOnEquity, debtToEquity, currentRatio, priceToBook, marketCap,
   sharesOutstanding) + dbt compute + catalogue rows.
4. **Sector/Lifecycle Router** (classify company type → metric set + eligibility + rendering + AI prompt).
5. **AI assessment generator** (Python step after dbt/export; Claude; store to Supabase; not-advice).
6. **UI redesign** implemented in Streamlit, consuming all of the above.

## Do NOT

- Commit/push `main`; `gh pr merge`. Agent commits need `gitleaks` on PATH (export from the WinGet
  Packages dir if a commit hook can't find it).
- Emit buy/sell/hold/price-target/advice anywhere — the app and the AI reads are educational only.
- Reword metric copy/definitions without owner sign-off (§6).
- Use ROIC / Tier 1 / NIM / ARR / multi-year metrics — yfinance can't source them reliably.
- Clip or hide outlier magnitudes — route to the correct lens instead.

## Context / open items

- **Backend (track B):** free-tier Supabase pauses after ~7 days idle → app shows repeated
  "Could not load cards" (rendered 4× — a real bug in `_ensure_all_cards`). Restored this session.
  Decide keep-alive vs paid tier.
- `docs/refresh-june-2026` is unrelated in-flight docs work (other chat) — leave it.
- This handover was badly stale before today's rewrite; keep it current after each PR.
