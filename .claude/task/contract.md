# Task contract

objective: Add an equity-analyst-reviewer to the blinded review cycle — a finance-domain reviewer that checks the financial CONTENT (metric calculations, interpretations, applicability, direction, and AI assessments) for accuracy, honesty, beginner-fit, and the "educational, never advice" line. Mirrors the football repo's domain-expert reviewer. This is the reviewer infrastructure; it reviews the catalogue-enrichment work next.

scope_paths:
  - .claude/agents/equity-analyst-reviewer.md
  - .claude/review_routing.json
  - .claude/**

decisions_reserved:
  - (none new) — owner approved adding the financial-expert reviewer role.

done_when:
  - .claude/agents/equity-analyst-reviewer.md exists (read-only finance reviewer; default-FAIL; checks financial validity, applicability honesty, direction, beginner-fit, not-advice, no-fabrication, owner-approval).
  - review_routing.json routes financial content to it: *metric_catalogue.csv, docs/metric_layer.md, docs/data_contract.md (alongside the existing reviewers). JSON valid.
  - Review cycle recorded; PR opened to main (not merged). The catalogue enrichment is a SEPARATE follow-on PR, now subject to this reviewer.

impact_map: (none) — review-cycle configuration only. No runtime, dbt, ingestion, or frontend change. Adds a required reviewer for future financial-content commits.

amendments:
  - 2026-06-29 — initial contract; owner asked "do we need a financial expert reviewer role?" and approved adding it. Gap it fills: scope/analytics-engineer/cto/data-engineer reviewers cover process, SQL, engineering, ingestion — none judges financial correctness or the not-advice line.
