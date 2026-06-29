# Active work — handover

_The next session is handed exactly this file. Keep it current._

## Current task

Modernize the gitleaks pre-commit hook (`gitleaks protect` → `gitleaks git --pre-commit --staged`) —
branch `chore/gitleaks-git-command`.

## Status

**Awaiting CI + owner merge.** PR being opened from `chore/gitleaks-git-command`.

- Guardrail adoption (#127), extras (#128), and the pre-commit config repair (#129) are all **merged**;
  repo auto-deletes head branches on merge.
- Local enablement done: `pre-commit` installed in `.venv`; `gitleaks` 8.30.1 installed. The dbt MCP
  activates on a desktop-app restart (owner said they'd restart).
- This change swaps the hook to the non-deprecated `gitleaks git --pre-commit --staged`; verified the
  command loads `.gitleaks.toml` and exits 0.

## Next concrete action

Owner reviews + merges this PR (do NOT self-merge). After merge: sync local `main`.

## Decisions locked / notes

- `gitleaks` must be on the PERMANENT user PATH (Dev Mode reinstall or GUI PATH edit) so the local
  pre-commit hook resolves it at commit time. The `set PATH` used during setup was session-only;
  agent tool shells export the WinGet Packages path inline until the user makes it permanent.

## Do NOT

- Do not commit/push to `main`; do not `gh pr merge`.
- Do not re-introduce a second working-agreement file or restate agent rules in `CLAUDE.md`.
- Do not broaden the dbt MCP beyond read-only tools, or enable ruff-format, without asking.

## Context

A separate branch `docs/refresh-june-2026` holds unrelated in-flight docs work (other chat); leave it alone.
