# Task contract

objective: Adopt the dbt-agent-kit plugin guardrails as this repo's canonical agent setup, retiring the superseded Cursor-era material without duplicating sources.

scope_paths:
  - CLAUDE.md
  - .claude/**
  - docs/working_agreement.md
  - .cursor/rules/**
  - README.md
  - docs/development_workflow.md

decisions_reserved:
  - Whether to add the optional extras (gitleaks secret-scan, .pre-commit-config.yaml, read-only dbt MCP) — owner wants these as a separate explicit approval.
  - Any change to the dbt layer rules, engineering standards, or product/UX content in docs/ — out of scope here.

done_when:
  - CLAUDE.md, .claude/working-agreement.md (verbatim plugin template), .claude/review_routing.json (tuned to repo folders), and .claude/active_work.md exist.
  - Exactly one agent-process working agreement (.claude/working-agreement.md); docs/working_agreement.md reduced to a redirect + the project-specific UX PR gate, with no broken inbound links.
  - .cursor/rules/ removed and its two inbound references (README.md, docs/development_workflow.md) fixed.
  - Review cycle recorded in .claude/task/review.md and committed on chore/adopt-guardrails; PR opened to main (not merged).

impact_map: (none) — documentation/config and Claude Code setup only; no dbt models, ingestion, or consumption outputs change. No CI behavior changes (no edits to .github/workflows/ or scripts/).

amendments:
  - 2026-06-29 — initial contract; reflects owner's pivot from "merge into docs/" to "plugin setup is canonical, Cursor retired".
