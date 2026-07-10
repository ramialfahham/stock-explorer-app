# Task contract

objective: **Sector/Lifecycle Router — Slice 4c: the pre-revenue / survival card.** The last Router slice.
  Pre-revenue companies (loss-makers, revenue ≤ 0) still never appear — they ride the `else`/five-metric AND,
  which they fail. 4c gives them the survival card (cash runway, monthly cash burn, net-cash-vs-value, working
  capital) + a pre-revenue eligibility branch, catalogues the 4 already-computed metrics, adds a compact-currency
  display format for the two dollar amounts, and adds a synthetic pre-revenue fixture.
  Approved plan: ~/.claude/plans/dynamic-snuggling-truffle.md.
  Note: branch stacks on feat/sector-router-slice4b (4b/#146 not yet merged); the 4c PR shows 4b+4c until #146 merges.

scope_paths:
  - dbt_analytics/models/4_intermediate/int_stock__card_metrics.sql   # pre_revenue eligibility + missing_metrics branch
  - dbt_analytics/models/4_intermediate/_intermediate.yml             # int per-type eligibility test (3-branch) + pre-rev unit test + column docs
  - dbt_analytics/models/4_intermediate/int_stock__sector_benchmarks.sql # exclude pre_revenue from benchmark peers (review cycle 1)
  - dbt_analytics/tests/assert_eligible_mart_rows_have_all_metrics.sql # per-type required-metric assertion (3-branch)
  - dbt_analytics/models/5_marts/mart_stock_cards.sql                 # + 4 survival metric values in SELECT; exclude pre_revenue from benchmark join (cycle 2)
  - dbt_analytics/models/5_marts/_marts.yml                           # per-type eligibility test (3-branch); doc 4 columns
  - dbt_analytics/models/_docs.md                                     # card_eligibility doc block -> 3-branch per-type (review cycle 2)
  - dbt_analytics/seeds/metric_catalogue.csv                          # +4 pre_revenue rows; narrow pre_revenue off 5 metrics
  - dbt_analytics/seeds/_seeds.yml                                    # format accepted_values += currency_compact
  - frontend/card_copy.py                                             # currency_compact formatter + format_metric_value currency param
  - frontend/card_ui.py                                              # _metric_cell_html passes card currency
  - frontend/metrics.json                                            # regenerated from the seed
  - scripts/export_to_supabase.py                                    # EXPORT_COLUMNS += 4 survival metrics
  - supabase/migrations/009_pre_revenue_card_metrics.sql             # new: add the 4 numeric columns
  - docs/data_contract.md                                            # export table += 4; eligibility section += pre_revenue branch
  - scripts/seed_ci_raw_fixtures.py                                  # add a pre_revenue Healthcare fixture per market
  - scripts/eligibility_baseline.ci.json                             # 30 -> 35 (recalibrated)
  - tests/tooling/test_metric_catalogue.py                           # _VALID_FORMATS += currency_compact
  - tests/frontend/test_card_copy.py                                 # metrics_for_card(pre_revenue) + currency_compact format
  - tests/frontend/test_card_ui.py                                   # pre_revenue build_card_html render
  - .claude/task/contract.md

review_artifacts (separate artifact-only commit after; review.md records the reviewed diff's hash):
  - .claude/task/review.md
  - .claude/active_work.md

decisions_reserved (owner-approved this session; §6):
  - **Fuller survival card = 4 metrics** (cash_runway_months, burn_rate_monthly, net_cash_to_market_cap, working_capital),
    incl. a **new compact-currency format** for burn_rate + working_capital.
  - **Broader pre-revenue gate:** a pre_revenue company is eligible when `net_cash_to_market_cap is not null` (has
    market cap + cash + debt) — not only when actively burning.
  - **Add a synthetic pre-revenue fixture** for local verifiability (CI baseline 30 -> 35).
  - **Beginner copy** for the 4 metrics is owner-signed (plan-approved). `data_contract.md` stays factual.

technical_definition:
  - **Per-type eligibility (3-branch):** `eligibility` CTE `CASE company_type`: `financial` = core three (4b);
    `pre_revenue` = `net_cash_to_market_cap is not null`; else (operating) = five-metric AND. `missing_metrics` mirrors it.
    Applied to all 5 sites (int model + `_intermediate.yml`/`_marts.yml` expression tests + the singular assertion).
  - **Catalogue:** +4 rows `applies_to = pre_revenue`, `benchmarkable = false` (net_cash_to_market_cap ratio_2/valuation;
    working_capital currency_compact/liquidity; cash_runway_months ratio_1/cash; burn_rate_monthly
    currency_compact/cash). Narrow `pre_revenue` off `forward_pe`/`revenue_growth_yoy_pct` (-> operating|financial)
    and `ebit_margin_pct`/`net_debt_to_ebitda`/`fcf_margin_pct` (-> operating). Pre-revenue card = the 4 survival metrics.
  - **currency_compact format:** `card_copy._format_currency_compact(value, currency)` — compact magnitude (B/M/K,
    sign-aware) + currency symbol (USD $ / GBP £ / JPY ¥ / EUR € / AUD A$; fallback code). `format_metric_value`
    gains an optional `currency`; `_metric_cell_html` passes `card.get("currency")`. Backward-compatible.
    Registered in `_seeds.yml` format accepted_values + `test_metric_catalogue._VALID_FORMATS`.
  - **Mart carry:** the 4 metric VALUES to `mart_stock_cards.sql` SELECT + `_marts.yml` docs + `EXPORT_COLUMNS` +
    `009_pre_revenue_card_metrics.sql` (4 nullable columns) + `data_contract.md`.
  - **Fixture:** one `info_sector: 'Healthcare'`, `stmt_total_revenue: 0` row per market (burning: negative OCF +
    capex; cash + debt + market cap -> net_cash_to_market_cap present -> eligible; current assets/liabilities ->
    working_capital). CI baseline 30 -> 35.

done_when:
  - `dbt build --project-dir dbt_analytics --profiles-dir . --no-partial-parse --full-refresh` green incl. the
    3-branch eligibility test + the pre-revenue unit test; the pre_revenue fixture is `pre_revenue` + eligible.
  - `python scripts/export_metric_definitions_json.py` -> `metrics.json` regenerated & committed.
  - Gates green; `check_eligibility_baseline.py --baseline-path scripts/eligibility_baseline.ci.json` -> **35**; export-health OK.
  - `pytest tests/` -> current + new survival/currency tests.
  - Survival-card smoke: a card from the pre_revenue fixture mart row renders the 4 survival metrics
    (`$`-formatted burn + working capital), omits operating/bank metrics, no `—`; operating + bank cards unchanged.
  - Full blinded review cycle recorded in `review.md`; reviewed commit + separate artifact commit; PR to main (NOT merged).

impact_map:
  - **Eligible pool grows again:** pre-revenue companies with net_cash_to_market_cap now appear. CI baseline 30 -> 35
    (fixture); full-pipeline baseline (843) rises -> `check_eligibility_baseline.py` passes (only fails on drops) ->
    owner `--write-baseline` refresh on the next weekly pipeline (not local).
  - Operating + financial cards unchanged (their eligibility branches + rendered sets identical). New Supabase
    columns additive/nullable. The `currency_compact` format is additive (ratio/percent metrics unaffected).
  - Required reviewers (per `.claude/review_routing.json`): **scope-auditor** · **analytics-engineer**
    (`*.sql`/`*.csv`/`_marts.yml`/`_intermediate.yml`) · **cto** (`frontend/*`/`scripts/*`/`tests/*` — the currency
    format) · **data-engineer** (`supabase/*`) · **equity-analyst** (`metric_catalogue.csv`/`data_contract.md` —
    the survival copy). No `ingestion/` change.

amendments:
  - 2026-07-08 — supersedes the Slice 4b contract (PR #146). Scope = Sector Router Slice 4c (pre-revenue/survival
    card + pre-revenue eligibility branch + compact-currency format) per approved plan dynamic-snuggling-truffle.md.
  - 2026-07-08 (review cycle 1) — 5 blinded reviewers: data-engineer / scope-auditor / cto PASS; equity-analyst +
    analytics-engineer FAIL, both resolved. **Metric switch (owner-approved via AskUserQuestion):** replaced
    `net_cash_to_ev` with `net_cash_to_market_cap` (net cash / market cap) — the EV denominator sign-flips when
    net cash exceeds enterprise value (a real cash-rich-biotech pattern), contradicting higher_better; market cap
    is monotonic, no pole. Swapped across the model, catalogue, 5 eligibility sites, mart/export/migration 009,
    data_contract, fixture, and tests; `net_cash_to_ev` reverts to data-only. **Benchmark fix (analytics):**
    `int_stock__sector_benchmarks` now excludes `pre_revenue` from the peer set, so a pre-revenue biotech can't
    inflate an operating card's sector peer-count / >= 8 gate in a shared sector. Fixed stale `_intermediate.yml`
    column docs (is_card_eligible "all five" -> 3-branch; the 4c metrics' + company_type's "data-only" claims) and
    the singular-test header; added the runway "assumes steady burn" caveat to the rendered `learn` copy (equity);
    added `currency` to the render-test helper (cto coverage nit). **Owner §6 sign-off** of the reworked net-cash
    metric obtained this session (AskUserQuestion, 2026-07-08).
  - Deferred (out of 4c scope): the pre-existing 4a/4b "data-only — not in the catalogue/export yet" boilerplate on
    now-catalogued metrics (debt_to_equity, current_ratio_stmt, price_to_tangible_book, net_margin_pct, roa_pct,
    statement_roe_pct, dividend_yield_pct) in `_intermediate.yml` — a prior-slice doc-staleness cleanup.
  - 2026-07-10 (review cycle 2) — 5 blinded reviewers on the reworked diff: scope-auditor PASS; data-engineer /
    equity-analyst / analytics-engineer / cto FAIL, all on incomplete-sweep documentation staleness (every reviewer
    verified the executable eligibility/metric logic is correct + consistent) plus one behavioral edge case. Fixed:
    leftover `net_cash_to_ev` prose in `_marts.yml` (is_card_eligible desc), `int_stock__card_metrics.sql`
    (eligibility-CTE header comment), `seed_ci_raw_fixtures.py` (fixture docstring arithmetic 0.667 -> 0.4), and the
    contract body (decisions_reserved / technical_definition / impact_map now name net_cash_to_market_cap; the switch
    history stays in the cycle-1 amendment); the authoritative `_docs.md` `card_eligibility` block "all five" -> the
    3-branch per-type set (added to scope); `_marts.yml` company_type "does not affect is_card_eligible" -> "selects the
    per-type eligibility branch". **Behavioral (analytics):** `mart_stock_cards` now excludes pre_revenue from the
    sector-benchmark join (`and m.company_type != 'pre_revenue'`) so a pre-revenue card no longer inherits an
    operating-peer `sector_peer_count` / "(N companies)" headline for a set it was excluded from — the mirror of the
    cycle-1 benchmark fix. Repo-wide `net_cash_to_ev` grep re-audited: remaining hits are the data-only computation
    (`int_stock__card_metrics.sql`), its column doc (`_intermediate.yml`), and the formula-reference list
    (`data_contract.md`) — all correct/data-only.
  - Deferred (still out of 4c scope, pre-existing since 4b, user-facing copy = §6): the "all five fundamentals" /
    "five-metric snapshot" search-tip copy in `frontend/overflow_menu.py` (+ `tests/frontend/test_overflow_menu.py`)
    and the high-level "five-metric" framing in `README.md` / `docs/north_star.md` — a per-type copy/doc modernization
    to raise with the owner, not folded into 4c.
  - 2026-07-10 (review cycle 3) — 5 blinded reviewers on the reworked diff (hash 048c9a84): cto / scope-auditor /
    data-engineer PASS; equity-analyst + analytics-engineer FAILed on one shared item — the `company_type`
    "does not affect is_card_eligible" clause survived in `docs/data_contract.md` (the twin of the `_marts.yml`
    clause fixed in cycle 2). Swept it and every same-class contradiction in that file: the export-table row
    (line 320), the company-type classification block ("not part of is_card_eligible / the Supabase export yet" +
    "the Router will use ... out of scope here" -> company_type drives the per-type eligibility branch and is
    exported), and the two stale "data-only / not catalogued" headers that had begun to include this slice's own
    now-catalogued metrics (working_capital / cash_runway_months / burn_rate_monthly) -> reworded to point at the
    authoritative seed and name only the genuinely data-only intermediates. Doc-only; no code/test/gate change
    (dbt build / pytest / gates stay green from the cycle-2 verification).
  - Deferred (still out of 4c scope): `docs/data_contract.md` market-onboarding checklist "coverage audit (all five
    metrics ...)" — the same pre-existing "five-metric framing" class as the README/north_star copy above; a
    per-type doc modernization to raise with the owner, not folded into 4c.
