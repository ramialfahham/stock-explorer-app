# Task contract

objective: Modernize the gitleaks pre-commit hook from the deprecated `gitleaks protect` to the supported `gitleaks git --pre-commit --staged`.

scope_paths:
  - .pre-commit-config.yaml
  - .claude/**

decisions_reserved:
  - (none) — owner approved this follow-up.

done_when:
  - The local gitleaks hook entry uses `gitleaks git --pre-commit --staged --redact --config .gitleaks.toml`; verified valid against the staged diff (gitleaks 8.30.1, exit 0, config loads).
  - Review recorded in .claude/task/review.md (scope-auditor) and committed on chore/gitleaks-git-command; PR opened to main (not merged).

impact_map: (none) — pre-commit config only; same scan behavior, non-deprecated subcommand. No runtime, dbt, or CI change.

amendments:
  - 2026-06-29 — initial contract; the deprecation follow-up flagged during #129.
