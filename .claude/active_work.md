# Active work — handover

_The next session is handed exactly this file. Keep it current. Full slice-by-slice
history through 2026-08-18 is archived in [`docs/handover_2026-08-18.md`](../docs/handover_2026-08-18.md)
— this file stays lean on purpose (it's injected whole at SessionStart by `handover_in.py`,
capped at 32,000 bytes; see Context/open items). When a slice merges, collapse its Status entry to
one line here and let the archive keep the detail._

## Current task

**Reshaping the dashboard into a beginner financial-literacy tool** — sector-aware metrics + AI "reads"
+ a health verdict, via the **Sector/Lifecycle Router** built in slices. **Slices 1–5a and 5b are all
MERGED into `main`** (#139–#148, plus 5b via MR #3) — the full raw-data foundation, per-type metric
compute, the Router mechanism, and both the deterministic health-verdict generator and the Claude Haiku
prose read are complete and merged, code-wise. Whether they're actually live for real users is a
separate, unconfirmed question — see the Infra section for the unresolved Streamlit deploy path and
unverified CI/CD variables. **Slice 6 (UI redesign)**, phased by the owner into 6a/6b/6c, is under way: **6a
(design system foundation) is also MERGED** (MR #4 — tokens, shared row primitive, Search styling, six
review rounds). **6b (Landing/Overflow unification)** and **6c (render new card content: health verdict,
AI read, per-type metrics onto the finished system)** are the remaining phases — **neither has started.**

Note on this section: as of 2026-08-18, this repo's own committed handover prose still described 5b's
MR #3 and 6a's MR #4 as "open" long after both were actually merged (confirmed via the real merge
commits `335046a` and `9b5aaea` on `gitlab/main`) — nobody went back to flip the wording after either
merge landed. This section has been corrected to match actual `main` state; watch for the same drift
next time a slice merges — update this paragraph immediately, don't leave "MR open" language stranded.
Full slice-by-slice narrative (the "do it right" correction, the metric-assignment matrix reasoning, the
external-review adjudication, 5b's and 6a's own review journeys) is in `docs/handover_2026-08-18.md`;
the durable outcomes of that reasoning are captured in Decisions locked below.

## Infra: GitHub → GitLab migration (separate track, not a product slice)

**Why:** GitHub account (`ramialfahham`) was suspended 2026-08-14; ran `/migrate-to-gitlab` at the
owner's direction. Orthogonal to the Sector Router / AI-assessment work.

**State:** Migration complete and verified — new private GitLab project
`rami.al-fahham/stock-swipe-app`, `main` protected correctly, CI green for real
(`validate:branch-guard`/`secret-scan`/`full` all passed on a real pipeline run, not just config that
parses). Full narrative (CI-minutes blocker, runner consolidation, branch-protection ordering trap)
archived in `docs/handover_2026-08-18.md` and [[gitlab-runner-duplicate-registration]].

**Owner-only, still not decided:**
- Streamlit Community Cloud only deploys from GitHub — the live app (stock-explorer.streamlit.app) has
  no deploy path from GitLab. Keep a GitHub mirror, or find another host — not solved.
