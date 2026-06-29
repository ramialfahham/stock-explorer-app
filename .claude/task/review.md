# Review

diff_sha256: d35ab2e28e09802d941087070506bc4f23d9dde17ab75e6e32b396ce0a7e77a6

## scope-auditor
VERDICT: PASS
risks_checked:
- Every staged path is inside the contract's scope_paths (.gitleaks.toml, .mcp.json, .pre-commit-config.yaml, requirements-dev.txt, .github/workflows/secret-scan.yml, scripts/install_git_hooks.py, docs/development_workflow.md, .claude/**). No out-of-scope edit.
- Approved decisions honored: gitleaks delivered via CI + a local system-binary hook; ruff intentionally omitted (no mass reformat sneaked in); sqlfluff hook left at manual stage.
- impact_map "(none)" holds: no dbt model, ingestion, frontend, or export/runtime file changed. The only CI change is an additive new workflow; ci-validate.yml is untouched.
- No scope creep: pre-existing untracked clutter (.venv/, dbt_analytics/dev.duckdb, storage/audit/, .gh-issue-body.md) left unstaged.

## cto-reviewer
VERDICT: PASS
risks_checked:
- Secrets/safety: .mcp.json enables only read-only dbt tools (get_lineage_dev, get_node_details_dev, list, parse) — no run/build/seed/write, so the MCP cannot mutate the warehouse. No credentials embedded in any config. The change net-improves posture (gitleaks in CI + staged, plus detect-private-key and no-commit-to-branch locally).
- New mechanisms scoped correctly: pre-commit and dbt-mcp are dev-only — pre-commit lives in requirements-dev.txt (NOT root requirements.txt), so the pipeline/CI runtime install and the Streamlit deploy are unaffected; dbt-mcp runs in an isolated uvx env and is editor-side only.
- CI soundness: secret-scan.yml is a separate additive workflow (own job), uses gitleaks/gitleaks-action@v2 with GITHUB_TOKEN, fetch-depth:0 for history; free for a public personal-account repo (no GITLEAKS_LICENSE). Worst case it fails if a real secret exists in history — desired behavior.
- No loss of protection from removing scripts/install_git_hooks.py: humans get the main-commit block via pre-commit no-commit-to-branch (same one-time-setup requirement as before), CI keeps check_not_on_main.py, and the plugin's branch_discipline hook covers the agent. Doc reference updated.
- Version pins are consistent: sqlfluff 3.5.0 matches requirements.txt (template's 3.2.5 corrected); pre-commit-hooks v5.0.0, pre-commit==4.0.1, gitleaks-action@v2 are valid.
- Known limitation (accepted): DBT_PATH=".venv/Scripts/dbt.exe" in committed .mcp.json is Windows/venv-specific and not portable to another machine/OS. Acceptable for this solo Windows project; called out in the PR. Revisit if a contributor joins or CI ever runs the MCP.
