# Working Agreement — Agent Behaviour

This document governs how any AI agent (Claude, Cursor, or other) operates in this repo.
Read it before doing anything.

---

## 1. Permission to act

- Do not edit files, run terminal commands, or start implementation unless the user clearly
  asked for that action ("implement this", "run it", "commit and push") or replied with an
  explicit go-ahead after options were presented.
- Exploring tradeoffs, asking "what should I do?", or venting frustration are not permission
  to change the repo or run tools. Answer only — options, risks, recommendation — then wait.
- When in doubt, ask one short clarifying question instead of acting.

---

## 2. Before any non-trivial change

State a short block first:
- **Intent**: what you are about to do
- **Files / systems touched**: every file, table, workflow, or external service affected
- **Definition of done**: what "finished" looks like and how it will be verified

If anything could silently shrink scope or affect something not listed, stop and ask.

---

## 3. Branches — always

Every change goes on a new branch. Never commit directly to `main`.

1. `git checkout -b feature/name`
2. Do the work and commit
3. `git push origin feature/name` — explicit remote branch name
4. Open a PR; wait for CI and user approval before merging
5. **After merge:** the agent syncs local `main` (`git fetch --prune`, `checkout main`, `pull`) and
   deletes merged local (and stale remote) branches — the user should not need to do this each time.

---

## 4. Quality is non-negotiable

- **No hacky solutions.** If the clean solution takes longer, say so and agree on the
  timeline — do not ship a workaround and call it done.
- **No unnecessary complexity.** Do not introduce abstractions, layers, or patterns not
  required by the current task. Three clear lines beat a premature abstraction.
- **No scope creep.** Implement exactly what was agreed. If you spot something adjacent
  worth fixing, flag it separately — do not fold it in without agreement.
- **No half-finished implementations.** If a task cannot be completed cleanly, say so
  before starting, not halfway through.

---

## 5. Do not work against the user

- Never change environment config, cost caps, or pipeline behaviour to "make a run finish
  faster" or "unblock quickly" without explicit confirmation.
- Never silently narrow scope.
- If external limits (API quotas, rate limits, free tier caps) require a different approach,
  say so clearly before acting.

---

## 6. Layer contract — dbt

Each dbt layer has a strict purpose. Violating it is a quality defect, not a style preference.

| Layer          | Purpose |
|----------------|---------|
| `1_staging`    | Source-near cleanup only. Renaming, casting, light normalisation. No business logic. |
| `2_base`       | Union and dedup across sources where the same entity appears in more than one place. |
| `3_core`       | Canonical dimensions and facts. System of record. |
| `4_intermediate` | Complex logic, multi-step calculations, cross-table joins reused by multiple marts. |
| `5_marts`      | Consumption layer. Shaped for a specific consumer (app, report, export). |

Cross-layer rules:
- `staging` must not join across sources.
- `intermediate` must not reference `mart_*` models.
- `marts` must not redefine business logic already centralised in `core`.

---

## 7. Communication style

- Present options with tradeoffs before implementing. One recommendation, clearly labelled.
- Flag risks before they materialise, not after.
- If a requirement is ambiguous, ask — do not assume and proceed.
- Keep responses concise. No summaries of what you just did — the diff speaks for itself.
