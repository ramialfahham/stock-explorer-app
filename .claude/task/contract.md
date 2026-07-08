# Task contract

objective: **Sector/Lifecycle Router — Slice 4a: the Router mechanism + the grown operating card.**
  Turn the data-only per-type columns (merged in #139/#143) into actual per-type cards. Add a catalogue-driven
  `applies_to` column so the frontend renders **only** the metrics that apply to a card's `company_type`, and
  **omit** (never `—`) any metric that doesn't apply or has no value. Carry `company_type` end-to-end
  (int model → mart → Supabase export → frontend). **Grow the operating card 5 → 8** by cataloguing three new
  operating metrics (`debt_to_equity`, `current_ratio_stmt`, `statement_roe_pct`) with owner-signed beginner
  copy. Eligibility is **untouched** (five-metric AND stays); the new metrics are display-only, so the eligible
  pool and the baseline are unchanged and 4a is fully verifiable on the all-operating local fixtures.
  Financial (4b) and pre-revenue (4c) cards + per-type eligibility are separate follow-on PRs.
  Approved plan: ~/.claude/plans/dynamic-snuggling-truffle.md.

scope_paths:
  - dbt_analytics/models/5_marts/mart_stock_cards.sql        # + m.company_type in SELECT
  - dbt_analytics/models/5_marts/_marts.yml                  # company_type doc + not_null + accepted_values
  - dbt_analytics/seeds/metric_catalogue.csv                 # + applies_to column; + 3 new operating rows
  - dbt_analytics/seeds/_seeds.yml                           # applies_to not_null (dbt-native catalogue guard)
  - dbt_analytics/models/4_intermediate/_intermediate.yml    # negative-equity unit test (review cycle 2)
  - scripts/export_metric_definitions_json.py                # emit applies_to into metrics.json
  - frontend/metrics.json                                    # regenerated from the seed
  - frontend/card_copy.py                                    # parse applies_to; metrics_for_card(card, tier)
  - frontend/card_ui.py                                      # 3 ALL_METRICS loops -> per-card set
  - scripts/export_to_supabase.py                            # EXPORT_COLUMNS += company_type + 3 metric values
  - supabase/migrations/007_router_card_columns.sql          # new: add company_type + 3 operating metric cols
  - docs/data_contract.md                                    # export-shape table += company_type (factual only)
  - tests/tooling/test_metric_catalogue.py                   # applies_to well-formedness
  - tests/frontend/test_card_copy.py                         # metrics_for_card unit tests
  - tests/frontend/test_card_ui.py                           # per-type render assertions (as needed)
  - scripts/seed_ci_raw_fixtures.py                          # only if fixtures lack the balance-sheet inputs
  - .claude/task/contract.md

review_artifacts (separate artifact-only commit after; review.md records the reviewed diff's hash):
  - .claude/task/review.md
  - .claude/active_work.md

decisions_reserved (owner-approved this session; §6):
  - **Three-PR slicing:** 4a = mechanism + operating; 4b = financial; 4c = pre-revenue.
  - **Grow operating now** (not keep-at-five) — fills the liquidity + returns lenses and complements solvency.
  - **Omit blank lenses silently** — no explainer row.
  - **New operating metrics are display-only, NOT in the eligibility gate** (baseline stays stable). Eligibility
    rework + baseline recalibration deferred to 4b/4c (full-pipeline only).
  - **Operating returns lens = ROE only** (ROA joins ROE on the financial card in 4b, where the numerator-
    asymmetry caveat lands).
  - **Beginner copy** for the 3 new metrics is owner-signed (plan-approved); `data_contract.md` stays strictly
    factual — caveats live in the catalogue.

technical_definition:
  - **applies_to**: pipe-delimited company-type set on every catalogue row (avoids CSV quoting). 5 existing =
    `operating|financial|pre_revenue` (parity — unchanged rendering on all card types); 3 new = `operating`.
  - **Render rule** (centralized in `card_copy.metrics_for_card(card, tier=None)`): show metric *m* on card *c*
    iff `c.company_type in m.applies_to` AND `c[m] is not null`; ordered by `display_order`; optional tier
    filter; missing/None `company_type` defaults to `operating`. `card_ui.py` loops (`:57`, `:83`, `:194`)
    consume it. `ALL_METRICS` stays the full catalogue id set -> the no-drift test stays green.
  - **mart carry (company_type + the 3 new metric VALUES)**: the frontend renders from the exported card
    dict, so the new metric values must reach it too — not just company_type. `mart_stock_cards.sql` SELECT
    adds `m.company_type` + `m.debt_to_equity` + `m.current_ratio_stmt` + `m.statement_roe_pct`; `_marts.yml`
    docs all four (company_type: `not_null` + `accepted_values:[operating,financial,pre_revenue]`);
    `export_to_supabase.py` `EXPORT_COLUMNS` += the four; `007_router_card_columns.sql` adds the four Supabase
    columns (all nullable/additive); `data_contract.md` export table += the four. Frontend read is
    `select("*")` -> no change there.
  - **Operating card 5 -> 8**, lens-grouped, new metrics `tier=2`, `benchmarkable=false`:
    forward_pe(1) - ebit_margin_pct(2) - revenue_growth_yoy_pct(3) - net_debt_to_ebitda(4) - **debt_to_equity(5)**
    - **current_ratio_stmt(6)** - fcf_margin_pct(7) - **statement_roe_pct(8)**. (`fcf_margin` order 5->7.)
  - The 3 new metrics are already **computed** in `int_stock__card_metrics` (#143) -> no model change; only the
    catalogue rows + generated JSON + render wiring are new.
  - **generator**: `export_metric_definitions_json.py` emits `applies_to`; regenerate `metrics.json`, commit.

done_when:
  - `dbt build --project-dir dbt_analytics --profiles-dir . --no-partial-parse --full-refresh` green (seed change).
  - `python scripts/export_metric_definitions_json.py` -> `metrics.json` regenerated & committed (byte-identical to test).
  - Gates green: layer / SQL-structure / doc / sqlfluff; **eligibility-baseline unchanged** (eligibility untouched);
    export-health OK. (`company_type` non-null is enforced by the dbt `not_null` test during `dbt build`, not by
    export-health, which only checks the `business_summary` fill rate.)
  - `pytest tests/` -> current 80 **plus** the new `applies_to` + `metrics_for_card` tests.
  - Grown-card smoke: an operating fixture card renders its metrics (<=8, no `—` when a balance-sheet line is null);
    `company_type` reaches the card dict.
  - Full blinded review cycle recorded in `review.md`; reviewed commit + separate artifact commit; PR to main (NOT merged).

impact_map:
  - Operating cards gain 3 metrics (below the hero three). Financial/pre-revenue cards render **exactly as today**
    in 4a (the 5 existing metrics keep `applies_to` = all types); their tailored cards land in 4b/4c.
  - No eligibility change -> discovery pool + baseline stable. New Supabase column is additive (nullable) — safe
    for the current export; frontend defaults a missing `company_type` to `operating`.
  - Required reviewers (per `.claude/review_routing.json` vs staged paths): **scope-auditor** (always) -
    **analytics-engineer-reviewer** (`*.sql`, `*.csv`, `_marts.yml`) - **cto-reviewer** (`frontend/*`,
    `scripts/*`, `tests/*`) - **data-engineer-reviewer** (`supabase/*`) - **equity-analyst-reviewer**
    (`metric_catalogue.csv`, `data_contract.md` — the new metric copy/caveats). No `ingestion/` change.

amendments:
  - 2026-07-07 — supersedes the merged test-architecture contract (#144). Scope = Sector Router Slice 4a
    (per-type render mechanism + company_type carry + grown operating card) per approved plan
    dynamic-snuggling-truffle.md.
  - 2026-07-07 (review cycle 1) — addressed blinded-reviewer findings: added `applies_to` `not_null` to
    `_seeds.yml` (analytics-engineer #2); added a `current_ratio_stmt >= 0` mart consistency test
    (analytics-engineer #1); `debt_to_equity` / `statement_roe_pct` are sign-varying (legitimately negative on
    negative equity / losses, like the existing untested `net_debt_to_ebitda`) so carry no simple range test —
    their computation + null-guards are unit-tested at the int layer (#143) and the mart is a verified
    SELECT-only carry. Reworded `statement_roe_pct` copy: "two-year average" → "Yahoo averages equity across the
    year" (imprecise ROE methodology) and dropped "minority interests" jargon (equity-analyst) — reviewer-driven
    corrections to plan-approved copy, flagged for owner sign-off at merge. Corrected the done_when export-health
    wording (data-engineer).
  - 2026-07-08 (review cycle 2) — adopted the analytics-engineer's non-blocking option (b): added the
    `card_metrics_statement_metrics_negative_equity` unit test to `_intermediate.yml` (asserts negative equity ->
    real signed `debt_to_equity` = -0.5 and loss-over-negative-equity -> spuriously positive `statement_roe_pct`
    = 20.0, the behavior the copy warns about). Fixed the equity-analyst's residual finding: dropped the
    "minority interest" jargon from BOTH new-metric `description` fields (frontend-facing; the `learn` field was
    fixed in cycle 1). **Owner §6 sign-off obtained this session**: the exact before/after wording of both
    corrections was presented to the owner via an AskUserQuestion prompt, and the owner selected "Approve — ship
    as-is" (2026-07-08). The reworded copy is therefore owner-approved, not merely deferred to merge; also
    recorded in review.md.
