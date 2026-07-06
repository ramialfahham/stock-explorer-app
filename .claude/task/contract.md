# Task contract

objective: Add **`company_type` as a DATA-ONLY classifier** — Slice 1 of the Sector/Lifecycle
  Router (handover next-action #1). Classify every snapshot into `operating` / `financial` /
  `pre_revenue` from signals we already have: Yahoo `info_sector` = "Financial Services" →
  financial; near-zero `stmt_total_revenue` → pre_revenue; else operating. This is the foundation
  the later Router slices build on (per-type metric sets, eligibility rework, display, AI framing).
  **No display surface and no eligibility change:** no catalogue row, metrics.json, card_copy/UI,
  Supabase export, or `is_card_eligible`/`missing_metrics` change; frontend untouched. Approved
  plan: ~/.claude/plans/noble-forging-beaver.md. Owner decisions this session: (1) three types as
  described, **REITs stay `operating`**; (2) build the bank debt metrics (debt-to-equity +
  interest coverage) — but they need new ingestion, so they are **Slice 2, not here**.

scope_paths:
  - dbt_analytics/models/4_intermediate/int_stock__card_metrics.sql
  - dbt_analytics/models/4_intermediate/_intermediate.yml
  - docs/data_contract.md
  - .claude/task/contract.md

review_artifacts (NOT in the reviewed diff — separate artifact-only/gate-exempt commit after the
  reviewed commit; review.md records the reviewed diff's hash):
  - .claude/task/review.md
  - .claude/active_work.md

decisions_reserved:
  - The three-type taxonomy (`operating`/`financial`/`pre_revenue`) and the classification rules are
    owner-approved this session (plan + AskUserQuestion). **REITs → `operating`** (owner choice, not
    financial-style, for now).
  - **Pre-revenue threshold is owner-flagged as their call.** This slice uses the conservative rule:
    `stmt_total_revenue` present AND ≤ 0 → `pre_revenue`; a **null** revenue is treated as a data gap
    (stays `operating`), not assumed pre-revenue. Validated by inspecting the real classified
    distribution during verify; tunable toward near-zero if the set proves too sparse.
  - DEFERRED to later Router slices (NOT here): per-type metric sets; per-type eligibility rework;
    catalogue rows + per-type display; beginner/applicability copy (ROE negative/thin-equity + breaks
    for financials; FCF-yield **negative for cash-burners** — the #137 equity-analyst flag; EV/EBITDA
    & P/B financials caveats); the bank metrics debt-to-equity + interest coverage (need ingestion —
    Slice 2); cash runway (Slice 2).
  - No interpretive/beginner copy authored here — `data_contract.md` stays factual (the #135 §6 lesson).

technical_definition (factual; no beginner copy):
  - compute in the `metrics` CTE of `int_stock__card_metrics.sql`, derived purely from existing columns
    (`sector` is already `coalesce(info_sector, st.sector)`; `stmt_total_revenue` is on the snapshot):
    `case when coalesce(s.info_sector, st.sector) = 'Financial Services' then 'financial'
     when s.stmt_total_revenue is not null and s.stmt_total_revenue <= 0 then 'pre_revenue'
     else 'operating' end as company_type`
  - Always resolves to exactly one of the three values → **non-null for every row**. Adds no rows, no
    grain change. NOT in `is_card_eligible` / `missing_metrics`. NOT selected by `mart_stock_cards`
    (not exported).

done_when:
  - dbt: `company_type` added to the `metrics` CTE; `eligibility`/`missing_metrics` CTEs UNCHANGED
    (still exactly the original five metrics).
  - docs (doc gate): `company_type` documented in `_intermediate.yml` with `not_null` +
    `accepted_values ['operating','financial','pre_revenue']`.
  - test: dbt **unit test(s)** in `_intermediate.yml` mocking `fct_fundamentals_snapshot` — a
    Financial-Services row → `financial`; a `stmt_total_revenue = 0` row → `pre_revenue`; a normal
    row → `operating`. (Add alongside / extend the existing HSBC·Lloyds unit tests.)
  - data_contract.md: factual "Company-type classification" subsection (the three values + the exact
    rules; no interpretation/beginner copy).
  - CI fixtures UNTOUCHED — classification is proven via mocked unit tests, so the eligibility baseline
    (25) is not disturbed.
  - Verify green: dbt parse; dbt build; dbt docs generate + check_dbt_documentation;
    check_layer_contract; check_dbt_sql_structure; sqlfluff; check_eligibility_baseline (stays 25) +
    check_export_health (stays 100%); pytest. Card byte-identical (frontend untouched). Distribution
    spot-check: `financial` = banks/insurers, `pre_revenue` = genuine no-sales firms (tune if needed).
  - After the reviewed commit (artifact-only): record review.md, advance active_work.md; PR to main
    (NOT merged).

impact_map:
  - `company_type` is a derived column over existing fields — adds no rows, no grain change. Absent
    from eligibility and from `mart_stock_cards` → export shape, export-health, and the eligibility
    baseline are all unchanged. No catalogue row → not rendered (frontend byte-identical). No
    ingestion/staging/base/core touched. CI raw fixtures untouched (tested via mocked unit tests).
  - Required reviewers (per `.claude/review_routing.json`): scope-auditor (always) +
    analytics-engineer-reviewer (`*.sql` + `dbt_analytics/*.yml`) + equity-analyst-reviewer
    (`docs/data_contract.md`). cto-reviewer and data-engineer-reviewer NOT triggered (no
    scripts/frontend/ingestion/supabase files; unit tests live in the dbt yml, not `tests/`).

amendments:
  - 2026-07-06 — supersedes the merged FCF-yield contract (#137). Scope = `company_type` classifier
    data-only (Slice 1 of the Sector/Lifecycle Router), per approved plan noble-forging-beaver.md and
    the owner's three-type + REITs-operating decisions; run through the plan-mode spine.
