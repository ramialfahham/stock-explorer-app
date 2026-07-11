# Task contract

objective: **Slice 5a — AI assessment: deterministic health verdict + storage (no LLM).** First half of
  Slice 5 (the AI assessment generator). Computes a per-type 🟢/🟡/🔴 **financial-health** verdict from each
  card's own numbers via **deterministic rules** (NOT the LLM), stores it + an `input_hash` to a new Supabase
  table `card_assessments`, and wires the generator into the weekly pipeline. Ships **NO LLM / anthropic dep /
  API key / cost** — 5b adds the Claude-written prose read + regenerate-on-change. Data-only (Slice 6 renders).
  Approved plan: ~/.claude/plans/dynamic-snuggling-truffle.md.

scope_paths:
  - scripts/assessment_rules.py                    # NEW: pure per-type verdict + input_hash
  - scripts/generate_assessments.py                # NEW: runner (read mart -> verdict+hash -> upsert)
  - supabase/migrations/010_card_assessments.sql   # NEW: card_assessments table + RLS public read
  - .github/workflows/data_pipeline.yml            # + "Generate assessments" step after export
  - .github/workflows/ci-validate.yml              # + no-secret dry-run smoke
  - docs/data_contract.md                          # + card_assessments section (factual)
  - tests/tooling/test_assessment_rules.py         # NEW: verdict + hash unit tests + catalogue mirror
  - tests/tooling/test_generate_assessments.py     # NEW: offline generator test
  - .claude/task/contract.md

review_artifacts (separate artifact-only commit after; review.md records the reviewed diff's hash):
  - .claude/task/review.md
  - .claude/active_work.md                          # incl. the 4c PR'd -> MERGED handover flip

decisions_reserved (owner-approved this session; §6 — plan-approved):
  - **Verdict = deterministic per-type rules** decide the color; the LLM writes prose only (5b). Measures
    **financial health / resilience** on the card's own numbers only — **excludes valuation (P/E, P/TBV) and
    growth**. Conservative **worst-axis-wins**. Per-type bands (owner-signed): operating
    (leverage `net_debt_to_ebitda` / profitability `ebit_margin_pct` / cash `fcf_margin_pct` + supporting
    debt_to_equity/current_ratio_stmt/statement_roe_pct); financial (statement_roe_pct/net_margin_pct/roa_pct —
    **profitability-only honest limit**, no sourceable capital adequacy); pre_revenue
    (cash_runway_months/net_cash_to_market_cap/working_capital).
  - **Generate-and-store, data-only** (no UI — Slice 6 renders). **Split 5a/5b** (5a ships no LLM/dep/key/cost).
  - **Grain = (market_code, ticker)**; store the ASCII token `green|yellow|red` (Slice 6 maps to 🟢/🟡/🔴).

technical_definition:
  - **assessment_rules.py (pure, no I/O):** `INPUT_FIELDS_BY_TYPE` + `DIRECTION_BY_METRIC` mirror
    `metric_catalogue.csv` `applies_to`/`direction`; `compute_verdict(row)` dispatches on `company_type`
    (null/unknown -> operating), null-tolerant + **total** (always `green|yellow|red`; all-unknown -> yellow).
    `compute_input_hash(row, verdict, *, version)` = sha256 of the canonicalized per-type input set +
    `company_type` + verdict + version (floats `round(v,6)`, `NaN->None`; numbers only, no name/sector).
  - **010_card_assessments.sql:** table (`market_code` FK markets, `ticker`, `company_type`,
    `health_verdict` CHECK in `green|yellow|red`, `ai_read` null-in-5a, `read_model` null-in-5a, `input_hash`,
    `snapshot_date`, `generated_at`; `unique(market_code, ticker)`); indexes on market_code + health_verdict;
    RLS enable + public **select** policy (service-role writes bypass). Mirrors `002_fundamentals_mart.sql`.
  - **generate_assessments.py:** mirrors `export_to_supabase.py` — read `marts.mart_stock_cards` read-only
    (already `is_card_eligible`), NaN->None coercion, dedupe to latest snapshot per `(market_code, ticker)`,
    `build_assessment_records` (pure: verdict + hash; **OMIT `ai_read`/`read_model`** so a 5a re-run never
    clobbers a 5b read), `--dry-run` returns **before** requiring creds, else upsert `on_conflict=market_code,ticker`.
  - **Pipeline:** `data_pipeline.yml` "Generate assessments" step after "Export to Supabase" (reuses the job's
    Supabase service-role secret); `ci-validate.yml` dry-run smoke after export-health (no secret).

done_when:
  - `pytest tests/` green incl. the new rules unit tests (per type × verdict, boundaries, null-tolerance,
    totality, hash determinism/float-stability/version) + the catalogue-mirror guard + the offline generator test.
  - `python scripts/generate_assessments.py --duckdb-path storage/stock_data.db --dry-run` over the fixture mart
    prints one verdict per eligible card (CI01–05 operating, CIFIN bank, CIPRE pre_revenue), no creds required.
  - `python scripts/apply_supabase_migrations.py --dry-run` lists `010_card_assessments.sql`; idempotent.
  - `data_contract.md` card_assessments section accurate; **no new dependency, no API key, no LLM call in 5a**.
  - Full blinded review recorded in `review.md`; reviewed commit + separate artifact commit; PR to main (NOT merged).

impact_map:
  - New Supabase table `card_assessments` (additive; public-read RLS; service-role write). New weekly pipeline
    step — **no new secret** (reuses `SUPABASE_SERVICE_ROLE_KEY`). No dbt / mart / frontend / dependency change.
    `anthropic` + `ANTHROPIC_API_KEY` + the prose read deferred to **5b**; rendering deferred to **Slice 6**.
  - Required reviewers (per `.claude/review_routing.json`): **scope-auditor** · **analytics-engineer**
    (`010_*.sql`) · **data-engineer** (`supabase/*`) · **cto** (`scripts/*`/`tests/*`/`.github/workflows/*`) ·
    **equity-analyst** (`data_contract.md` + the verdict rubric).

amendments:
  - 2026-07-11 — Slice 5a per approved plan dynamic-snuggling-truffle.md (repurposed from the 4c plan; owner
    approved the plan incl. the per-type verdict rubric, the (market_code, ticker) grain, and the token format).
