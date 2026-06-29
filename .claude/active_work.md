# Active work — handover

_The next session is handed exactly this file. Keep it current._

## Current task

Adopt the `dbt-agent-kit` plugin guardrails in this repo (branch `chore/adopt-guardrails`).

## Status

**In progress.** Plugin installed into `~/.claude/plugins/` (restart `claude` to activate
its hooks/agents). On branch `chore/adopt-guardrails`, the following are written:

- `CLAUDE.md` — entry doc, points to `.claude/working-agreement.md` + `docs/`.
- `.claude/working-agreement.md` — plugin template, verbatim (the canonical agent process).
- `.claude/review_routing.json` — plugin default, tuned to this repo's folders.
- `.claude/active_work.md` — this file.
- `docs/working_agreement.md` — slimmed to a redirect + the project-specific UX PR gate.
- `.cursor/rules/` — deleted (Cursor retired).
- `README.md`, `docs/development_workflow.md` — references updated.

## Next concrete action

Run the review cycle (`.claude/task/review.md`) over the staged diff, then commit on
`chore/adopt-guardrails`, push, and open a PR to `main`. Do not merge — that's the owner's.

## Decisions locked this session

- Plugin setup is canonical; Cursor-era material yields (owner: "use the setup that comes
  with installation … not going to use Cursor anymore").
- One working agreement only: `.claude/working-agreement.md`. `docs/working_agreement.md`
  keeps only the UX PR gate (project-specific) + a redirect.
- `.cursor/rules/` deleted (owner approved).

## Do NOT

- Do not recreate a second working-agreement file or restate agent rules in `CLAUDE.md`
  (drift trap the owner explicitly flagged).
- Do not commit/push to `main`; do not `gh pr merge`.
- Do not touch the optional extras (gitleaks, pre-commit, dbt MCP) without asking — owner
  wants those as a separate, explicit approval.

## Context

A separate branch `docs/refresh-june-2026` holds unrelated in-flight docs work; this task
branched from `origin/main`, not from it.
