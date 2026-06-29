# Task contract

objective: Adopt the three optional dbt-agent-kit extras — gitleaks secret-scan, a pre-commit framework, and a read-only dbt MCP — tuned to this repo.

scope_paths:
  - .gitleaks.toml
  - .mcp.json
  - .pre-commit-config.yaml
  - requirements-dev.txt
  - .github/workflows/secret-scan.yml
  - scripts/install_git_hooks.py
  - docs/development_workflow.md
  - README.md
  - .claude/**

decisions_reserved:
  - (none) — owner approved adopting all three; gitleaks = CI step + local system-binary hook; ruff = skipped this change.

done_when:
  - .gitleaks.toml, .mcp.json (read-only dbt tools only), .pre-commit-config.yaml exist and are valid; requirements-dev.txt adds pre-commit.
  - gitleaks runs in CI (new secret-scan.yml) and as a local pre-commit hook (system gitleaks binary).
  - pre-commit's no-commit-to-branch replaces scripts/install_git_hooks.py (removed); check_not_on_main.py stays for CI; doc references fixed.
  - sqlfluff pre-commit hook tuned to dbt_analytics/(models|tests), pinned 3.5.0, manual stage. ruff intentionally omitted.
  - Review cycle recorded in .claude/task/review.md (scope-auditor + cto-reviewer, required by .mcp.json / scripts / requirements / workflow) and committed on chore/guardrail-extras; PR opened to main (not merged).

impact_map: (none) — adds local/CI tooling and an editor-side read-only MCP; no dbt models, ingestion, or runtime/export behavior changes. CI gains a secret-scan job; the existing validate job is untouched.

amendments:
  - 2026-06-29 — initial contract for the optional extras (separate, approved follow-up to the guardrail adoption in PR #127).
