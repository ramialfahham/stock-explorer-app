# Task contract

objective: Repair the pre-commit config shipped in #128 so it runs cleanly with the installed toolchain — fix the check-json JSONC false-positive and the invalid empty gitleaks allowlist.

scope_paths:
  - .pre-commit-config.yaml
  - .gitleaks.toml
  - .claude/**

decisions_reserved:
  - (none) — owner approved folding the .gitleaks.toml fix into this PR.

done_when:
  - check-json hook excludes .devcontainer/; `pre-commit run check-json --all-files` passes.
  - .gitleaks.toml has no empty [allowlist]; `gitleaks ... --config .gitleaks.toml` loads and reports no leaks (verified, gitleaks 8.30.1).
  - Review recorded in .claude/task/review.md (scope-auditor) and committed on fix/precommit-check-json-jsonc; PR opened to main (not merged).

impact_map: (none) — pre-commit + gitleaks config only; no runtime, dbt, or CI behavior change.

amendments:
  - 2026-06-29 — initial contract (check-json fix).
  - 2026-06-29 — scope expanded to .gitleaks.toml: verifying the check-json fix surfaced that the #128 .gitleaks.toml (empty [allowlist]) is rejected by gitleaks 8.30.1 and blocks every local commit. Owner approved fixing both in this PR.
