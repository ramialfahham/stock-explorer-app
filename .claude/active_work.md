# Active work — handover

_The next session is handed exactly this file. Keep it current._

## Current task

**Project evaluation → redesign.** Owner's lead complaint was a cluttered/inconsistent UI; digging in
revealed the bigger truth: **it's a dashboard, not a learning tool.** The work is reshaping it into a
beginner **financial-literacy** tool — sector-aware metrics + AI-written plain-language "reads" with a
health verdict. The straightforward **data-only metrics are done and merged** (ROE #135, four ratios #136,
FCF yield #137). **The Sector/Lifecycle Router is now in progress, built in slices** — it turns this inert
metric data into per-company-type, displayed, owner-copy'd value. **Slice 1 (the company-type classifier,
data-only) is [PR #139](https://github.com/ramialfahham/stock-swipe-app/pull/139) — open, awaiting merge.**

## Status

- **Metric layer Phases 1+2 MERGED** (#131, #132); **equity-analyst-reviewer MERGED** (#133);
  **catalogue enrichment MERGED** (#134, `metric_group → perspective` + calculation/interpretation/
  applicability + 7-value taxonomy).
- **Data-only metrics — ALL MERGED** (computed in `int_stock__card_metrics`, nothing rendered):
  - **ROE** (#135) `roe_pct`; **ratios** (#136) `current_ratio`, `price_to_book`, `price_to_sales`,
    `ev_to_ebitda`; **FCF yield** (#137) `fcf_yield_pct = info_free_cashflow / info_market_cap * 100`
    (Yahoo trailing freeCashflow / current marketCap; a 2nd FCF source vs annual `stmt_free_cash_flow`).
- **Sector Router — Slice 1 (company-type classifier) PR OPEN [#139](https://github.com/ramialfahham/stock-swipe-app/pull/139)**
  (branch `feat/company-type-classifier`). `company_type` in `int_stock__card_metrics`: `financial`
  (info_sector = 'Financial Services'), `pre_revenue` (stmt_total_revenue present & ≤ 0; null → operating),
  else `operating`. Data-only (not in eligibility/catalogue/metrics.json/export). Verified: build 93; all
  gates; eligibility 25 + export 100% unchanged; pytest 73; card byte-identical. 3-reviewer cycle all PASS.
- **UI redesign mock: approved look** (one cohesive card, scan→deep tiers, one disclosure pattern, label
  chips for basis, words-not-arrows benchmarks). NOT implemented — waits on the Router + metric model.

## Decisions locked (the important ones)

- **Stay on yfinance.** Use ROE not ROIC; financials get ROE + P/B + margin; pre-revenue get cash runway.
- **Company types (owner-approved, this session):** `operating` / `financial` / `pre_revenue`. Financial by
  `info_sector = 'Financial Services'`; pre_revenue by `stmt_total_revenue` present & ≤ 0 (a **null** revenue
  is a data gap → `operating`, conservative, tunable — owner-flagged threshold). **REITs stay `operating`.**
- **Bank solvency (owner-approved, this session): BUILD debt-to-equity + interest coverage** — but yfinance
  staging has **no total-equity and no interest-expense field** (checked `stg_yf__fundamentals`), so they are
  NOT passthroughs: each needs a new raw field ingested first → **Slice 2**, not a quick add. Net-debt/EBITDA
  is also routed to operating-only by the Router (routing IS the fix; the two new metrics are additive).
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

**The Sector/Lifecycle Router is sliced** (approved plan: `~/.claude/plans/noble-forging-beaver.md`). Don't
try to land it in one PR.

1. **Slice 1 — company-type classifier: DONE, [PR #139](https://github.com/ramialfahham/stock-swipe-app/pull/139) open.**
   `company_type` data-only in `int_stock__card_metrics`. (Merge, then continue.)
2. **Slice 2 — ingestion + new data-only metrics.** Add **total-equity** and **interest-expense** raw fields
   (ingestion → staging → base → core), then compute `debt_to_equity` + `interest_coverage` as data-only.
   Also compute `cash_runway` (uses existing `info_total_cash` + FCF burn; only meaningful when FCF < 0 — no
   operating-cash-flow field exists). Still data-only (no display).
3. **Slice 3 — the Router mechanism (keystone).** Per-type metric sets; **eligibility rework** (today's
   all-five-required gate can't express sector-varying sets — likely a per-type required-set config);
   carry `company_type` into `mart_stock_cards`; per-type `card_ui`/`card_copy` display; **catalogue rows +
   owner-approved applicability/beginner copy** for the surfaced metrics; recalibrate the eligibility baseline.
   Likely sub-split operating (at parity) → financial → pre_revenue.
   - **Metric sets (proposed, need §6 sign-off at this slice):** operating = current five + selected ratios;
     financial = ROE + P/B + margin + debt-to-equity/interest-coverage (NOT net-debt/EBITDA, NOT FCF margin);
     pre_revenue = cash runway + FCF yield (negative = burn) + P/B.
   - **Applicability copy the Router MUST author** (reviewer flags, deferred): ROE — distorted by
     negative/thin equity (spuriously positive) + leverage/DuPont, breaks for financials; **FCF yield — can
     be NEGATIVE for cash-burners** (equity-analyst flag on #137); EV/EBITDA & P/B — financials caveats.
4. **AI assessment generator** (Python step after dbt/export; Claude; store to Supabase; not-advice).
5. **UI redesign** in Streamlit, consuming all of the above.

## Do NOT

- Commit/push `main`; `gh pr merge`. Agent commits need `gitleaks` on PATH (it is — WinGet Packages dir).
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
  regenerates fixtures from `scripts/seed_ci_raw_fixtures.py`; **local raw is the CI fixture set (25 rows,
  all Technology → all `operating`), so financial/pre_revenue only surface on the full pipeline, not locally.**
  Verify set: build + doc/layer/structure/sqlfluff + eligibility-baseline + export-health + pytest.
- **Ingestion gap for Slice 2:** `stg_yf__fundamentals` has `info_total_debt`, `info_total_cash`, `info_ebitda`,
  `info_return_on_equity` … but **no total-equity, no interest-expense, no operating-cash-flow** field. So
  debt-to-equity + interest coverage each need a new ingested raw field first.
- **Review mechanics:** the active gate is the **plugin** `commit_review_gate.py` (no in-repo
  `.claude/hooks/git_discipline.py`, so it does NOT stand down). `diff_sha256` = `sha256(git diff --staged
  --no-renames --no-abbrev)`; get it via `commit_review_gate.py <plugin-root> --staged-hash`. Reviewer agents
  are NOT registered as subagent_types in this frontend — run them as general-purpose agents with the role
  `.md` inlined. review.md + active_work.md are a **separate artifact-only commit** after the reviewed one.
- **Backend (track B):** free-tier Supabase pauses after ~7 days idle → repeated "Could not load cards"
  (a real bug in `_ensure_all_cards`). Decide keep-alive vs paid tier.
- `docs/refresh-june-2026` is unrelated in-flight docs work (other chat) — leave it.
- **README/shopfront (side-quest) — MERGED [#138](https://github.com/ramialfahham/stock-swipe-app/pull/138)**
  (in `main` at 825f208). README funnel, MIT `LICENSE`, `docs/media/`, repo metadata. **Owner's manual steps
  may still be pending:** add `docs/media/swipe-demo.gif` (+ uncomment the README line) and optionally a
  social-preview image (Settings → Social preview, 1280×640).
- Hygiene note (not done, out of scope): `.venv/` is untracked and NOT gitignored — `git add -A` tries to
  stage thousands of files and times out. Stage explicit paths, or add `.venv/` to `.gitignore` in a future PR.
- Keep this handover current after each PR.
