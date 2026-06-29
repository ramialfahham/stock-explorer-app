# Active work — handover

_The next session is handed exactly this file. Keep it current._

## Current task

Adopt the three optional dbt-agent-kit extras (gitleaks, pre-commit, read-only dbt MCP) —
branch `chore/guardrail-extras`, PR #128.

## Status

**Awaiting CI + owner merge.** PR open: https://github.com/ramialfahham/stock-swipe-app/pull/128

- The base guardrail adoption (PR #127) is **merged**; repo auto-deletes head branches on merge now.
- #128 adds: `.gitleaks.toml`, `.github/workflows/secret-scan.yml` (gitleaks in CI),
  `.pre-commit-config.yaml` (hygiene + staged gitleaks + `no-commit-to-branch`; sqlfluff manual,
  pinned 3.5.0; ruff deferred), `.mcp.json` (read-only dbt MCP), `requirements-dev.txt` (adds
  pre-commit). Removes `scripts/install_git_hooks.py` (superseded); `docs/development_workflow.md`
  reference updated. Review recorded (scope-auditor + cto-reviewer).

## Next concrete action

Owner reviews + merges #128 (do NOT self-merge). After merge: sync local `main` (origin auto-deletes
the branch). One-time local enablement: `pip install -r requirements-dev.txt && pre-commit install`,
and install the `gitleaks` binary (e.g. `winget install gitleaks`) for the local hook.

## Decisions locked this session

- All three extras adopted. gitleaks = CI step + local system-binary hook. ruff = deferred to its
  own PR (avoid a mass first-run reformat). sqlfluff pre-commit hook = manual stage (CI stays the gate).
- `scripts/install_git_hooks.py` removed; replaced by pre-commit `no-commit-to-branch`;
  `check_not_on_main.py` stays for CI.
- `.mcp.json` exposes read-only dbt tools only; `DBT_PATH` is Windows/venv-specific (accepted for solo setup).

## Do NOT

- Do not commit/push to `main`; do not `gh pr merge`.
- Do not enable ruff-format silently (it would reformat the existing Python en masse — must be its own PR).
- Do not broaden the dbt MCP beyond read-only tools without asking.

## Context

A separate branch `docs/refresh-june-2026` holds unrelated in-flight docs work (other chat); leave it alone.
