# Task contract

objective: Metric-catalogue enrichment (handover step 2). Enrich the `metric_catalogue` seed
  SCHEMA and populate the FIVE existing metrics — schema + existing-metric content only. Rename
  `metric_group` → `perspective` (mapping quality→profitability, momentum→growth) and add three
  analytical columns `calculation`, `interpretation`, `applicability`, then fill them for the five
  current metrics with owner-approved text (quoted below). Ripple the rename + new fields through
  `_seeds.yml`, the export script, `frontend/metrics.json`, the Python test, and the two docs. NO new
  metrics, NO Sector Router, NO AI generator, NO UI work (those are handover steps 3–6).

scope_paths:
  - dbt_analytics/seeds/metric_catalogue.csv
  - dbt_analytics/seeds/_seeds.yml
  - scripts/export_metric_definitions_json.py
  - frontend/metrics.json
  - tests/test_metric_catalogue.py
  - docs/metric_layer.md
  - docs/data_contract.md
  - dbt_analytics/models/_docs.md
  - .claude/task/contract.md

review_artifacts (NOT part of the reviewed diff — committed AFTER the reviewed commit as artifact-only,
  gate-exempt commits, per the dbt-agent-kit two-commit pattern, cf. PR #133's separate review/handover
  commits. review.md cannot be in the reviewed diff — it records that diff's own hash (self-reference);
  active_work.md is finalised with the PR link after the commit):
  - .claude/task/review.md       — the recorded review cycle; its diff_sha256 matches the reviewed commit.
  - .claude/active_work.md       — the advanced session handover.

decisions_reserved:
  - Metric definitions/wording and the perspective taxonomy are §6 owner content. ALREADY signed off
    by the owner this session — the calculation/interpretation/applicability text and the rename are
    quoted verbatim below and must be written EXACTLY (no rewording). No new owner decision is opened.

owner_approved_content (write verbatim — §6 sign-off):
  perspective taxonomy (accepted values): valuation · profitability · growth · solvency · liquidity · cash · returns
  rename mapping: metric_group→perspective; quality→profitability; momentum→growth

  forward_pe — perspective: valuation — direction: lower_better
    calculation:    Share price ÷ forecast earnings per share for next year (Yahoo forwardPE).
    interpretation: Higher = the market pays more per dollar of expected profit (priced for quality/growth, or simply expensive). Always read next to growth.
    applicability:  Undefined for loss-makers (negative or near-zero forecast earnings) — the value is meaningless, not "cheap."

  ebit_margin_pct — perspective: profitability — direction: higher_better
    calculation:    Operating profit ÷ revenue × 100 (trailing twelve months from four quarters; latest annual as fallback).
    interpretation: Higher = more of each sales dollar kept as operating profit. Stable high margins signal pricing power and efficiency.
    applicability:  Breaks for pre-revenue firms (revenue ≈ 0 → explodes); means something different for financials.

  revenue_growth_yoy_pct — perspective: growth — direction: higher_better
    calculation:    Latest quarter revenue vs the same quarter a year ago (Yahoo revenueGrowth × 100).
    interpretation: Higher = faster top-line growth — but growth ≠ health (a company can grow into losses). Single quarter, so noisy.
    applicability:  Distorted by tiny prior-year bases (micro-caps, commodity ramps → huge % off a small base).

  net_debt_to_ebitda — perspective: solvency — direction: lower_better
    calculation:    (Total debt − cash) ÷ EBITDA — roughly how many years of earnings to clear net debt.
    interpretation: Lower = less leverage, safer. Negative = net cash. High = exposed in downturns or when rates rise.
    applicability:  Meaningless for financials ("cash" includes customer/policyholder assets); explodes when EBITDA ≈ 0 (distressed/pre-profit).

  fcf_margin_pct — perspective: cash — direction: higher_better
    calculation:    Free cash flow ÷ revenue × 100 (latest annual statements).
    interpretation: Higher = more real cash per sales dollar — harder to fake than accounting profit. The strongest single health signal.
    applicability:  Breaks for pre-revenue firms (revenue ≈ 0); not meaningful for financials.

