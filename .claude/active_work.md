# Active work — handover

_The next session is handed exactly this file. Keep it current._

## Current task

Repair the #128 pre-commit config — branch `fix/precommit-check-json-jsonc`. Two fixes:
(1) check-json JSONC false-positive on `.devcontainer/devcontainer.json`;
(2) `.gitleaks.toml` empty `[allowlist]` rejected by gitleaks 8.30.1 (blocked every local commit).

## Status

**Awaiting CI + owner merge.** PR being opened from `fix/precommit-check-json-jsonc`.

- Guardrail adoption (#127) and the extras (#128) are both **merged**; repo auto-deletes head branches.
- Local enablement is done: `pre-commit` installed in `.venv`, `gitleaks` 8.30.1 installed (needs a
  PERMANENT PATH entry — Dev Mode reinstall or GUI PATH edit — the `set PATH` test was session-only).
  The read-only dbt MCP still needs a desktop-app restart to load `.mcp.json`.
- Verified: `pre-commit run check-json --all-files` passes; `gitleaks ... --config .gitleaks.toml`
  loads and reports no leaks.
- Known follow-up (NOT in this PR): the gitleaks hook uses the deprecated `gitleaks protect`
  subcommand — modernize to `gitleaks git` in a separate change.

## Next concrete action

Owner reviews + merges this PR (do NOT self-merge). After merge: sync local `main`. Then make the
`gitleaks` PATH entry permanent so the local secret-scan hook resolves `gitleaks` at commit time.

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