- `dbt-agent-kit` (this repo's guardrail plugin source) was not migrated — out of scope, also
  unreachable (same suspension).
- Repo visibility: created private by default — flip if wrong; docs reference production secret names.
- CI/CD variable *values* (Supabase creds, `ANTHROPIC_API_KEY`) — confirm these are actually set now
  that 5b (which needs `ANTHROPIC_API_KEY`) is merged; `supabase-migrate` and `data-pipeline` were
  unexercised pending this, plus the Mon 06:00 UTC pipeline schedule, which is project config and can't
  be committed.
- Whether/when to restore `main` branch-protection expectations if GitHub access is ever restored — two
  remotes exist for now.

**Next concrete action:** verify the CI/CD variables and pipeline schedule are actually set (owner-only)
— unclear from this repo's own files whether that step ever happened, since it predates confirmation.

## Status

**Merged (full detail in `docs/handover_2026-08-18.md`):**
- Metric layer + data-only `info_*` metrics (#131–137): ROE, four ratios, FCF yield.
- Sector Router Slice 1 (#139): `company_type` classifier (financial / pre_revenue / operating).
- Sector Router Slice 2 (#140) + 2b (#141): balance-sheet + full three-statement raw data foundation.
- Sector Router Slice 3a (#142) + 3b (#143): statement enrichment + 13 per-type computed metrics.
- Sector Router Slice 4a (#145): Router mechanism (`applies_to` → `metrics_for_card`), grown operating
  card (5→8 metrics), baseline 25.
- Sector Router Slice 4b (#146): financial/bank card (4 metrics), per-type eligibility, baseline 25→30.
- Sector Router Slice 4c (#147): pre-revenue/survival card (4 metrics), pre-revenue eligibility branch,
  baseline 30→35.
- Slice 5a (#148): deterministic 🟢/🟡/🔴 health verdict (rules, not LLM) + `card_assessments` storage.
- **Slice 5b (MR #3): Claude Haiku prose read, regenerate-on-change.** `READ_SYSTEM_PROMPT`/
  `READ_METRIC_BRIEF`/`build_read_messages`; Haiku call gated on `input_hash` change; degrades
  gracefully with no key. Five review rounds, four with real findings (a credential/network-leak in an
  adjacent test, a stale `.env.example` reference, eleven missing metric-applicability caveats, a
  "financial = bank" mislabeling) — all resolved. pytest 142.
- **Slice 6a (MR #4): UI design-system foundation.** New spacing/radius/type-scale CSS tokens
  (`frontend/styles.py`) + `frontend/row_ui.py` shared by Saved-list and Search (Search previously had
  zero custom styling) + `docs/ui/design_system.md`. Six review rounds, five with real findings (missing
  test coverage, a hover-highlight CSS bug bleeding to all rows, an unverified Saved-focus-view
  regression, two rounds of fabricated "Used by" token-doc claims that needed real wiring, not just doc
  edits). pytest 145.
- README/shopfront (#138): owner's manual steps may still be pending — `docs/media/swipe-demo.gif`
  (+ uncomment README line) and an optional social-preview image.
- Test-architecture cleanup (#144): `tests/` reorganized into domain subdirs + `conftest.py` + taxonomy doc.

**Not started:**
- **Slice 6b — Landing/Overflow unification.** Deferred by the owner, explicitly out of 6a's scope.
- **Slice 6c — render new card content** (health verdict, AI read, per-type metrics) **on the finished
  design system.** Deferred by the owner, explicitly out of 6a's scope.

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
- **6a deliberately scoped narrow** — design-system tokens + shared row primitive only; explicitly does not
  touch 6b (Landing/Overflow) or 6c (rendering the new card content). Don't widen a UI-phase PR to cover a
  later phase's scope.

## Next concrete actions

Approved plans (historical design docs, kept in case Slice 6 needs to consult prior slice reasoning):
`~/.claude/plans/noble-forging-beaver.md`, `logical-roaming-brook.md`, `dynamic-snuggling-truffle.md`.
Full slice-by-slice action history in `docs/handover_2026-08-18.md`.

1. **Slice 6b — Landing/Overflow unification.** Not started. Builds on 6a's design-system tokens/`row_ui.py`
   primitive.
2. **Slice 6c — render new card content** (health verdict, AI read, per-type metrics) on the finished
   design system. Not started. This is what finally surfaces Slice 5's AI assessment work in the UI.
3. Confirm the GitLab CI/CD variables (`ANTHROPIC_API_KEY` etc.) and pipeline schedule are actually set —
   see Infra section; status unconfirmed from this repo's own files.
4. **`chore/agent-setup-hygiene` pushed (2026-08-18), MR not yet opened.** Separate track, not a product
   slice — same category as the GitLab migration. Two commits (`fab79de` the reviewed change, `e87c24a`
   the task artifacts): forces `working-agreement.md` to load every session instead of being opt-in, pins
   `dbt-mcp`, and is the branch that produced this file's own trim/corrections. Owner opens the MR
   (https://gitlab.com/rami.al-fahham/stock-swipe-app/-/merge_requests/new?merge_request%5Bsource_branch%5D=chore%2Fagent-setup-hygiene)
   when ready.

## Do NOT

- Commit/push `main`; `gh pr merge`. Agent commits need `gitleaks` on PATH (it is — WinGet Packages dir).
- (GitLab) Don't buy CI minutes, register a self-hosted runner, set CI/CD variable *values*,
  or touch protected-branch settings — all owner-only (§6 cost/config). **Never merge an MR**
  — same rule as GitHub PRs, the owner merges, every time, regardless of MR number. Don't
  assume GitHub is gone for good; don't delete the GitHub remote or repo.
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

- **Review mechanics (keep — reused every slice):** the blocking review gate is `commit_review_gate.py`,
  now wired globally in `~/.claude/settings.json` as of 2026-08-18 (an agent-setup audit that session
  found it had been copied to `~/.claude/hooks/` but never registered — `pre_push_gate.py` and
  `handover_in.py` had the same gap, both now also wired). `diff_sha256` = `sha256(git diff --staged
  --no-renames --no-abbrev)`; get it via `commit_review_gate.py --staged-hash`. Reviewer agents are NOT
  registered as subagent_types in this frontend — run them as **general-purpose** agents with the role
  `.md` inlined (definitions in the plugin `agents/` dir + `.claude/agents/equity-analyst-reviewer.md`).
  review.md + active_work.md are a **separate artifact-only commit** after the reviewed one.
- **This handover fell behind actual `main` state at least twice** (5b and 6a both sat "MR open" in this
  file long after merging) — likely because parallel sessions on this repo did the merging/next-slice
  work without this file being the thing they updated first. If you're picking this file up and something
  in it seems inconsistent with `git log main`, trust `git log main` and fix this file, don't assume the
  file is right.
- **`handover_in.py`'s injection cap (`MAX_BYTES`) exists in three places that can silently diverge:**
  the live, actually-wired copy at `~/.claude/hooks/handover_in.py` (bumped 16000→32000 on 2026-08-18),
  and two dormant source copies — `~/.claude/plugins/cache/dbt-agent-kit/.../hooks/handover_in.py` and
  `~/.claude/plugins/marketplaces/dbt-agent-kit/hooks/handover_in.py` — both still at 16000, unchanged. A
  future `/plugin update` or reinstall of dbt-agent-kit that copies from either dormant source into the
  live hooks dir would silently revert the cap and reintroduce this same truncation bug. Not fixed here
  (editing plugin-managed source felt out of scope for a hygiene branch); if you touch this again, update
  all three or accept the cap will drift back.
- **New raw `stmt_*` field footprint (learned #140):** ingestion module/wiring + staging cast +
  staging/base/core yml docs + **`sources.yml` declaration** + **`scripts/audit_mart_vs_yfinance.py`
  `FUNDAMENTALS_COLUMNS`** + `seed_ci_raw_fixtures.py` + `data_contract.md`. The **two schema mirrors**
  (sources.yml + FUNDAMENTALS_COLUMNS) are easy to miss — the scope-auditor blocks on them (it did on #140).
- **yfinance canonicalises balance-sheet row labels** (camel2title of a fixed `const.py` key set) — labels do
  NOT vary by market. Single canonical label per line; only equity has a real alternate (`Stockholders
  Equity`/`Common Stock Equity`). Probe: `scripts/probe_balance_sheet_labels.py`.
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
- Hygiene: `.venv/` is untracked and NOT gitignored — `git add -A` times out. Stage explicit paths, or add
  `.venv/` to `.gitignore` in a future PR.
- Keep this handover current after each PR.