done_when:
  - metric_catalogue.csv: `metric_group` column renamed to `perspective`; values mapped
    (quality→profitability, momentum→growth; valuation/solvency/cash unchanged). New columns
    `calculation`, `interpretation`, `applicability` added (placed right after `description`) and
    populated for all five metrics with the verbatim owner-approved text above. `description`,
    `direction`, `gloss`, `analogy`, `learn`, formula spec, tier/order, benchmarkable — all unchanged.
  - _seeds.yml: column renamed `metric_group`→`perspective`; `accepted_values` = the full 7-value
    taxonomy; `perspective` gets `not_null`; each of `calculation`/`interpretation`/`applicability`
    gets `not_null` (free text → no accepted_values); seed-level prose + column descriptions updated.
  - export_metric_definitions_json.py: `_TEXT_FIELDS` drops `metric_group`, adds `perspective` +
    `calculation`/`interpretation`/`applicability`; `frontend/metrics.json` regenerated and committed.
  - test_metric_catalogue.py: `_VALID_GROUPS`→`_VALID_PERSPECTIVES` (7 values); well-formed check
    reads `perspective`; non-empty checks added for the three new fields.
  - docs/metric_layer.md + docs/data_contract.md: field list reflects `perspective` + the three new
    columns; data_contract.md:55 ordering line updated (quality→profitability, momentum→growth).
  - dbt_analytics/models/_docs.md: the `{% docs card_metrics %}` taxonomy-ordering line updated to the
    renamed order (valuation → profitability → growth → solvency → cash), matching data_contract.md:55.
  - Rendered card byte-identical (card_copy.py reads none of the changed/added fields).
  - Verify green: `dbt parse`; `dbt seed --select metric_catalogue`; `dbt test --select
    metric_catalogue`; `pytest tests/`; `metrics.json` regenerated with no further diff.
  - After the reviewed commit (as artifact-only, gate-exempt commits — NOT in the reviewed diff): record
    the review cycle in .claude/task/review.md (scope-auditor + analytics-engineer-reviewer +
    cto-reviewer + equity-analyst-reviewer, per review_routing.json) and advance .claude/active_work.md.
    PR opened to main (NOT merged); #133 already merged.

impact_map:
  - frontend/metrics.json: content changes (new `perspective` key replaces `metric_group`; three new
    keys added). INTENDED. card_copy.py does not read any of these keys, so the rendered card is
    unchanged — only the JSON file's bytes change, locked by test_regenerated_json_matches_committed.
  - No dbt model / DAG change: `metric_catalogue` is not `ref`'d by any model (verified); the seed is
    documentation/registry only and int_stock__card_metrics computes the metrics independently.
  - No ingestion, Supabase export, or migration change. No new metric, mechanism, or dependency.

amendments:
  - 2026-06-30 — initial contract for the catalogue-enrichment PR (handover step 2). Supersedes the
    equity-analyst-reviewer contract (PR #133, now merged). Owner content pre-approved and quoted above.
  - 2026-06-30 — scope-auditor FAIL (doc-sync): the `{% docs card_metrics %}` block in
    dbt_analytics/models/_docs.md still stated the pre-rename taxonomy ordering (a sibling of the
    data_contract.md:55 line that WAS updated). Added that file to scope_paths and updated the ordering
    to match the owner-approved rename — a mechanical consistency fix, no new owner content. Full review
    cycle re-run against the updated diff.
  - 2026-06-30 — scope-auditor process feedback: review.md/active_work.md are review-cycle artifacts that
    cannot live in the reviewed diff (review.md records that diff's own hash → self-reference;
    active_work.md is finalised with the PR link post-commit). Moved them out of scope_paths into
    review_artifacts and reframed done_when to the dbt-agent-kit two-commit pattern (cf. #133). The
    reviewed diff is now exactly the 8 substantive files + this contract. active_work.md has been advanced
    (#133 merged; this enrichment now the open PR).
